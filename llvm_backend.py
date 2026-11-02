"""Direct LLVM IR backend for Zelix's typed numeric and voxel-game subset."""

from __future__ import annotations

import re
from dataclasses import dataclass

from game_backend import GAME_FUNCTIONS, GAME_FUNCTION_IDS, GAME_FUNCTION_RETURN_TYPES
from syntax import (
    Assign, Binary, Call, CallStatement, Create, Display, Expr, FunctionIR, If,
    Input, Literal, ModuleIR, RangeLoop, Repeat, Return, Stmt, Unary, Variable,
    While,
)
from typesys import Type, TypeChecker, TypeCheckError, parse_type


@dataclass(frozen=True)
class LLVMValue:
    value: str
    type: Type


class LLVMBackend:
    SUPPORTED_TYPES = {"number", "boolean", "text", "list", "void"}

    def __init__(self, module: ModuleIR):
        self.module = module
        self.checker = TypeChecker(module)
        self.checker.check()
        self.function_map = {function.name: function for function in module.functions}
        self.global_names = sorted(_defined_names(module.body))
        self.global_types = self._statement_types(module.body, {})
        self.strings: dict[str, tuple[str, bytes]] = {}
        self.lines: list[str] = []
        self.temp_id = 0
        self.block_id = 0
        self.loop_id = 0
        self.current_lines: list[str] = []
        self.entry_allocas: list[str] = []
        self.current_label = ""
        self.terminated = False
        self.variables: dict[str, str] = {}
        self.initialized: dict[str, str] = {}
        self.variable_types: dict[str, Type] = {}
        self.local_names: set[str] = set()
        self.current_function: FunctionIR | None = None

    def generate(self) -> str:
        self._validate_module()
        declarations = [
            'source_filename = "zelix"',
            "%ZValue = type { i32, double, ptr, ptr, ptr, ptr }",
            "declare ptr @z_llvm_list_new(i32)",
            "declare void @z_llvm_list_append(ptr, double, i32)",
            "declare void @z_llvm_list_insert(ptr, double, double, i32)",
            "declare void @z_llvm_list_remove(ptr, double, i32)",
            "declare double @z_llvm_list_get(ptr, double, i32)",
            "declare double @z_llvm_number_divide(double, double, i32)",
            "declare double @z_llvm_number_modulo(double, double, i32)",
            "declare i64 @z_llvm_to_integer(double, i32)",
            "declare i64 @z_llvm_repeat_count(double, i32)",
            "declare void @z_llvm_loop_guard(i64, i32)",
            "declare void @z_llvm_require_initialized(i32, i32)",
            "declare void @z_llvm_require_uninitialized(i32, i32)",
            "declare void @z_llvm_value_number(ptr, double)",
            "declare void @z_llvm_value_boolean(ptr, i32)",
            "declare void @z_llvm_value_text(ptr, ptr)",
            "declare void @z_llvm_value_list(ptr, ptr)",
            "declare void @z_llvm_game_void(i32, i32, ptr, i32)",
            "declare double @z_llvm_game_number(i32, i32, ptr, i32)",
            "declare i32 @z_llvm_game_boolean(i32, i32, ptr, i32)",
            "declare void @z_llvm_print_number(double)",
            "declare void @z_llvm_print_boolean(i32)",
            "declare void @z_llvm_print_text(ptr)",
            "",
        ]
        self.lines = declarations
        for name in self.global_names:
            value_type = self._llvm_type(self.global_types[name], 1)
            ident = _ident(name)
            self.lines.extend([
                f"@zelix_global_{ident} = internal global {value_type} {self._zero(self.global_types[name])}",
                f"@zelix_initialized_{ident} = internal global i1 false",
            ])
        if self.global_names:
            self.lines.append("")

        self._compile_functions()
        self._compile_entry()

        string_definitions = [
            f"@{name} = private unnamed_addr constant [{len(data) + 1} x i8] "
            f'c"{_llvm_bytes(data + bytes([0]))}", align 1'
            for name, data in self.strings.values()
        ]
        if string_definitions:
            insertion = next(
                (index for index, line in enumerate(self.lines) if line.startswith("@zelix_global_")),
                len(declarations),
            )
            self.lines[insertion:insertion] = string_definitions + [""]
        return "\n".join(self.lines).rstrip() + "\n"

    def _validate_module(self) -> None:
        if any(function.is_async or function.generic_params for function in self.module.functions):
            function = next(
                function for function in self.module.functions
                if function.is_async or function.generic_params
            )
            self._error(function.line, "LLVM backend does not support async or generic functions")
        for function in self.module.functions:
            if function.return_type is None:
                self._error(function.line, "LLVM backend requires an explicit function return type")
            for name in function.params:
                if name not in function.param_types:
                    self._error(function.line, f"LLVM backend requires a type for parameter {name!r}")
        for value_type in self.global_types.values():
            self._llvm_type(value_type, 1)
        for function in self.module.functions:
            local_types = self._statement_types(function.body, self.global_types)
            local_types.update({
                name: parse_type(function.param_types[name])
                for name in function.params
            })
            for value_type in local_types.values():
                self._llvm_type(value_type, function.line)

    def _statement_types(
        self, statements: list[Stmt], initial: dict[str, Type],
    ) -> dict[str, Type]:
        result = dict(initial)
        for statement in statements:
            if isinstance(statement, Create):
                result[statement.name] = (
                    parse_type(statement.type_annotation)
                    if statement.type_annotation
                    else self.checker.expression_types[id(statement.value)]
                )
            elif isinstance(statement, RangeLoop):
                result[statement.name] = Type("number")
                result.update(self._statement_types(statement.body, result))
            elif isinstance(statement, (If, While, Repeat)):
                result.update(self._statement_types(statement.body, result))
                if isinstance(statement, If):
                    result.update(self._statement_types(statement.otherwise, result))
        return result

    def _compile_functions(self) -> None:
        for function in self.module.functions:
            self.current_function = function
            self.current_lines = []
            self.entry_allocas = []
            self.temp_id = 0
            self.block_id = 0
            self.loop_id = 0
            local_types = self._statement_types(function.body, self.global_types)
            local_types.update({
                name: parse_type(function.param_types[name])
                for name in function.params
            })
            self.local_names = _defined_names(function.body) | set(function.params)
            names = sorted(self.local_names | set(self.global_names))
            self.variables = {name: f"%slot_{_ident(name)}" for name in names}
            self.initialized = {name: f"%init_{_ident(name)}" for name in names}
            self.variable_types = {
                name: local_types.get(name, self.global_types.get(name, Type("any")))
                for name in names
            }
            return_type = parse_type(function.return_type or "void")
            params = ", ".join(
                f"{self._llvm_type(parse_type(function.param_types[name]), function.line)} "
                f"%arg_{_ident(name)}"
                for name in function.params
            )
            self.lines.append(
                f"define {self._llvm_type(return_type, function.line)} "
                f"@zelix_fn_{_ident(function.name)}({params}) {{"
            )
            self._start_block("entry")
            for name in names:
                value_type = self.variable_types[name]
                self._emit(f"{self.variables[name]} = alloca {self._llvm_type(value_type, function.line)}")
                self._emit(f"{self.initialized[name]} = alloca i1")
                self._emit(f"store i1 false, ptr {self.initialized[name]}")
            for name in self.global_names:
                if name in self.variables:
                    value_type = self._llvm_type(self.variable_types[name], function.line)
                    loaded = self._temp()
                    loaded_init = self._temp()
                    self._emit(f"{loaded} = load {value_type}, ptr @zelix_global_{_ident(name)}")
                    self._emit(f"store {value_type} {loaded}, ptr {self.variables[name]}")
                    self._emit(f"{loaded_init} = load i1, ptr @zelix_initialized_{_ident(name)}")
                    self._emit(f"store i1 {loaded_init}, ptr {self.initialized[name]}")
            for name in function.params:
                value_type = self._llvm_type(self.variable_types[name], function.line)
                self._emit(f"store {value_type} %arg_{_ident(name)}, ptr {self.variables[name]}")
                self._emit(f"store i1 true, ptr {self.initialized[name]}")
            self._compile_statements(function.body)
            if not self.terminated:
                if return_type.name == "void":
                    self._emit("ret void")
                elif return_type.name == "number":
                    self._emit("ret double 0.000000e+00")
                elif return_type.name == "boolean":
                    self._emit("ret i1 false")
                else:
                    self._emit(f"ret {self._llvm_type(return_type, function.line)} null")
            self._finish_function()
            self.current_function = None

    def _compile_entry(self) -> None:
        self.current_function = None
        self.current_lines = []
        self.entry_allocas = []
        self.temp_id = 0
        self.block_id = 0
        self.loop_id = 0
        self.local_names = set(self.global_names)
        self.variables = {
            name: f"@zelix_global_{_ident(name)}" for name in self.global_names
        }
        self.initialized = {
            name: f"@zelix_initialized_{_ident(name)}" for name in self.global_names
        }
        self.variable_types = dict(self.global_types)
        self._emit_function_header("define i32 @z_llvm_main() {")
        self._start_block("entry")
        self._compile_statements(self.module.body)
        if not self.terminated:
            self._emit("ret i32 0")
        self._finish_function()

    def _emit_function_header(self, header: str) -> None:
        self.lines.append(header)

    def _finish_function(self) -> None:
        self.current_lines[1:1] = [f"  {allocation}" for allocation in self.entry_allocas]
        self.lines.extend(self.current_lines)
        self.lines.extend(["}", ""])
        self.current_lines = []
        self.entry_allocas = []

    def _compile_statements(self, statements: list[Stmt]) -> None:
        for statement in statements:
            if self.terminated:
                break
            if isinstance(statement, Create):
                value = self._expression(statement.value)
                self._require_uninitialized(statement.name, statement.line)
                self._store(statement.name, value, statement.line)
            elif isinstance(statement, Assign):
                value = self._expression(statement.value)
                self._require_initialized(statement.name, statement.line)
                self._store(statement.name, value, statement.line)
            elif isinstance(statement, Display):
                value = self._expression(statement.value)
                if value.type.name == "number":
                    self._emit(f"call void @z_llvm_print_number(double {value.value})")
                elif value.type.name == "boolean":
                    flag = self._to_i32(value)
                    self._emit(f"call void @z_llvm_print_boolean(i32 {flag})")
                elif value.type.name == "text":
                    self._emit(f"call void @z_llvm_print_text(ptr {value.value})")
                else:
                    self._error(statement.line, f"LLVM display does not support {value.type}")
            elif isinstance(statement, CallStatement):
                self._expression(statement.call)
            elif isinstance(statement, Return):
                value = self._expression(statement.value)
                if self.current_function is None:
                    self._error(statement.line, "return can only be used inside a function")
                return_type = parse_type(self.current_function.return_type or "void")
                if return_type.name == "void":
                    self._emit("ret void")
                else:
                    self._emit(f"ret {self._llvm_type(return_type, statement.line)} {value.value}")
                self.terminated = True
            elif isinstance(statement, If):
                self._if_statement(statement)
            elif isinstance(statement, While):
                self._while_statement(statement)
            elif isinstance(statement, Repeat):
                self._repeat_statement(statement)
            elif isinstance(statement, RangeLoop):
                self._range_statement(statement)
            else:
                self._error(statement.line, f"LLVM backend does not support {type(statement).__name__}")

    def _if_statement(self, statement: If) -> None:
        condition = self._expression(statement.condition)
        then_label = self._new_block("if_then")
        else_label = self._new_block("if_else")
        merge_label = self._new_block("if_end")
        self._emit(f"br i1 {condition.value}, label %{then_label}, label %{else_label}")
        self.terminated = True

        self._start_block(then_label)
        self._compile_statements(statement.body)
        then_terminated = self.terminated
        if not then_terminated:
            self._emit(f"br label %{merge_label}")
            self.terminated = True

        self._start_block(else_label)
        self._compile_statements(statement.otherwise)
        else_terminated = self.terminated
        if not else_terminated:
            self._emit(f"br label %{merge_label}")
            self.terminated = True

        self._start_block(merge_label)
        if then_terminated and else_terminated:
            self._emit("unreachable")
            self.terminated = True

    def _while_statement(self, statement: While) -> None:
        loop_id = self.loop_id
        self.loop_id += 1
        preheader = self.current_label
        condition_label = self._new_block("while_cond")
        body_label = self._new_block("while_body")
        step_label = self._new_block("while_step")
        exit_label = self._new_block("while_end")
        self._emit(f"br label %{condition_label}")
        self.terminated = True
        self._start_block(condition_label)
        iteration = self._temp()
        self._emit(
            f"{iteration} = phi i64 [ 0, %{preheader} ], "
            f"[ %loop_next_{loop_id}, %{step_label} ]"
        )
        condition = self._expression(statement.condition)
        self._emit(f"br i1 {condition.value}, label %{body_label}, label %{exit_label}")
        self.terminated = True
        self._start_block(body_label)
        self._emit(f"call void @z_llvm_loop_guard(i64 {iteration}, i32 {statement.line})")
        self._compile_statements(statement.body)
        if not self.terminated:
            self._emit(f"br label %{step_label}")
            self.terminated = True
        self._start_block(step_label)
        next_value = f"%loop_next_{loop_id}"
        self._emit(f"{next_value} = add i64 {iteration}, 1")
        self._emit(f"br label %{condition_label}")
        self.terminated = True
        self._start_block(exit_label)

    def _repeat_statement(self, statement: Repeat) -> None:
        count = self._expression(statement.count)
        count_int = self._temp()
        self._emit(
            f"{count_int} = call i64 @z_llvm_repeat_count("
            f"double {count.value}, i32 {statement.line})"
        )
        self._counted_loop(statement.body, statement.line, count_int, inclusive=False)

    def _range_statement(self, statement: RangeLoop) -> None:
        start_value = self._expression(statement.start)
        end_value = self._expression(statement.end)
        start = self._temp()
        end = self._temp()
        self._emit(
            f"{start} = call i64 @z_llvm_to_integer(double {start_value.value}, "
            f"i32 {statement.line})"
        )
        self._emit(
            f"{end} = call i64 @z_llvm_to_integer(double {end_value.value}, "
            f"i32 {statement.line})"
        )
        self._counted_loop(
            statement.body, statement.line, end, inclusive=True,
            variable=statement.name, start=start,
        )

    def _counted_loop(
        self,
        body: list[Stmt],
        line: int,
        end: str,
        *,
        inclusive: bool,
        variable: str | None = None,
        start: str | None = None,
    ) -> None:
        loop_id = self.loop_id
        self.loop_id += 1
        preheader = self.current_label
        condition_label = self._new_block("range_cond")
        body_label = self._new_block("range_body")
        step_label = self._new_block("range_step")
        overflow_label = self._new_block("range_overflow")
        exit_label = self._new_block("range_end")
        initial = start if start is not None else "0"
        self._emit(f"br label %{condition_label}")
        self.terminated = True
        self._start_block(condition_label)
        index = f"%range_index_{loop_id}"
        self._emit(
            f"{index} = phi i64 [ {initial}, %{preheader} ], "
            f"[ %range_next_{loop_id}, %{step_label} ]"
        )
        if inclusive:
            comparison = self._temp()
            self._emit(f"{comparison} = icmp sle i64 {index}, {end}")
        else:
            comparison = self._temp()
            self._emit(f"{comparison} = icmp slt i64 {index}, {end}")
        self._emit(f"br i1 {comparison}, label %{body_label}, label %{exit_label}")
        self.terminated = True
        self._start_block(body_label)
        if variable is not None:
            number = self._temp()
            self._emit(f"{number} = sitofp i64 {index} to double")
            self._store(variable, LLVMValue(number, Type("number")), line)
        self._compile_statements(body)
        if not self.terminated:
            self._emit(f"br label %{overflow_label}")
            self.terminated = True
        self._start_block(overflow_label)
        at_maximum = self._temp()
        self._emit(f"{at_maximum} = icmp eq i64 {index}, 9223372036854775807")
        self._emit(
            f"br i1 {at_maximum}, label %{exit_label}, label %{step_label}"
        )
        self.terminated = True
        self._start_block(step_label)
        self._emit(f"%range_next_{loop_id} = add i64 {index}, 1")
        self._emit(f"br label %{condition_label}")
        self.terminated = True
        self._start_block(exit_label)

    def _expression(self, expression: Expr) -> LLVMValue:
        if isinstance(expression, Literal):
            if isinstance(expression.value, bool):
                return LLVMValue("true" if expression.value else "false", Type("boolean"))
            if isinstance(expression.value, (int, float)):
                return LLVMValue(_float(expression.value), Type("number"))
            if isinstance(expression.value, str):
                return LLVMValue(self._string_pointer(expression.value), Type("text"))
            self._error(expression.line, "LLVM backend does not support null literals")
        if isinstance(expression, Variable):
            self._require_initialized(expression.name, expression.line)
            value_type = self.variable_types.get(expression.name, self.global_types.get(expression.name))
            if value_type is None:
                self._error(expression.line, f"Unknown variable {expression.name!r}")
            loaded = self._temp()
            llvm_type = self._llvm_type(value_type, expression.line)
            self._emit(f"{loaded} = load {llvm_type}, ptr {self.variables[expression.name]}")
            return LLVMValue(loaded, value_type)
        if isinstance(expression, Input):
            self._error(expression.line, "LLVM backend does not support input expressions")
        if isinstance(expression, Unary) and expression.op == "not":
            value = self._expression(expression.value)
            result = self._temp()
            self._emit(f"{result} = xor i1 {value.value}, true")
            return LLVMValue(result, Type("boolean"))
        if isinstance(expression, Binary):
            return self._binary(expression)
        if isinstance(expression, Call):
            return self._call(expression)
        self._error(expression.line, f"LLVM backend does not support {type(expression).__name__}")
        raise AssertionError

    def _binary(self, expression: Binary) -> LLVMValue:
        left = self._expression(expression.left)
        right = self._expression(expression.right)
        if expression.op in {"and", "or"}:
            result = self._temp()
            opcode = "and" if expression.op == "and" else "or"
            self._emit(f"{result} = {opcode} i1 {left.value}, {right.value}")
            return LLVMValue(result, Type("boolean"))
        if left.type.name == right.type.name == "number":
            if expression.op in {"add", "sub", "mul"}:
                result = self._temp()
                opcode = {"add": "fadd", "sub": "fsub", "mul": "fmul"}[expression.op]
                self._emit(f"{result} = {opcode} double {left.value}, {right.value}")
                return LLVMValue(result, Type("number"))
            if expression.op == "div":
                result = self._temp()
                self._emit(
                    f"{result} = call double @z_llvm_number_divide("
                    f"double {left.value}, double {right.value}, i32 {expression.line})"
                )
                return LLVMValue(result, Type("number"))
            if expression.op == "mod":
                result = self._temp()
                self._emit(
                    f"{result} = call double @z_llvm_number_modulo("
                    f"double {left.value}, double {right.value}, i32 {expression.line})"
                )
                return LLVMValue(result, Type("number"))
            predicate = {
                "eq": "oeq", "ne": "une", "gt": "ogt", "lt": "olt",
                "gte": "oge", "lte": "ole",
            }.get(expression.op)
            if predicate:
                result = self._temp()
                self._emit(
                    f"{result} = fcmp {predicate} double {left.value}, {right.value}"
                )
                return LLVMValue(result, Type("boolean"))
        if left.type.name == right.type.name == "boolean" and expression.op in {"eq", "ne"}:
            result = self._temp()
            predicate = "eq" if expression.op == "eq" else "ne"
            self._emit(f"{result} = icmp {predicate} i1 {left.value}, {right.value}")
            return LLVMValue(result, Type("boolean"))
        self._error(expression.line, f"LLVM backend does not support operator {expression.op!r} for {left.type}")
        raise AssertionError

    def _call(self, expression: Call) -> LLVMValue:
        name = expression.name
        if name in GAME_FUNCTIONS:
            arguments = [self._expression(argument) for argument in expression.args]
            array = self._value_array(arguments)
            game_id = GAME_FUNCTION_IDS[name]
            return_type = parse_type(GAME_FUNCTION_RETURN_TYPES.get(name, "void"))
            if return_type.name == "void":
                self._emit(
                    f"call void @z_llvm_game_void(i32 {game_id}, i32 {len(arguments)}, "
                    f"ptr {array}, i32 {expression.line})"
                )
                return LLVMValue("0", Type("void"))
            if return_type.name == "boolean":
                raw = self._temp()
                self._emit(
                    f"{raw} = call i32 @z_llvm_game_boolean(i32 {game_id}, "
                    f"i32 {len(arguments)}, ptr {array}, i32 {expression.line})"
                )
                result = self._temp()
                self._emit(f"{result} = icmp ne i32 {raw}, 0")
                return LLVMValue(result, return_type)
            if return_type.name == "number":
                result = self._temp()
                self._emit(
                    f"{result} = call double @z_llvm_game_number(i32 {game_id}, "
                    f"i32 {len(arguments)}, ptr {array}, i32 {expression.line})"
                )
                return LLVMValue(result, return_type)
            self._error(expression.line, f"LLVM backend does not support the {return_type} result from {name}")
        if name in {"empty_list", "list"}:
            values = [self._expression(argument) for argument in expression.args]
            collection = self._temp()
            self._emit(f"{collection} = call ptr @z_llvm_list_new(i32 {expression.line})")
            for value in values:
                if value.type.name != "number":
                    self._error(expression.line, "LLVM backend lists currently contain numbers only")
                self._emit(
                    f"call void @z_llvm_list_append(ptr {collection}, "
                    f"double {value.value}, i32 {expression.line})"
                )
            result_type = self.checker.expression_types.get(id(expression), Type("list", (Type("number"),)))
            return LLVMValue(collection, result_type)
        if name in {"append", "insert", "remove", "get"}:
            values = [self._expression(argument) for argument in expression.args]
            if name == "append":
                self._emit(
                    f"call void @z_llvm_list_append(ptr {values[0].value}, "
                    f"double {values[1].value}, i32 {expression.line})"
                )
                return LLVMValue("0", Type("void"))
            if name == "insert":
                self._emit(
                    f"call void @z_llvm_list_insert(ptr {values[0].value}, "
                    f"double {values[1].value}, double {values[2].value}, "
                    f"i32 {expression.line})"
                )
                return LLVMValue("0", Type("void"))
            if name == "remove":
                self._emit(
                    f"call void @z_llvm_list_remove(ptr {values[0].value}, "
                    f"double {values[1].value}, i32 {expression.line})"
                )
                return LLVMValue("0", Type("void"))
            result = self._temp()
            self._emit(
                f"{result} = call double @z_llvm_list_get(ptr {values[0].value}, "
                f"double {values[1].value}, i32 {expression.line})"
            )
            return LLVMValue(result, Type("number"))
        if name in self.function_map:
            function = self.function_map[name]
            arguments = [self._expression(argument) for argument in expression.args]
            return_type = parse_type(function.return_type or "void")
            params = ", ".join(
                f"{self._llvm_type(value.type, expression.line)} {value.value}"
                for value in arguments
            )
            signature = self._llvm_type(return_type, expression.line)
            if return_type.name == "void":
                self._emit(f"call void @zelix_fn_{_ident(name)}({params})")
                return LLVMValue("0", return_type)
            result = self._temp()
            self._emit(
                f"{result} = call {signature} @zelix_fn_{_ident(name)}({params})"
            )
            return LLVMValue(result, return_type)
        self._error(expression.line, f"LLVM backend does not support function {name!r}")
        raise AssertionError

    def _value_array(self, arguments: list[LLVMValue]) -> str:
        if not arguments:
            return "null"
        storage = self._temp()
        self.entry_allocas.append(f"{storage} = alloca [{len(arguments)} x %ZValue]")
        for index, value in enumerate(arguments):
            if value.type.name == "number":
                boxed = self._temp()
                self._emit(
                    f"{boxed} = getelementptr inbounds [{len(arguments)} x %ZValue], "
                    f"ptr {storage}, i64 0, i64 {index}"
                )
                self._emit(
                    f"call void @z_llvm_value_number(ptr {boxed}, double {value.value})"
                )
            elif value.type.name == "boolean":
                flag = self._to_i32(value)
                boxed = self._temp()
                self._emit(
                    f"{boxed} = getelementptr inbounds [{len(arguments)} x %ZValue], "
                    f"ptr {storage}, i64 0, i64 {index}"
                )
                self._emit(
                    f"call void @z_llvm_value_boolean(ptr {boxed}, i32 {flag})"
                )
            elif value.type.name == "text":
                boxed = self._temp()
                self._emit(
                    f"{boxed} = getelementptr inbounds [{len(arguments)} x %ZValue], "
                    f"ptr {storage}, i64 0, i64 {index}"
                )
                self._emit(
                    f"call void @z_llvm_value_text(ptr {boxed}, ptr {value.value})"
                )
            elif value.type.name == "list":
                boxed = self._temp()
                self._emit(
                    f"{boxed} = getelementptr inbounds [{len(arguments)} x %ZValue], "
                    f"ptr {storage}, i64 0, i64 {index}"
                )
                self._emit(
                    f"call void @z_llvm_value_list(ptr {boxed}, ptr {value.value})"
                )
            else:
                self._error(1, f"LLVM game calls do not support {value.type} arguments")
        return storage

    def _store(self, name: str, value: LLVMValue, line: int) -> None:
        variable_type = self.variable_types.get(name, self.global_types.get(name))
        if variable_type is None:
            self._error(line, f"Unknown variable {name!r}")
        self._expect_type(line, variable_type, value.type, f"Variable {name!r}")
        llvm_type = self._llvm_type(variable_type, line)
        self._emit(f"store {llvm_type} {value.value}, ptr {self.variables[name]}")
        self._emit(f"store i1 true, ptr {self.initialized[name]}")

    def _require_initialized(self, name: str, line: int) -> None:
        if name not in self.initialized:
            self._error(line, f"Unknown variable {name!r}")
        value = self._temp()
        flag_type = "i1"
        self._emit(f"{value} = load {flag_type}, ptr {self.initialized[name]}")
        as_int = self._temp()
        self._emit(f"{as_int} = zext i1 {value} to i32")
        self._emit(f"call void @z_llvm_require_initialized(i32 {as_int}, i32 {line})")

    def _require_uninitialized(self, name: str, line: int) -> None:
        if name not in self.initialized:
            self._error(line, f"Unknown variable {name!r}")
        value = self._temp()
        self._emit(f"{value} = load i1, ptr {self.initialized[name]}")
        as_int = self._temp()
        self._emit(f"{as_int} = zext i1 {value} to i32")
        self._emit(f"call void @z_llvm_require_uninitialized(i32 {as_int}, i32 {line})")

    def _to_i32(self, value: LLVMValue) -> str:
        result = self._temp()
        self._emit(f"{result} = zext i1 {value.value} to i32")
        return result

    def _llvm_type(self, value_type: Type, line: int) -> str:
        if value_type.name == "number":
            return "double"
        if value_type.name == "boolean":
            return "i1"
        if value_type.name == "text":
            return "ptr"
        if value_type.name == "list" and value_type.arguments == (Type("number"),):
            return "ptr"
        if value_type.name == "void":
            return "void"
        self._error(line, f"LLVM backend does not support type {value_type}")
        raise AssertionError

    def _zero(self, value_type: Type) -> str:
        llvm_type = self._llvm_type(value_type, 1)
        if llvm_type == "ptr":
            return "null"
        if llvm_type == "i1":
            return "false"
        return "0.000000e+00"

    def _expect_type(self, line: int, expected: Type, actual: Type, context: str) -> None:
        if expected != actual and expected.name != "any" and actual.name != "any":
            self._error(line, f"{context} expects {expected}, got {actual}")

    def _string_pointer(self, value: str) -> str:
        if value not in self.strings:
            name = f"zelix_string_{len(self.strings)}"
            self.strings[value] = (name, value.encode("utf-8"))
        name, data = self.strings[value]
        return (
            f"getelementptr inbounds ([{len(data) + 1} x i8], ptr @{name}, "
            "i64 0, i64 0)"
        )

    def _start_block(self, label: str) -> None:
        self.current_label = label
        self.current_lines.append(f"{label}:")
        self.terminated = False

    def _new_block(self, prefix: str) -> str:
        label = f"{prefix}_{self.block_id}"
        self.block_id += 1
        return label

    def _temp(self) -> str:
        value = f"%v{self.temp_id}"
        self.temp_id += 1
        return value

    def _emit(self, instruction: str) -> None:
        if self.terminated:
            raise RuntimeError(f"LLVM instruction emitted after terminator in {self.current_label}")
        self.current_lines.append(f"  {instruction}")

    def _error(self, line: int, message: str) -> None:
        raise ValueError(f"Line {line}: {message}")


def _defined_names(statements: list[Stmt]) -> set[str]:
    names: set[str] = set()
    for statement in statements:
        if isinstance(statement, Create):
            names.add(statement.name)
        elif isinstance(statement, RangeLoop):
            names.add(statement.name)
            names.update(_defined_names(statement.body))
        elif isinstance(statement, (If, While, Repeat)):
            names.update(_defined_names(statement.body))
            if isinstance(statement, If):
                names.update(_defined_names(statement.otherwise))
    return names


def _ident(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def _float(value: int | float) -> str:
    return f"{float(value):.17e}"


def _llvm_bytes(value: bytes) -> str:
    result = []
    for byte in value:
        if 32 <= byte <= 126 and byte not in {34, 92}:
            result.append(chr(byte))
        else:
            result.append(f"\\{byte:02X}")
    return "".join(result)


def emit_llvm_ir(module: ModuleIR) -> str:
    try:
        return LLVMBackend(module).generate()
    except (TypeCheckError, ValueError) as exc:
        from compiler import CompileError

        raise CompileError(str(exc)) from exc
