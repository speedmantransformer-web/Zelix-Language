"""Static type parsing and checking for Zelix."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, is_dataclass
from game_backend import (
    GAME_FUNCTIONS, GAME_FUNCTION_ARGUMENT_TYPES, GAME_FUNCTION_RETURN_TYPES,
)

from syntax import (
    Assign, Await, Binary, Call, CallStatement, Create, Display, Expr, FunctionIR,
    If, Input, Literal, ModuleIR, RangeLoop, Repeat, Return, Spawn, Unary, Variable,
    While,
)


class TypeCheckError(Exception):
    pass


@dataclass(frozen=True)
class Type:
    name: str
    arguments: tuple[Type, ...] = ()

    def __str__(self) -> str:
        if not self.arguments:
            return self.name
        return f"{self.name}<{', '.join(map(str, self.arguments))}>"


_PRIMITIVES = {
    "number", "text", "boolean", "any", "void", "null", "texture", "sound",
    "animation", "animation_machine", "combatant", "entity", "path_grid",
    "path", "particle_emitter",
}
_GENERICS = {"list": 1, "set": 1, "map": 2, "tuple": -1, "task": 1, "channel": 1}
_ALIASES = {"bool": "boolean", "string": "text"}
_RESOURCE_TYPES = {"texture", "sound"}


def parse_type(source: str) -> Type:
    original = source.strip()
    if re.fullmatch(r"[A-Z]", original):
        return Type(original)
    source = original.lower()
    if source in _ALIASES:
        source = _ALIASES[source]
    open_bracket = source.find("<")
    if open_bracket < 0:
        if source not in _PRIMITIVES:
            raise TypeCheckError(f"Unknown type {source!r}")
        return Type(source)
    if not source.endswith(">"):
        raise TypeCheckError(f"Invalid type syntax {source!r}")
    name = original[:open_bracket].strip().lower()
    if name not in _GENERICS:
        raise TypeCheckError(f"Unknown generic type {name!r}")
    arguments = _split_type_arguments(original[open_bracket + 1:-1])
    expected = _GENERICS[name]
    if not arguments or (expected != -1 and len(arguments) != expected):
        arity = "one or more" if expected == -1 else str(expected)
        raise TypeCheckError(f"Type {name} expects {arity} type argument(s)")
    return Type(name, tuple(parse_type(argument) for argument in arguments))


def _split_type_arguments(source: str) -> list[str]:
    parts: list[str] = []
    start = depth = 0
    for index, character in enumerate(source):
        if character == "<":
            depth += 1
        elif character == ">":
            depth -= 1
            if depth < 0:
                raise TypeCheckError(f"Invalid generic type syntax {source!r}")
        elif character == "," and depth == 0:
            parts.append(source[start:index].strip())
            start = index + 1
    if depth != 0:
        raise TypeCheckError(f"Invalid generic type syntax {source!r}")
    parts.append(source[start:].strip())
    return parts


def _compatible(expected: Type, actual: Type) -> bool:
    if expected.name == "any" or actual.name == "any" or _is_type_variable(expected.name):
        return True
    if expected.name == "number" and actual.name == "number":
        return True
    if expected.name != actual.name or len(expected.arguments) != len(actual.arguments):
        return False
    return all(_compatible(want, got) for want, got in zip(expected.arguments, actual.arguments))


def _hashable(value: Type) -> bool:
    if value.name in {"number", "text", "boolean", "null", "any"}:
        return True
    return value.name == "tuple" and all(_hashable(item) for item in value.arguments)


def _valid_set_element(value: Type) -> bool:
    return _hashable(value) or (
        value.name == "list"
        and len(value.arguments) == 1
        and value.arguments[0].name == "text"
    )


def _contains_resource(value: Type) -> bool:
    return value.name in _RESOURCE_TYPES or any(
        _contains_resource(argument) for argument in value.arguments
    )


def _contains_any(value: Type) -> bool:
    return value.name == "any" or any(
        _contains_any(argument) for argument in value.arguments
    )


def _merge(left: Type, right: Type) -> Type:
    return left if left == right else Type("any")


class TypeChecker:
    def __init__(self, module: ModuleIR, strict: bool = False):
        self.module = module
        self.functions = {function.name: function for function in module.functions}
        self.strict = strict
        self._owned_resources: set[str] = set()
        self._released_resources: set[str] = set()
        self._function_resource_globals: set[str] = set()
        self.expression_types: dict[int, Type] = {}
        self._resource_initializer_call: Call | None = None

    def check(self) -> None:
        globals_env: dict[str, Type] = {}
        self._statements(self.module.body, globals_env, None, True, 1)
        self._check_owned_resources_released(1)
        for function in self.module.functions:
            self._owned_resources = set()
            self._released_resources = set()
            generic_params = set(function.generic_params)
            if any(not _is_type_variable(item) for item in generic_params):
                self._error(function.line, "Generic parameters must be single uppercase letters such as T")
            for annotation in [*function.param_types.values(), function.return_type]:
                if annotation:
                    undeclared = _type_variables(parse_type(annotation)) - generic_params
                    if undeclared:
                        self._error(
                            function.line,
                            f"Undeclared generic type variable {sorted(undeclared)[0]!r}",
                        )
            env = dict(globals_env)
            if self.strict:
                for parameter in function.params:
                    if parameter not in function.param_types:
                        self._error(
                            function.line,
                            f"Strict mode requires a type for parameter {parameter!r}",
                        )
                    elif _contains_any(parse_type(function.param_types[parameter])):
                        self._error(
                            function.line,
                            f"Strict mode forbids any in parameter {parameter!r}",
                        )
                if function.return_type is None:
                    self._error(function.line, "Strict mode requires an explicit function return type")
                elif _contains_any(parse_type(function.return_type)):
                    self._error(function.line, "Strict mode forbids any as a function return type")
            env.update({
                name: parse_type(function.param_types[name])
                if name in function.param_types else Type("any")
                for name in function.params
            })
            local_names = set(function.params)
            self._function_resource_globals = {
                name for name, value in globals_env.items()
                if _contains_resource(value) and name not in local_names
            }
            return_type = parse_type(function.return_type) if function.return_type else None
            self._statements(function.body, env, return_type, function.is_async, function.line)
            self._check_owned_resources_released(function.line)
            self._function_resource_globals = set()
            if function.is_async:
                self._validate_task_target(function, function.line)

    def _error(self, line: int, message: str) -> None:
        raise TypeCheckError(f"Line {line}: {message}")

    def _expect(self, line: int, expected: Type, actual: Type, context: str) -> None:
        if self.strict and _contains_any(actual) and not _contains_any(expected):
            self._error(
                line,
                f"Strict mode cannot verify {context} because its type is {actual}",
            )
        if not _compatible(expected, actual):
            self._error(line, f"{context} expects {expected}, got {actual}")

    def _check_owned_resources_released(self, line: int) -> None:
        leaked = sorted(self._owned_resources - self._released_resources)
        if leaked:
            self._error(
                line,
                f"Owned resource {leaked[0]!r} is not released on this exit path",
            )

    def _expression(
        self, expression: Expr, env: dict[str, Type], expected: Type | None = None,
    ) -> Type:
        result = self._infer_expression(expression, env, expected)
        self.expression_types[id(expression)] = result
        return result

    def _infer_expression(
        self, expression: Expr, env: dict[str, Type], expected: Type | None = None,
    ) -> Type:
        if isinstance(expression, Literal):
            value = expression.value
            if isinstance(value, bool):
                return Type("boolean")
            if isinstance(value, (int, float)):
                return Type("number")
            if isinstance(value, str):
                return Type("text")
            return Type("null")
        if isinstance(expression, Input):
            return Type(expression.kind)
        if isinstance(expression, Variable):
            if expression.name not in env:
                self._error(expression.line, f"Unknown variable {expression.name!r}")
            if (
                expression.name in self._function_resource_globals
                and _contains_resource(env[expression.name])
            ):
                self._error(
                    expression.line,
                    f"Resource global {expression.name!r} must be passed as a typed parameter",
                )
            if expression.name in self._released_resources:
                self._error(
                    expression.line,
                    f"Resource {expression.name!r} was already released",
                )
            return env[expression.name]
        if isinstance(expression, Unary):
            self._expect(
                expression.line, Type("boolean"),
                self._expression(expression.value, env, Type("boolean")), "not",
            )
            return Type("boolean")
        if isinstance(expression, Await):
            if not self._async_context:
                self._error(expression.line, "await can only be used in async functions or at top level")
            task_type = self._expression(expression.value, env)
            if task_type.name != "task" or not task_type.arguments:
                self._error(expression.line, f"await expects a task, got {task_type}")
            return task_type.arguments[0]
        if isinstance(expression, Spawn):
            function = self.functions.get(expression.call.name)
            if function is None:
                self._error(expression.line, "spawn expects a user-defined function")
            self._call(expression.call, env)
            self._validate_task_target(function, expression.line)
            result = parse_type(function.return_type) if function.return_type else Type("any")
            return Type("task", (result,))
        if isinstance(expression, Binary):
            left = self._expression(expression.left, env)
            right = self._expression(expression.right, env)
            if self.strict and (_contains_any(left) or _contains_any(right)):
                self._error(
                    expression.line,
                    "Strict mode cannot verify an operator with an any operand",
                )
            if expression.op in {"and", "or"}:
                self._expect(expression.line, Type("boolean"), left, expression.op)
                self._expect(expression.line, Type("boolean"), right, expression.op)
                return Type("boolean")
            if expression.op in {"add", "sub", "mul", "div", "mod"}:
                if expression.op == "add" and left == right == Type("text"):
                    return Type("text")
                self._expect(expression.line, Type("number"), left, expression.op)
                self._expect(expression.line, Type("number"), right, expression.op)
                return Type("number")
            if expression.op in {"gt", "lt", "gte", "lte"}:
                if left.name != right.name or left.name not in {"number", "text", "any"}:
                    self._error(expression.line, f"Cannot compare {left} with {right}")
                return Type("boolean")
            if expression.op in {"eq", "ne"}:
                if not _compatible(left, right) and not _compatible(right, left):
                    self._error(expression.line, f"Cannot compare {left} with {right}")
                return Type("boolean")
        if isinstance(expression, Call):
            return self._call(expression, env, expected)
        self._error(expression.line, f"Unsupported expression: {type(expression).__name__}")
        return Type("any")

    def _call(
        self, call: Call, env: dict[str, Type], expected: Type | None = None,
    ) -> Type:
        if call.name == "spawn_thread":
            if not call.args or not isinstance(call.args[0], Literal):
                self._error(call.line, "spawn_thread expects a function name followed by arguments")
            function = self.functions.get(str(call.args[0].value))
            if function is None:
                self._error(call.line, f"Unknown thread function {call.args[0].name!r}")
            if function.is_async:
                self._error(call.line, "spawn_thread requires a synchronous function")
            self._validate_task_target(function, call.line)
            arguments = call.args[1:]
            if len(arguments) != len(function.params):
                self._error(
                    call.line,
                    f"Thread function {function.name} expects {len(function.params)} "
                    f"arguments, got {len(arguments)}",
                )
            for name, argument in zip(function.params, arguments):
                parameter_type = (
                    parse_type(function.param_types[name])
                    if name in function.param_types else None
                )
                actual = self._expression(argument, env, parameter_type)
                if _contains_resource(actual) and (
                    parameter_type is None or _type_variables(parameter_type)
                ):
                    self._error(
                        call.line,
                        "Resource handles cannot be passed through untyped or generic parameters",
                    )
                if self.strict and _contains_any(actual):
                    self._error(
                        call.line,
                        f"Strict mode cannot verify argument {name!r} because its type is any",
                    )
                if parameter_type:
                    self._expect(call.line, parameter_type, actual, f"Argument {name!r}")
            result = parse_type(function.return_type) if function.return_type else Type("any")
            return Type("task", (result,))

        if call.name in self.functions:
            function = self.functions[call.name]
            generic_params = set(function.generic_params)
            substitutions: dict[str, Type] = {}
            if len(call.args) != len(function.params):
                self._error(
                    call.line,
                    f"Function {call.name} expects {len(function.params)} arguments, got {len(call.args)}",
                )
            for name, argument in zip(function.params, call.args):
                parameter_type = (
                    parse_type(function.param_types[name])
                    if name in function.param_types else None
                )
                actual = self._expression(argument, env, parameter_type)
                if _contains_resource(actual) and (
                    parameter_type is None or _type_variables(parameter_type)
                ):
                    self._error(
                        call.line,
                        "Resource handles cannot be passed through untyped or generic parameters",
                    )
                if parameter_type:
                    try:
                        _unify(parameter_type, actual, generic_params, substitutions)
                    except TypeCheckError as exc:
                        self._error(call.line, str(exc))
                    self._expect(
                        call.line, _substitute_type(parameter_type, substitutions),
                        actual, f"Argument {name!r}",
                    )
            result = (
                _substitute_type(parse_type(function.return_type), substitutions)
                if function.return_type else Type("any")
            )
            self._validate_task_target(function, call.line) if function.is_async else None
            return Type("task", (result,)) if function.is_async else result

        if call.name in GAME_FUNCTIONS:
            expected_count = GAME_FUNCTIONS[call.name]
            if len(call.args) != expected_count:
                self._error(
                    call.line,
                    f"Game API {call.name} expects {expected_count} arguments, got {len(call.args)}",
                )
            arguments = [self._expression(argument, env) for argument in call.args]
            for index, type_name in GAME_FUNCTION_ARGUMENT_TYPES.get(call.name, {}).items():
                self._expect(
                    call.line, Type(type_name), arguments[index],
                    f"Game API {call.name} argument {index + 1}",
                )
            if call.name in {"unload_texture", "unload_sound"}:
                resource = call.args[0]
                if not isinstance(resource, Variable):
                    self._error(call.line, f"{call.name} requires an owned resource variable")
                if resource.name not in self._owned_resources:
                    self._error(
                        call.line,
                        f"{call.name} can only release a resource owned in this scope",
                    )
                self._released_resources.add(resource.name)
            return_type = Type(GAME_FUNCTION_RETURN_TYPES.get(call.name, "any"))
            if (
                return_type.name in _RESOURCE_TYPES
                and call is not self._resource_initializer_call
            ):
                self._error(
                    call.line,
                    "A resource handle must be bound directly to an owning variable",
                )
            if call.name == "close_audio":
                if self._function_resource_globals:
                    self._error(
                        call.line,
                        "close_audio cannot be called from a function while resource globals exist",
                    )
                self._released_resources.update(
                    name for name in self._owned_resources
                    if name in env and env[name] == Type("sound")
                )
            if call.name == "close_window":
                if self._function_resource_globals:
                    self._error(
                        call.line,
                        "close_window cannot be called from a function while resource globals exist",
                    )
                self._released_resources.update(
                    name for name in self._owned_resources
                    if name in env and env[name] == Type("texture")
                )
            return return_type

        args = [self._expression(argument, env) for argument in call.args]
        name = call.name
        modapi_records = Type(
            "list", (Type("map", (Type("text"), Type("any"))),)
        )
        if name in {"modapi_items", "modapi_recipes"}:
            if args:
                self._error(call.line, f"{name} expects no arguments")
            return modapi_records
        if name in {"modapi_recipe_gui"}:
            if args:
                self._error(call.line, f"{name} expects no arguments")
            return Type("number")
        if name in {"modapi_recipes_for", "getrecipesforid"}:
            if len(args) != 1:
                self._error(call.line, f"{name} expects one item ID")
            self._expect(call.line, Type("number"), args[0], "Item ID")
            return modapi_records
        if name in {"modapi_item_id", "getidforitem"}:
            if len(args) != 1:
                self._error(call.line, f"{name} expects one registry name")
            self._expect(call.line, Type("text"), args[0], "Registry name")
            return Type("number")
        if name == "getitembyid":
            if len(args) != 1:
                self._error(call.line, "getItemById expects one item ID")
            self._expect(call.line, Type("number"), args[0], "Item ID")
            return Type("map", (Type("text"), Type("any")))
        if name == "getrecipe":
            if len(args) != 2:
                self._error(call.line, "getRecipe expects an item ID and recipe index")
            self._expect(call.line, Type("number"), args[0], "Item ID")
            self._expect(call.line, Type("number"), args[1], "Recipe index")
            return Type("map", (Type("text"), Type("any")))
        if name == "modapi_register_item":
            if len(args) != 2:
                self._error(call.line, "modapi_register_item expects a name and stack size")
            self._expect(call.line, Type("text"), args[0], "Item name")
            self._expect(call.line, Type("number"), args[1], "Stack size")
            return Type("number")
        if name == "modapi_register_block":
            if len(args) != 3:
                self._error(call.line, "modapi_register_block expects a name, material, and hardness")
            self._expect(call.line, Type("text"), args[0], "Block name")
            self._expect(call.line, Type("text"), args[1], "Block material")
            self._expect(call.line, Type("number"), args[2], "Block hardness")
            return Type("number")
        if name in {"list", "set", "empty_list", "empty_set"}:
            if any(_contains_resource(argument) for argument in args):
                self._error(call.line, "Resource handles cannot be stored in collections")
            collection_name = name.removeprefix("empty_")
            element = args[0] if args else (expected.arguments[0] if expected and expected.arguments else Type("any"))
            if collection_name == "set" and not _valid_set_element(element):
                self._error(call.line, f"Set elements must be hashable or string arrays, got {element}")
            for actual in args[1:]:
                self._expect(call.line, element, actual, f"{collection_name} element")
            return Type(collection_name, (element,))
        if name == "tuple":
            if any(_contains_resource(argument) for argument in args):
                self._error(call.line, "Resource handles cannot be stored in collections")
            return Type("tuple", tuple(args))
        if name in {"map", "empty_map"}:
            if any(_contains_resource(argument) for argument in args):
                self._error(call.line, "Resource handles cannot be stored in collections")
            key_type = args[0] if args else (
                expected.arguments[0] if expected and expected.name == "map" else Type("any")
            )
            value_type = args[1] if len(args) > 1 else (
                expected.arguments[1] if expected and expected.name == "map" else Type("any")
            )
            if not _hashable(key_type):
                self._error(call.line, f"Map keys must be hashable, got {key_type}")
            if len(args) % 2:
                self._error(call.line, "map expects alternating key and value arguments")
            for index in range(2, len(args), 2):
                self._expect(call.line, key_type, args[index], "Map key")
                self._expect(call.line, value_type, args[index + 1], "Map value")
            return Type("map", (key_type, value_type))
        if name == "channel":
            if len(args) != 1:
                self._error(call.line, "channel expects a capacity")
            self._expect(call.line, Type("number"), args[0], "Channel capacity")
            if expected and (
                _contains_resource(expected)
                or any(_contains_resource(argument) for argument in expected.arguments)
            ):
                self._error(call.line, "Resource handles cannot be stored in channels")
            return expected if expected and expected.name == "channel" else Type("channel", (Type("any"),))
        if name == "append":
            if len(args) != 2 or args[0].name != "list":
                self._error(call.line, "append expects a list and a value")
            if _contains_resource(args[0]) or _contains_resource(args[1]):
                self._error(call.line, "Resource handles cannot be stored in collections")
            self._expect(call.line, args[0].arguments[0], args[1], "List element")
            return Type("void")
        if name == "add_to_set":
            if len(args) != 2 or args[0].name != "set":
                self._error(call.line, "add_to_set expects a set and an element")
            if _contains_resource(args[0]) or _contains_resource(args[1]):
                self._error(call.line, "Resource handles cannot be stored in collections")
            self._expect(call.line, args[0].arguments[0], args[1], "Set element")
            return Type("void")
        if name == "put":
            if len(args) != 3 or args[0].name != "map":
                self._error(call.line, "put expects a map, key, and value")
            if any(_contains_resource(argument) for argument in args):
                self._error(call.line, "Resource handles cannot be stored in collections")
            self._expect(call.line, args[0].arguments[0], args[1], "Map key")
            self._expect(call.line, args[0].arguments[1], args[2], "Map value")
            return Type("void")
        if name == "insert":
            if len(args) != 3 or args[0].name != "list":
                self._error(call.line, "insert expects a list, index, and value")
            if _contains_resource(args[0]) or _contains_resource(args[2]):
                self._error(call.line, "Resource handles cannot be stored in collections")
            self._expect(call.line, Type("number"), args[1], "List index")
            self._expect(call.line, args[0].arguments[0], args[2], "List element")
            return Type("void")
        if name in {"get", "remove"}:
            if len(args) != 2:
                self._error(call.line, f"{name} expects a collection and a key")
            collection = args[0]
            if collection.name == "any" and name == "get":
                return Type("any")
            if collection.name == "list":
                self._expect(call.line, Type("number"), args[1], "List index")
                return collection.arguments[0] if name == "get" else Type("void")
            if collection.name == "tuple":
                self._expect(call.line, Type("number"), args[1], "Tuple index")
                if name == "remove":
                    self._error(call.line, "Tuples are immutable")
                return Type("any")
            if collection.name == "map":
                self._expect(call.line, collection.arguments[0], args[1], "Map key")
                return collection.arguments[1] if name == "get" else Type("void")
            if collection.name == "set" and name == "remove":
                self._expect(call.line, collection.arguments[0], args[1], "Set element")
                return Type("void")
            self._error(call.line, f"{name} expects a list, map, tuple, or set")
        if name == "contains":
            if len(args) != 2:
                self._error(call.line, "contains expects a collection and a value")
            collection = args[0]
            if collection.name == "map":
                self._expect(call.line, collection.arguments[0], args[1], "Map key")
            elif collection.name in {"list", "set"}:
                self._expect(call.line, collection.arguments[0], args[1], "Collection element")
            elif collection.name == "tuple":
                if not any(_compatible(item_type, args[1]) for item_type in collection.arguments):
                    self._error(call.line, f"Value {args[1]} cannot occur in {collection}")
            else:
                self._error(call.line, "contains expects a list, map, set, or tuple")
            return Type("boolean")
        if name in {"length", "keys", "values"}:
            if len(args) != 1:
                self._error(call.line, f"{name} expects one collection")
            collection = args[0]
            if name == "length":
                return Type("number")
            if collection.name != "map":
                self._error(call.line, f"{name} expects a map")
            return Type("list", (collection.arguments[0 if name == "keys" else 1],))
        if name in {"send", "receive"}:
            if not args or args[0].name != "channel":
                self._error(call.line, f"{name} expects a channel")
            if name == "send":
                if len(args) != 2:
                    self._error(call.line, "send expects a channel and a value")
                if (
                    _contains_resource(args[0])
                    or _contains_resource(args[1])
                    or any(_contains_resource(argument) for argument in args[0].arguments)
                ):
                    self._error(call.line, "Resource handles cannot be sent through channels")
                self._expect(call.line, args[0].arguments[0], args[1], "Channel message")
                return Type("task", (Type("void"),))
            return Type("task", (args[0].arguments[0],))
        if name == "close_channel":
            if len(args) != 1 or args[0].name != "channel":
                self._error(call.line, "close_channel expects a channel")
            return Type("void")
        if name == "sleep":
            if len(args) != 1:
                self._error(call.line, "sleep expects a duration in seconds")
            self._expect(call.line, Type("number"), args[0], "sleep duration")
            return Type("task", (Type("void"),))
        if name == "assert":
            if len(args) != 1:
                self._error(call.line, "assert expects one boolean condition")
            self._expect(call.line, Type("boolean"), args[0], "assert condition")
            return Type("void")
        return Type("any")

    def _validate_task_target(
        self, function: FunctionIR, line: int, seen: set[str] | None = None,
    ) -> None:
        seen = set() if seen is None else seen
        if function.name in seen:
            return
        seen.add(function.name)
        safe = {"number", "text", "boolean"}

        def safe_type(value: Type) -> bool:
            if value.name in safe:
                return True
            return (
                value.name == "channel" and len(value.arguments) == 1
                and safe_type(value.arguments[0])
            )

        for parameter in function.params:
            annotation = function.param_types.get(parameter)
            if annotation is None:
                self._error(
                    line or function.line,
                    f"Concurrent function {function.name!r} must type parameter {parameter!r}",
                )
            parameter_type = parse_type(annotation)
            if not safe_type(parameter_type):
                self._error(
                    line or function.line,
                    f"Concurrent function parameters must be primitive values or channels, got {parameter_type}",
                )
        if function.return_type is None:
            self._error(
                line or function.line,
                f"Concurrent function {function.name!r} must declare a return type",
            )
        result_type = parse_type(function.return_type)
        if result_type.name != "void" and not safe_type(result_type):
            self._error(
                line or function.line,
                f"Concurrent functions cannot return mutable values such as {result_type}",
            )
        global_names = {
            node.name for node in _walk(self.module.body)
            if isinstance(node, Create)
        }
        local_names = set(function.params) | {
            node.name for node in _walk(function.body)
            if isinstance(node, (Create, RangeLoop))
        }
        for node in _walk(function.body):
            if (
                isinstance(node, Variable) and node.name in global_names
                and node.name not in local_names
            ):
                self._error(
                    line or function.line,
                    f"Concurrent function {function.name!r} cannot access mutable global {node.name!r}",
                )
            if isinstance(node, Call) and node.name in GAME_FUNCTIONS:
                self._error(
                    line or function.line,
                    f"Concurrent function {function.name!r} cannot call game API {node.name!r}",
                )
            if isinstance(node, Call) and node.name in self.functions:
                self._validate_task_target(self.functions[node.name], line, seen)


    def _check_expression_context(self, is_async: bool) -> None:
        self._async_context = is_async

    def _statements(
        self,
        statements: list,
        env: dict[str, Type],
        return_type: Type | None,
        is_async: bool,
        function_line: int,
    ) -> None:
        self._check_expression_context(is_async)
        self._statements_impl(statements, env, return_type, is_async, function_line)

    def _statements_impl(
        self,
        statements: list,
        env: dict[str, Type],
        return_type: Type | None,
        is_async: bool,
        function_line: int,
    ) -> None:
        for statement in statements:
            if isinstance(statement, If):
                self._expression(statement.condition, env, Type("boolean"))
                original_owners = set(self._owned_resources)
                original_released = set(self._released_resources)
                left, right = dict(env), dict(env)
                self._statements(statement.body, left, return_type, is_async, function_line)
                left_owners = set(self._owned_resources)
                left_released = set(self._released_resources)
                self._owned_resources = set(original_owners)
                self._released_resources = set(original_released)
                self._statements(statement.otherwise, right, return_type, is_async, function_line)
                right_owners = set(self._owned_resources)
                right_released = set(self._released_resources)
                if isinstance(statement.condition, Literal) and isinstance(
                    statement.condition.value, bool
                ):
                    selected_env, selected_owners, selected_released = (
                        (left, left_owners, left_released)
                        if statement.condition.value else
                        (right, right_owners, right_released)
                    )
                    env.clear()
                    env.update(selected_env)
                    self._owned_resources = selected_owners
                    self._released_resources = selected_released
                else:
                    resources = (
                        original_owners | original_released
                        | left_owners | left_released
                        | right_owners | right_released
                    )
                    for name in resources:
                        if (
                            (name in left_owners, name in left_released)
                            != (name in right_owners, name in right_released)
                        ):
                            self._error(
                                statement.line,
                                f"Resource {name!r} must have the same ownership state "
                                "in both branches",
                            )
                    for name in left.keys() & right.keys():
                        if name in env:
                            env[name] = _merge(left[name], right[name])
                        elif left[name] == right[name]:
                            env[name] = left[name]
                    self._owned_resources = left_owners
                    self._released_resources = left_released
            elif isinstance(statement, While):
                self._expression(statement.condition, env, Type("boolean"))
                owners, released = set(self._owned_resources), set(self._released_resources)
                self._statements(statement.body, dict(env), return_type, is_async, function_line)
                cannot_execute = (
                    isinstance(statement.condition, Literal)
                    and statement.condition.value is False
                )
                if not cannot_execute and (
                    self._owned_resources != owners
                    or self._released_resources != released
                ):
                    self._error(statement.line, "Resource ownership cannot change inside a loop")
                self._owned_resources, self._released_resources = owners, released
            elif isinstance(statement, Repeat):
                self._expect(
                    statement.line, Type("number"),
                    self._expression(statement.count, env, Type("number")), "Repeat count",
                )
                owners, released = set(self._owned_resources), set(self._released_resources)
                self._statements(statement.body, dict(env), return_type, is_async, function_line)
                cannot_execute = (
                    isinstance(statement.count, Literal)
                    and statement.count.value == 0
                )
                if not cannot_execute and (
                    self._owned_resources != owners
                    or self._released_resources != released
                ):
                    self._error(statement.line, "Resource ownership cannot change inside a loop")
                self._owned_resources, self._released_resources = owners, released
            elif isinstance(statement, RangeLoop):
                self._expect(
                    statement.line, Type("number"),
                    self._expression(statement.start, env, Type("number")), "Range start",
                )
                self._expect(
                    statement.line, Type("number"),
                    self._expression(statement.end, env, Type("number")), "Range end",
                )
                loop_env = dict(env)
                loop_env[statement.name] = Type("number")
                owners, released = set(self._owned_resources), set(self._released_resources)
                self._statements(statement.body, loop_env, return_type, is_async, function_line)
                cannot_execute = (
                    isinstance(statement.start, Literal)
                    and isinstance(statement.end, Literal)
                    and type(statement.start.value) is int
                    and type(statement.end.value) is int
                    and statement.start.value > statement.end.value
                )
                if not cannot_execute and (
                    self._owned_resources != owners
                    or self._released_resources != released
                ):
                    self._error(statement.line, "Resource ownership cannot change inside a loop")
                self._owned_resources, self._released_resources = owners, released
            else:
                self._statement(statement, env, return_type, is_async)

    def _statement(
        self, statement, env: dict[str, Type], return_type: Type | None, is_async: bool,
    ) -> None:
        if isinstance(statement, Create):
            if statement.name in env:
                self._error(statement.line, f"Variable {statement.name!r} already exists")
            declared = parse_type(statement.type_annotation) if statement.type_annotation else None
            self._resource_initializer_call = (
                statement.value if isinstance(statement.value, Call)
                and statement.value.name in {"load_texture", "load_sound"} else None
            )
            try:
                inferred = self._expression(statement.value, env, declared)
            finally:
                self._resource_initializer_call = None
            if self.strict and _contains_any(inferred):
                self._error(
                    statement.line,
                    f"Strict mode cannot infer a concrete type for {statement.name!r}",
                )
            if declared:
                if self.strict and _contains_any(declared):
                    self._error(statement.line, "Strict mode forbids any in a type annotation")
                self._expect(statement.line, declared, inferred, "Declaration")
                if _contains_resource(declared) and declared.name not in _RESOURCE_TYPES:
                    self._error(statement.line, "Resource handles cannot be stored in collections")
                if _contains_resource(inferred) and declared != inferred:
                    self._error(
                        statement.line,
                        "A resource declaration must preserve its concrete resource type",
                    )
                env[statement.name] = declared
            else:
                env[statement.name] = inferred
            if _contains_resource(inferred):
                if inferred.name not in _RESOURCE_TYPES:
                    self._error(statement.line, "Resource handles cannot be stored in collections")
                creator = {"texture": "load_texture", "sound": "load_sound"}[inferred.name]
                if not isinstance(statement.value, Call) or statement.value.name != creator:
                    self._error(
                        statement.line,
                        f"Resource handles cannot be copied by declaration; "
                        f"{inferred.name} ownership must come directly from {creator}",
                    )
                self._owned_resources.add(statement.name)
        elif isinstance(statement, Assign):
            if statement.name not in env:
                self._error(statement.line, f"Unknown variable {statement.name!r}")
            if _contains_resource(env[statement.name]):
                self._error(
                    statement.line,
                    f"Owned resource {statement.name!r} cannot be reassigned",
                )
            actual = self._expression(statement.value, env, env[statement.name])
            if _contains_resource(actual):
                self._error(statement.line, "Resource handles cannot be copied by assignment")
            self._expect(statement.line, env[statement.name], actual, "Assignment")
        elif isinstance(statement, Display):
            self._expression(statement.value, env)
        elif isinstance(statement, CallStatement):
            result = self._expression(statement.call, env)
            if result.name == "task":
                self._error(
                    statement.line,
                    "Async calls must be awaited or stored as a task",
                )
        elif isinstance(statement, Return):
            actual = self._expression(statement.value, env, return_type)
            if _contains_resource(actual):
                self._error(statement.line, "Resource handles cannot be returned")
            self._check_owned_resources_released(statement.line)
            if return_type:
                self._expect(statement.line, return_type, actual, "Return")


def _walk(value):
    yield value
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
    elif is_dataclass(value):
        for item in fields(value):
            yield from _walk(getattr(value, item.name))


def _is_type_variable(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]", name))


def _type_variables(value: Type) -> set[str]:
    result = {value.name} if _is_type_variable(value.name) else set()
    for argument in value.arguments:
        result.update(_type_variables(argument))
    return result


def _substitute_type(value: Type, substitutions: dict[str, Type]) -> Type:
    if _is_type_variable(value.name):
        return substitutions.get(value.name, value)
    return Type(
        value.name,
        tuple(_substitute_type(argument, substitutions) for argument in value.arguments),
    )


def _unify(
    pattern: Type,
    actual: Type,
    generic_params: set[str],
    substitutions: dict[str, Type],
) -> None:
    if pattern.name in generic_params:
        previous = substitutions.get(pattern.name)
        if previous is None:
            substitutions[pattern.name] = actual
        elif not _compatible(previous, actual) or not _compatible(actual, previous):
            raise TypeCheckError(f"Generic type {pattern.name} was inferred as both {previous} and {actual}")
        return
    if actual.name == "any" or pattern.name == "any":
        return
    if pattern.name != actual.name or len(pattern.arguments) != len(actual.arguments):
        return
    for expected, received in zip(pattern.arguments, actual.arguments):
        _unify(expected, received, generic_params, substitutions)
