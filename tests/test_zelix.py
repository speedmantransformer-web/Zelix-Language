import contextlib
import io
import json
import os
import queue
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zelix import Interpreter, ExpressionParser, ZelixError
from compiler import (
    CGenerator, CompileError, ZelixParser, compile_file, emit_ir_file, format_ir,
    optimize, validate_file, validate_source,
)
from project import ProjectError, init_project, install_project
from debug_server import DebugController, DebuggerStopped
from syntax import Call, FunctionIR, Lexer, ModuleIR, parse_source
from game_backend import GAME_FUNCTIONS, GAME_RUNTIME_C

STRING_ARRAY_SET_SOURCE = (
    "create labels as set<list<string>> with set with "
    "(list with text red end text and text blue end text) and "
    "(list with text red end text and text blue end text)\n"
    "display length with labels\n"
    "display contains with labels and "
    "(list with text red end text and text blue end text)\n"
    "call add_to_set with labels and (list with text green end text)\n"
    "display length with labels\n"
    "call remove with labels and "
    "(list with text red end text and text blue end text)\n"
    "display contains with labels and "
    "(list with text red end text and text blue end text)\n"
)


class ZelixTests(unittest.TestCase):
    def test_math_words(self):
        self.assertEqual(ExpressionParser("10 plus 5 times 2", {}).parse(), 20)

    def test_variables_and_assignment(self):
        src = "create score as 10\nscore becomes score plus 5\ndisplay score\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.zelix"
            p.write_text(src, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                Interpreter().run_file(p)
            self.assertEqual(out.getvalue().strip(), "15")

    def test_input_expression_can_be_reassigned_without_a_prompt(self):
        source = (
            "create event as input text\n"
            "event becomes input text\n"
            "display event\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input-expression.zelix"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            with patch("builtins.input", side_effect=["first", "second"]) as read_input:
                with contextlib.redirect_stdout(output):
                    Interpreter().run_file(path)
        self.assertEqual(output.getvalue().strip(), "second")
        self.assertEqual(read_input.call_args_list[1].args, ("",))

    def test_input_expression_is_generated_for_native_programs(self):
        generated = CGenerator(parse_source(
            "create event as text start end text\n"
            "event becomes input text\n"
        )).generate()
        self.assertIn('z_input(0, 2, "")', generated)

    def test_minecraft_zelix_loader_example_dispatches_events(self):
        example = (
            Path(__file__).resolve().parents[1]
            / "examples"
            / "minecraft-zelix-loader"
            / "mods"
            / "hello-world"
            / "main.zelix"
        )
        validate_file(example)
        output = io.StringIO()
        with patch(
            "builtins.input",
            side_effect=["minecraft_version_1_12_2", "load", "tick", "stop"],
        ):
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(example)
        self.assertIn("Hello World is running on Minecraft Java 1.12.2", output.getvalue())
        self.assertIn("Hello World mod loaded", output.getvalue())
        self.assertIn("Hello World received a periodic client update", output.getvalue())

    def test_function(self):
        src = "function add taking first and second\n    return first plus second\nend function\ncreate answer as add with 10 and 20\ndisplay answer\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.zelix"
            p.write_text(src, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                Interpreter().run_file(p)
            self.assertEqual(out.getvalue().strip(), "30")

    def test_interpreter_and_compiler_share_parser_and_support_nested_calls(self):
            source = (
                "function add taking first and second\n"
                "    return first plus second\n"
                "end function\n"
                "function identity taking value\n"
                "    return value\n"
                "end function\n"
                "create answer as add with (identity with (2 plus 3)) and 4\n"
                "create phrase as identity with text apples and oranges end text\n"
                "display answer\n"
                "display phrase\n"
            )
            module = parse_source(source)
            self.assertIsInstance(module, ModuleIR)
            self.assertIsInstance(module.functions[0], FunctionIR)
            self.assertIsInstance(module.body[0].value, Call)
            self.assertEqual(
                [token.value for token in Lexer("add with (2 plus 3) and 4").tokenize()],
                ["add", "with", "(", "2", "plus", "3", ")", "and", "4"],
            )
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "nested-calls.zelix"
                path.write_text(source, encoding="utf-8")
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    Interpreter().run_file(path)
            self.assertEqual(output.getvalue().splitlines(), ["9", "apples and oranges"])

    def test_optimizer_inlines_small_pure_function_calls(self):
            source = (
                "function square taking value\n"
                "    return value times value\n"
                "end function\n"
                "create result as square with 9\n"
            )
            optimized_ir = format_ir(optimize(parse_source(source)))
            self.assertIn("%result = create (mul 9, 9)", optimized_ir)
            self.assertNotIn("@square(", optimized_ir.split("module zelix", 1)[1].split("%result", 1)[-1])
            debug_ir = format_ir(optimize(parse_source(source), inline=False))
            self.assertIn("@square(", debug_ir)

    def test_operator_precedence_and_comparisons(self):
        self.assertEqual(ExpressionParser("2 plus 3 times 4", {}).parse(), 14)
        self.assertTrue(ExpressionParser("10 is greater than or equal to 10", {}).parse())
        self.assertTrue(ExpressionParser("true or false and false", {}).parse())

    def test_interpreter_nested_conditions_and_loops(self):
        source = (
            "create total as 0\n"
            "repeat with value from 1 to 3\n"
            "    if value is greater than 1\n"
            "        total becomes total plus value\n"
            "    otherwise\n"
            "        total becomes total plus 10\n"
            "    end if\n"
            "end loop\n"
            "display total\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.zelix"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(path)
        self.assertEqual(output.getvalue().strip(), "15")

    def test_interpreter_reports_unknown_variable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.zelix"
            path.write_text("display missing\n", encoding="utf-8")
            with self.assertRaisesRegex(ZelixError, "Unknown variable"):
                Interpreter().run_file(path)

    def test_ir_constant_folding(self):
        src = "create answer as 2 plus 3 times 4\ndisplay answer\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "test.zelix"
            p.write_text(src, encoding="utf-8")
            ir = emit_ir_file(p)
        self.assertIn("%answer = create 14", ir)
        self.assertIn("display 14", ir)

    def test_optimizer_propagates_constants_but_tracks_reassignment(self):
        source = (
            "create base as 20\n"
            "create answer as base plus 2\n"
            "base becomes 100\n"
            "display answer\n"
            "display base\n"
        )
        optimized_ir = format_ir(optimize(parse_source(source)))
        self.assertIn("%answer = create 22", optimized_ir)
        self.assertIn("%base = 100", optimized_ir)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "constants.zelix"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(path)
        self.assertEqual(output.getvalue().splitlines(), ["22", "100"])

    def test_source_validation(self):
        validate_source("create score as 10\nscore becomes score plus 1\n")
        with self.assertRaisesRegex(CompileError, "Line 1: Unknown variable"):
            validate_source("display missing\n")

    def test_static_types_and_generic_functions(self):
        source = (
            "function identity<T> taking value as T returning T\n"
            "    return value\n"
            "end function\n"
            "create answer as identity with 41\n"
            "display answer plus 1\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "generic.zelix"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(path)
        self.assertEqual(output.getvalue().strip(), "42")
        with self.assertRaisesRegex(CompileError, "expects number, got text"):
            validate_source("create score as number with text wrong end text\n")
        with self.assertRaisesRegex(CompileError, "expects number, got text"):
            validate_source(
                "function only_number taking value as number returning number\n"
                "    return value\n"
                "end function\n"
                "create mismatch as only_number with text no end text\n"
            )
        with self.assertRaisesRegex(CompileError, "list element expects number, got text"):
            validate_source(
                "create scores as list<number> with list with 1 and text wrong end text\n"
            )
        with self.assertRaisesRegex(CompileError, "Set elements must be hashable"):
            validate_source(
                "create nested as set<list<number>> with set with (list with 1)\n"
            )
        with self.assertRaisesRegex(CompileError, "must type parameter"):
            validate_source(
                "async function unsafe taking value returning void\n"
                "end function\n"
                "create task as spawn unsafe with 1\n"
            )

    def test_strict_type_mode_requires_explicit_types(self):
        validate_source(
            "function double taking value as number returning number\n"
            "    return value times 2\n"
            "end function\n"
            "create answer as double with 21\n",
            strict=True,
        )
        with self.assertRaisesRegex(CompileError, "Strict mode requires a type for parameter"):
            validate_source(
                "function identity taking value\n"
                "    return value\n"
                "end function\n",
                strict=True,
            )
    def test_owned_game_resources_are_typed_and_consumed(self):
        source = (
            "create sprite as load_texture with text sprite.png end text\n"
            "call draw_sprite with sprite and 10 and 20\n"
            "call unload_texture with sprite\n"
        )
        validate_source(source)
        with self.assertRaisesRegex(CompileError, "was already released"):
            validate_source(
                source + "call texture_width with sprite\n"
            )
        with self.assertRaisesRegex(CompileError, "not released on this exit path"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "display 1\n"
            )
        with self.assertRaisesRegex(CompileError, "not released on this exit path"):
            validate_source(
                "function load_and_forget returning void\n"
                "    create sprite as load_texture with text sprite.png end text\n"
                "end function\n"
            )
        with self.assertRaisesRegex(CompileError, "not released on this exit path"):
            validate_source(
                "function maybe_exit taking should_exit as boolean returning number\n"
                "    create sprite as load_texture with text sprite.png end text\n"
                "    if should_exit\n"
                "        return 1\n"
                "    end if\n"
                "    call unload_texture with sprite\n"
                "    return 0\n"
                "end function\n"
            )
        with self.assertRaisesRegex(CompileError, "was already released"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "call close_window\n"
                "call texture_width with sprite\n"
            )
        with self.assertRaisesRegex(CompileError, "expects texture, got sound"):
            validate_source(
                "create effect as load_sound with text effect.wav end text\n"
                "call draw_sprite with effect and 10 and 20\n"
            )
        with self.assertRaisesRegex(CompileError, "expects texture, got sound"):
            validate_source(
                "create effect as load_sound with text effect.wav end text\n"
                "create animation as create_animation with effect and 32 and 32 and 4 and 8\n"
            )
        with self.assertRaisesRegex(CompileError, "cannot be copied by declaration"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "create second as sprite\n"
            )
        with self.assertRaisesRegex(CompileError, "must be bound directly"):
            validate_source(
                "call play_sound with load_sound with text effect.wav end text\n"
            )
        with self.assertRaisesRegex(CompileError, "cannot be stored in collections"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "create items as list<any> with empty_list with\n"
                "call append with items and sprite\n"
            )
        with self.assertRaisesRegex(CompileError, "cannot be stored in collections"):
            validate_source(
                "create items as list<texture> with empty_list with\n"
            )
        with self.assertRaisesRegex(CompileError, "cannot be stored in channels"):
            validate_source(
                "create messages as channel<texture> with channel with 1\n"
            )
        with self.assertRaisesRegex(CompileError, "untyped or generic parameters"):
            validate_source(
                "function identity taking item\n"
                "    return item\n"
                "end function\n"
                "create sprite as load_texture with text sprite.png end text\n"
                "create second as identity with sprite\n"
            )
        validate_source(
            "function draw_image taking item as texture returning void\n"
            "    call draw_sprite with item and 10 and 20\n"
            "end function\n"
            "create sprite as load_texture with text sprite.png end text\n"
            "call draw_image with sprite\n"
            "call unload_texture with sprite\n"
        )
        with self.assertRaisesRegex(CompileError, "must be passed as a typed parameter"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "function draw_global returning void\n"
                "    call draw_sprite with sprite and 10 and 20\n"
                "end function\n"
                "call unload_texture with sprite\n"
            )
        with self.assertRaisesRegex(CompileError, "same ownership state in both branches"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "create should_release as true\n"
                "if should_release\n"
                "    call unload_texture with sprite\n"
                "otherwise\n"
                "    display false\n"
                "end if\n"
            )
        validate_source(
            "create sprite as load_texture with text sprite.png end text\n"
            "if true\n"
            "    call unload_texture with sprite\n"
            "otherwise\n"
            "    display false\n"
            "end if\n"
        )
        with self.assertRaisesRegex(CompileError, "ownership cannot change inside a loop"):
            validate_source(
                "create sprite as load_texture with text sprite.png end text\n"
                "create should_release as true\n"
                "while should_release\n"
                "    call unload_texture with sprite\n"
                "end loop\n"
            )
            with self.assertRaisesRegex(CompileError, "was already released"):
                validate_source(
                    "create effect as load_sound with text effect.wav end text\n"
                    "call close_audio\n"
                    "call play_sound with effect\n"
                )
            native_audio_shutdown = CGenerator(parse_source(
                "create effect as load_sound with text effect.wav end text\n"
                "call unload_sound with effect\n"
            )).generate()
            self.assertIn('if (!z_sound_loaded[handle]) z_fail(line, "Sound handle is not loaded");', native_audio_shutdown)
        validate_source(
            "create sprite as load_texture with text sprite.png end text\n"
            "while false\n"
            "    call unload_texture with sprite\n"
            "end loop\n"
            "call unload_texture with sprite\n"
        )

    def test_typed_numeric_codegen_uses_unboxed_arithmetic(self):
        module = parse_source(
            "function add taking left as number and right as number returning number\n"
            "    return left plus right\n"
            "end function\n"
            "create answer as add with 20 and 22\n"
        )
        generated = CGenerator(module).generate()
        self.assertIn(
            "z_num((z_get(v_left, init_v_left, 2).number + "
            "z_get(v_right, init_v_right, 2).number))",
            generated,
        )
        self.assertNotIn("z_binary(Z_ADD", generated)

    def test_assert_builtin_and_local_project_commands(self):
        from zelix import main

        generated = CGenerator(parse_source("call assert with true\n")).generate()
        self.assertIn("z_assert(z_bool(1), 1)", generated)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "app"
            manifest, entry = init_project(root)
            entry.write_text("display text Application ran end text\n", encoding="utf-8")
            test_root = root / "tests"
            test_root.mkdir()
            (test_root / "basic.zelix").write_text(
                "call assert with 20 plus 22 is 42\n", encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["check", str(root), "--strict"]), 0)
                self.assertEqual(main(["run", str(root)]), 0)
                self.assertEqual(main(["test", str(root)]), 0)
            self.assertIn("Checked 2 Zelix source file(s)", output.getvalue())
            self.assertIn("Application ran", output.getvalue())
            self.assertIn("test tests/basic.zelix ... ok", output.getvalue())
            with patch("zelix.compile_file", return_value=(root / "target" / "app", "")) as build:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["build", str(root)]), 0)
            self.assertEqual(build.call_args.args[0], entry)
            suffix = ".exe" if sys.platform == "win32" else ""
            self.assertEqual(
                build.call_args.args[1], root / "target" / f"app{suffix}",
            )
            self.assertTrue(manifest.is_file())

        with self.assertRaisesRegex(ZelixError, "Assertion failed"):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "failed.zelix"
                path.write_text("call assert with false\n", encoding="utf-8")
                Interpreter().run_file(path)

    def test_concurrency_and_collection_example(self):
        root = Path(__file__).resolve().parents[1]
        example = root / "examples" / "concurrency_and_collections.zelix"
        validate_file(example)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            Interpreter().run_file(example)
        self.assertEqual(
            output.getvalue().splitlines(),
            ["9", "First item ID:", "15", "2", "8", "health", "4", "5", "6", "42"],
        )

    def test_sets_of_string_arrays_in_interpreter(self):
        validate_source(STRING_ARRAY_SET_SOURCE)
        generated = CGenerator(parse_source(STRING_ARRAY_SET_SOURCE)).generate()
        self.assertIn(
            "if (!z_value_equal(a.collection->items[i], b.collection->items[i])) return 0;",
            generated,
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "string-array-set.zelix"
            source.write_text(STRING_ARRAY_SET_SOURCE, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(source)
        self.assertEqual(output.getvalue().splitlines(), ["1", "True", "2", "False"])

    @unittest.skipUnless(
        shutil.which("cc") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cl"),
        "native C compiler is not installed",
    )
    def test_native_sets_of_string_arrays(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "string-array-set.zelix"
            source.write_text(STRING_ARRAY_SET_SOURCE, encoding="utf-8")
            executable, _ = compile_file(source)
            result = subprocess.run(
                [str(executable)], capture_output=True, text=True, check=True, timeout=15,
            )
        self.assertEqual(result.stdout.splitlines(), ["1", "True", "2", "False"])

    def test_collection_bounds_are_checked_at_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bounds.zelix"
            source.write_text(
                "create items as list<number> with list with 1\n"
                "display get with items and 1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ZelixError, "out of range"):
                Interpreter().run_file(source)

    def test_native_concurrency_runtime_generation(self):
        source = (
            "async function pause returning void\n"
            "    await sleep with 0.001\n"
            "end function\n"
            "function double taking value as number returning number\n"
            "    return value times 2\n"
            "end function\n"
            "async function close_channel_task taking output as channel<number> returning void\n"
            "    call close_channel with output\n"
            "end function\n"
            "create messages as channel<number> with channel with 1\n"
            "create close_task as spawn close_channel_task with messages\n"
            "await close_task\n"
            "create task as spawn pause\n"
            "await task\n"
            "create worker as spawn_thread with double and 21\n"
            "display await worker\n"
        )
        validate_source(source)
        generated = CGenerator(parse_source(source)).generate()
        self.assertIn("AcquireSRWLockExclusive(&z_registry_lock)", generated)
        self.assertIn("InterlockedExchange(&z_runtime_failed, 1)", generated)
        self.assertIn("#include <pthread.h>", generated)
        self.assertIn("z_async_sleep", generated)
        self.assertIn("nanosleep", generated)
        self.assertIn("pthread_create", generated)
        self.assertIn("z_task_cleanup();", generated)
        self.assertIn("z_channel_close(z_get(v_output, init_v_output, 8), 8)", generated)

    @unittest.skipUnless(
        shutil.which("cc") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cl"),
        "native C compiler is not installed",
    )
    def test_native_concurrency_compile_and_run(self):
        root = Path(__file__).resolve().parents[1]
        example = (root / "examples" / "concurrency_and_collections.zelix").read_text(
            encoding="utf-8"
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "concurrency.zelix"
            source.write_text(example, encoding="utf-8")
            executable, _ = compile_file(source)
            try:
                result = subprocess.run(
                    [str(executable)], capture_output=True, text=True, check=True, timeout=15,
                )
            except subprocess.CalledProcessError as exc:
                self.fail(
                    f"Native concurrency example exited {exc.returncode}.\n"
                    f"stdout:\n{exc.stdout}\nstderr:\n{exc.stderr}"
                )
        self.assertEqual(
            result.stdout.splitlines(),
            ["9", "First item ID:", "15", "2", "8", "health", "4", "5", "6", "42"],
        )

    @unittest.skipUnless(
        shutil.which("cc") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cl"),
        "native C compiler is not installed",
    )
    def test_native_map_initialization_and_growth(self):
        source_text = (
            "create records as map<number, number> with map with "
            "1 and 10 and 2 and 20 and 3 and 30\n"
            "call put with records and 2 and 25\n"
            "call put with records and 4 and 40\n"
            "display length with records\n"
            "display get with records and 1\n"
            "display get with records and 2\n"
            "display get with records and 4\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "map.zelix"
            source.write_text(source_text, encoding="utf-8")
            executable, _ = compile_file(source)
            result = subprocess.run(
                [str(executable)], capture_output=True, text=True, check=True, timeout=15,
            )
        self.assertEqual(result.stdout.splitlines(), ["4", "10", "25", "40"])

    def test_raylib_game_api_codegen(self):
        source = (
            'call init_window with 640 and 480 and text Game end text\n'
            'while not window_should_close\n'
            '    call begin_drawing\n'
            '    call clear_background with text raywhite end text\n'
            '    call draw_rectangle with 10 and 20 and 30 and 40 and text orange end text\n'
            '    call end_drawing\n'
            'end loop\n'
            'call close_window\n'
        )
        generated = CGenerator(ZelixParser(source).parse()).generate()
        self.assertIn("atexit(z_game_shutdown);", generated)
        self.assertIn('#include "raylib.h"', generated)
        self.assertIn("InitWindow(", generated)
        self.assertIn("DrawRectangle(", generated)
        self.assertIn("WindowShouldClose()", generated)
        self.assertIn("z_game_shutdown();", generated)
        self.assertLess(
            generated.index("atexit(z_runtime_cleanup);"),
            generated.index("atexit(z_game_shutdown);"),
        )
        self.assertIn("z_socket_used[i] = false;", generated)

    def test_raylib_audio_codegen_uses_raylib_5_0_sound_fields(self):
        source = "call init_audio\n"
        generated = CGenerator(ZelixParser(source).parse()).generate()
        self.assertIn("sound.frameCount == 0", generated)
        self.assertNotIn("IsSoundValid(", generated)

    def test_game_sprite_animation_camera_and_input_codegen(self):
        source = (
            'call init_window with 640 and 360 and text Sprites end text\n'
            'call set_camera_2d with 0 and 0 and 320 and 180 and 1 and 0\n'
            'call enable_asset_hot_reload\n'
            'create texture as load_texture with text assets/player.png end text\n'
            'create animation as create_animation with texture and 32 and 32 and 4 and 8\n'
            'create machine as create_animation_machine\n'
            'call add_animation_state with machine and text idle end text and animation\n'
            'call add_animation_state with machine and text walk end text and animation\n'
            'call add_animation_transition with machine and text idle end text and text move end text and text walk end text\n'
            'while not window_should_close\n'
            '    if key_pressed with text right end text\n'
            '        call trigger_animation_event with machine and text move end text\n'
            '    end if\n'
            '    call update_animation_machine with machine and frame_time\n'
            '    call begin_drawing\n'
            '    call clear_background with text raywhite end text\n'
            '    call begin_camera_2d\n'
            '    call draw_animation_machine with machine and 0 and 0 and 2\n'
            '    call end_camera_2d\n'
            '    call end_drawing\n'
            'end loop\n'
            'call unload_texture with texture\n'
            'call close_window\n'
        )
        generated = CGenerator(parse_source(source)).generate()
        for expected in (
            "LoadTexture(", "DrawTexturePro(", "GetFileModTime(",
            "BeginMode2D(", "EndMode2D(", "IsKeyPressed(",
            "z_animation_machines", "Z_GAME_ADD_ANIMATION_TRANSITION",
            "Z_GAME_TRIGGER_ANIMATION_EVENT", "#define Z_ASSET_ROOT",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, generated)
        for function in GAME_FUNCTIONS:
            with self.subTest(game_function=function):
                self.assertIn(f"case Z_GAME_{function.upper()}", GAME_RUNTIME_C)

    def test_asset_validation_checks_files_formats_and_project_relative_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            (root / "assets" / "hero.png").write_bytes(b"placeholder image")
            source = root / "game.zelix"
            source.write_text(
                "create hero as load_texture with text assets/hero.png end text\n"
                "call unload_texture with hero\n",
                encoding="utf-8",
            )
            validate_file(source)
            source.write_text(
                "create hero as load_texture with text assets/missing.png end text\n"
                "call unload_texture with hero\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CompileError, "does not exist"):
                validate_file(source)
            source.write_text(
                "create hero as load_texture with text assets/hero.txt end text\n"
                "call unload_texture with hero\n",
                encoding="utf-8",
            )
            (root / "assets" / "hero.txt").write_text("not an image", encoding="utf-8")
            with self.assertRaisesRegex(CompileError, "Unsupported texture asset format"):
                validate_file(source)

    def test_game_api_argument_validation(self):
        with self.assertRaisesRegex(CompileError, "Game API init_window expects 3 arguments, got 2"):
            validate_source("call init_window with 640 and 480\n")

    def test_entity_component_physics_api(self):
        source = (
            "create player as create_entity\n"
            "create floor as create_entity\n"
            "call add_transform with player and 20 and 30\n"
            "call add_transform with floor and 0 and 100\n"
            "call add_rigidbody with player and 1\n"
            "call add_rigidbody with floor and 0\n"
            "call add_box_collider with player and 24 and 24 and 0.1 and 0.3\n"
            "call add_box_collider with floor and 400 and 20 and 0 and 0.8\n"
            "call entity_set_velocity with player and 10 and 0\n"
            "call entity_apply_force with player and 10 and 0\n"
            "create touching as entity_collides with player and floor\n"
            "create x as entity_x with player\n"
            "create y as entity_y with player\n"
            "create vx as entity_velocity_x with player\n"
            "create vy as entity_velocity_y with player\n"
            "call set_entity_position with player and x and y\n"
            "call physics_update with 0.016\n"
            "call destroy_entity with floor\n"
            "call destroy_entity with player\n"
        )
        validate_source(source)
        generated = CGenerator(parse_source(source)).generate()
        for api in (
            "CREATE_ENTITY", "DESTROY_ENTITY", "ADD_TRANSFORM", "ADD_RIGIDBODY",
            "ADD_BOX_COLLIDER", "ENTITY_SET_VELOCITY", "ENTITY_APPLY_FORCE",
            "ENTITY_COLLIDES", "ENTITY_X", "ENTITY_VELOCITY_Y",
        ):
            with self.subTest(api=api):
                self.assertIn(f"case Z_GAME_{api}", generated)
        self.assertIn("Z_GAME_MAX_ENTITIES 512", generated)
        self.assertIn("Z_GAME_MAX_OBJECTS; ++j", generated)
        self.assertIn("ceilf(delta * 120.0f)", generated)
        self.assertIn("z_game_resolve_aabb(", generated)
        self.assertIn("sqrtf(a_friction * b_friction)", generated)
        self.assertIn("generation != generation", generated)
        self.assertIn("Static rigidbodies cannot be moved", generated)

        with self.assertRaisesRegex(CompileError, "expects entity, got sound"):
            validate_source(
                "create effect as load_sound with text effect.wav end text\n"
                "call destroy_entity with effect\n"
                "call unload_sound with effect\n"
            )
        with self.assertRaisesRegex(CompileError, "expects 5 arguments, got 3"):
            validate_source(
                "create player as create_entity\n"
                "call add_transform with player and 0 and 0\n"
                "call add_box_collider with player and 10 and 10\n"
            )

    def test_3d_entity_physics_api(self):
        source = (
            "create crate as create_entity\n"
            "create floor as create_entity\n"
            "call add_transform_3d with crate and 0 and 3 and 0\n"
            "call add_transform_3d with floor and -5 and 0 and -5\n"
            "call add_rigidbody with crate and 2\n"
            "call add_rigidbody with floor and 0\n"
            "call add_box_collider_3d with crate and 1 and 1 and 1 and 0.2 and 0.4\n"
            "call add_box_collider_3d with floor and 10 and 1 and 10 and 0 and 0.8\n"
            "call physics_set_gravity_3d with 0 and -9.8 and 0\n"
            "call entity_set_velocity_3d with crate and 1 and 0 and 2\n"
            "call entity_apply_force_3d with crate and 0 and 4 and 0\n"
            "create z as entity_z with crate\n"
            "create vz as entity_velocity_z with crate\n"
            "create touching as entity_collides_3d with crate and floor\n"
            "call set_entity_position_3d with crate and 0 and 3 and z\n"
            "call physics_update with 0.016\n"
            "call destroy_entity with floor\n"
            "call destroy_entity with crate\n"
        )
        validate_source(source)
        generated = CGenerator(parse_source(source)).generate()
        for api in (
            "ADD_TRANSFORM_3D", "ENTITY_Z", "SET_ENTITY_POSITION_3D",
            "ENTITY_VELOCITY_Z", "ENTITY_SET_VELOCITY_3D",
            "ENTITY_APPLY_FORCE_3D", "ADD_BOX_COLLIDER_3D",
            "ENTITY_COLLIDES_3D", "PHYSICS_SET_GRAVITY_3D",
        ):
            with self.subTest(api=api):
                self.assertIn(f"case Z_GAME_{api}", generated)
        self.assertIn("ZBoxCollider3D", generated)
        self.assertIn("z_game_resolve_box_3d(", generated)
        self.assertIn("float overlap[3]", generated)
        self.assertIn("if (inverse_mass <= 0) return;", generated)

        with self.assertRaisesRegex(CompileError, "expects entity, got sound"):
            validate_source(
                "create effect as load_sound with text effect.wav end text\n"
                "call add_transform_3d with effect and 0 and 0 and 0\n"
                "call unload_sound with effect\n"
            )
        with self.assertRaisesRegex(CompileError, "expects 6 arguments, got 5"):
            validate_source(
                "create crate as create_entity\n"
                "call add_transform_3d with crate and 0 and 0 and 0\n"
                "call add_box_collider_3d with crate and 1 and 1 and 1 and 0\n"
            )

    def test_pathfinding_and_particle_apis(self):
        source = (
            "create grid as create_path_grid with 8 and 8 and 32\n"
            "call set_path_blocked with grid and 2 and 2 and true\n"
            "create route as find_path with grid and 0 and 0 and 7 and 7\n"
            "create route_size as path_length with route\n"
            "create cell_x as path_x with route and 0\n"
            "create cell_y as path_y with route and 0\n"
            "create actor as create_entity\n"
            "call add_transform with actor and 16 and 16\n"
            "create arrived as follow_path with route and actor and 80 and 0.016\n"
            "call destroy_path with route\n"
            "call destroy_path_grid with grid\n"
            "create sparks as create_particle_emitter with 128\n"
            "create emitted as emit_particles with sparks and 20 and 30 and 10 and 1 and 80 and text orange end text\n"
            "call set_particle_gravity with sparks and 100\n"
            "call update_particle_emitter with sparks and 0.016\n"
            "create count as particle_count with sparks\n"
            "call draw_particle_emitter with sparks\n"
            "call clear_particle_emitter with sparks\n"
            "call destroy_particle_emitter with sparks\n"
            "call destroy_entity with actor\n"
        )
        validate_source(source)
        generated = CGenerator(parse_source(source)).generate()
        for api in (
            "CREATE_PATH_GRID", "SET_PATH_BLOCKED", "FIND_PATH",
            "PATH_LENGTH", "PATH_X", "PATH_Y", "FOLLOW_PATH",
            "CREATE_PARTICLE_EMITTER", "EMIT_PARTICLES",
            "UPDATE_PARTICLE_EMITTER", "DRAW_PARTICLE_EMITTER",
            "PARTICLE_COUNT", "CLEAR_PARTICLE_EMITTER",
        ):
            with self.subTest(api=api):
                self.assertIn(f"case Z_GAME_{api}", generated)
        self.assertIn("Z_GAME_MAX_PATH_CELLS 4096", generated)
        self.assertIn("heuristic = (float)(abs(gx - x) + abs(gy - y))", generated)
        self.assertIn("Path coordinates are outside the grid", generated)
        self.assertIn("z_paths[i].active = false;", generated)
        self.assertIn("z_game_random(&emitter->random_state)", generated)
        self.assertIn("Particle capacity must be a whole number from 1 to 256", generated)

        with self.assertRaisesRegex(CompileError, "expects path_grid, got sound"):
            validate_source(
                "create effect as load_sound with text effect.wav end text\n"
                "call destroy_path_grid with effect\n"
                "call unload_sound with effect\n"
            )
        with self.assertRaisesRegex(CompileError, "expects 7 arguments, got 3"):
            validate_source(
                "create sparks as create_particle_emitter with 8\n"
                "call emit_particles with sparks and 0 and 0\n"
            )

    def test_game_ui_and_save_load_apis(self):
        source = (
            "call ui_panel with 12 and 12 and 280 and 180 and text Settings end text\n"
            "call ui_label with 24 and 48 and text Volume end text and 18 and text white end text\n"
            "create clicked as ui_button with 24 and 80 and 120 and 32 and text Save end text\n"
            "create enabled as ui_checkbox with 24 and 124 and text Enabled end text and true\n"
            "call ui_progress_bar with 24 and 160 and 200 and 12 and 3 and 5 and text lime end text\n"
            "call save_number with text profile.sav end text and text score end text and 42\n"
            "create score as load_number with text profile.sav end text and text score end text and 0\n"
            "call save_text with text profile.sav end text and text player end text and text Ada\\tLovelace end text\n"
            "create player as load_text with text profile.sav end text and text player end text and text Guest end text\n"
            "call save_boolean with text profile.sav end text and text audio end text and true\n"
            "create audio as load_boolean with text profile.sav end text and text audio end text and false\n"
        )
        validate_source(source)
        generated = CGenerator(parse_source(source)).generate()
        for api in (
            "UI_PANEL", "UI_LABEL", "UI_BUTTON", "UI_CHECKBOX", "UI_PROGRESS_BAR",
            "SAVE_NUMBER", "LOAD_NUMBER", "SAVE_TEXT", "LOAD_TEXT",
            "SAVE_BOOLEAN", "LOAD_BOOLEAN",
        ):
            with self.subTest(api=api):
                self.assertIn(f"case Z_GAME_{api}", generated)
        self.assertIn("CheckCollisionPointRec(GetMousePosition(), bounds)", generated)
        self.assertIn("z_game_encode_save_text", generated)
        self.assertIn("Text save value exceeds the maximum supported size", generated)
        self.assertIn("Malformed saved number", generated)
        self.assertIn("Saved value has a different type", generated)

        with self.assertRaisesRegex(CompileError, "expects boolean, got number"):
            validate_source(
                "call save_boolean with text profile.sav end text and "
                "text audio end text and 1\n"
            )
        with self.assertRaisesRegex(CompileError, "expects number, got text"):
            validate_source(
                "call ui_progress_bar with 0 and 0 and 100 and 12 and "
                "text full end text and 100 and text lime end text\n"
            )

    def test_modapi_read_only_item_and_recipe_queries(self):
        source = (
            "create items as modapi_items\n"
            "create first as get with items and 0\n"
            "display get with first and text registry_name end text\n"
            "create recipes as modapi_recipes_for with 4\n"
            "display length with recipes\n"
            "create recipe as get with recipes and 0\n"
            "create slots as get with recipe and text ingredients end text\n"
            "create alternatives as get with slots and 0\n"
            "display get with alternatives and 0\n"
            "create item_id as modapi_item_id with text minecraft:planks end text\n"
            "display item_id\n"
            "create all_recipes as modapi_recipes\n"
            "display length with all_recipes\n"
        )
        validate_source(source)
        requests = []
        fixture = {
            "items": [{
                "id": 1,
                "registry_name": "minecraft:stone",
                "unlocalized_name": "tile.stone",
            }],
            "recipes_for": [{
                "result_id": 4,
                "result_count": 1,
                "ingredients": [[1]],
            }],
            "item_id": 5,
            "recipes": [{
                "result_id": 4,
                "result_count": 1,
                "ingredients": [[1]],
            }],
        }
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(4)
            port = listener.getsockname()[1]

            def serve_queries():
                for _ in range(4):
                    client, _ = listener.accept()
                    with client:
                        request = client.makefile("rb").readline().decode("utf-8").rstrip("\n")
                        parts = request.split("\t")
                        requests.append(parts)
                        response = json.dumps(fixture[parts[1]]).encode("utf-8") + b"\n"
                        client.sendall(response)

            server = threading.Thread(target=serve_queries)
            server.start()
            with patch.dict(os.environ, {
                "ZELIX_MODAPI_PORT": str(port),
                "ZELIX_MODAPI_TOKEN": "fixture-token",
            }):
                output = io.StringIO()
                with tempfile.TemporaryDirectory() as directory:
                    script = Path(directory) / "query.zelix"
                    script.write_text(source, encoding="utf-8")
                    with contextlib.redirect_stdout(output):
                        Interpreter().run_file(script)
            server.join(timeout=3)
            self.assertFalse(server.is_alive())
        self.assertEqual(output.getvalue().splitlines(), [
            "minecraft:stone", "1", "1", "5", "1",
        ])
        self.assertEqual([request[:2] for request in requests], [
            ["fixture-token", "items"],
            ["fixture-token", "recipes_for"],
            ["fixture-token", "item_id"],
            ["fixture-token", "recipes"],
        ])
        generated = CGenerator(parse_source("create items as modapi_items\n")).generate()
        self.assertIn("modapi_items requires the Zelix Minecraft loader", generated)
        with self.assertRaisesRegex(CompileError, "modapi_recipes_for expects one item ID"):
            validate_source("create recipes as modapi_recipes_for with\n")
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "outside_loader.zelix"
            script.write_text("create items as modapi_items\n", encoding="utf-8")
            with patch.dict(os.environ, {
                "ZELIX_MODAPI_PORT": "",
                "ZELIX_MODAPI_TOKEN": "",
            }):
                with self.assertRaisesRegex(
                    ZelixError, "available only inside the Zelix Minecraft loader"
                ):
                    Interpreter().run_file(script)

    def test_modapi_jei_helpers_and_registration_actions(self):
        source = (
            "create item as getItemById with 5\n"
            "display get with item and text registry_name end text\n"
            "create item_id as getIdForItem with text minecraft:planks end text\n"
            "display item_id\n"
            "create recipes as getRecipesForId with 5\n"
            "display length with recipes\n"
            "create recipe as getRecipe with 5 and 0\n"
            "display get with recipe and text result_count end text\n"
            "create new_item as modapi_register_item with text copper_ingot end text and 64\n"
            "display new_item\n"
            "create new_block as modapi_register_block with text copper_ore end text and "
            "text rock end text and 3\n"
            "display new_block\n"
            "create gui_opened as modapi_recipe_gui\n"
            "display gui_opened\n"
        )
        validate_source(source)
        requests = []
        fixture = {
            "item_by_id": {
                "id": 5,
                "registry_name": "minecraft:planks",
                "unlocalized_name": "tile.wood",
            },
            "item_id": 5,
            "recipes_for": [{
                "result_id": 5,
                "result_count": 4,
                "ingredients": [[1]],
            }],
            "recipe": {
                "result_id": 5,
                "result_count": 4,
                "ingredients": [[1]],
            },
            "register_item": 101,
            "register_block": 102,
            "recipe_gui": 1,
        }
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(8)
            port = listener.getsockname()[1]

            def serve_actions():
                for _ in range(7):
                    client, _ = listener.accept()
                    with client:
                        parts = client.makefile("rb").readline().decode("utf-8").rstrip("\n").split("\t")
                        requests.append(parts)
                        client.sendall(json.dumps(fixture[parts[1]]).encode("utf-8") + b"\n")

            server = threading.Thread(target=serve_actions)
            server.start()
            with patch.dict(os.environ, {
                "ZELIX_MODAPI_PORT": str(port),
                "ZELIX_MODAPI_TOKEN": "fixture-token",
                "ZELIX_MODAPI_MOD_ID": "demo_mod",
            }):
                output = io.StringIO()
                with tempfile.TemporaryDirectory() as directory:
                    script = Path(directory) / "jei_helpers.zelix"
                    script.write_text(source, encoding="utf-8")
                    with contextlib.redirect_stdout(output):
                        Interpreter().run_file(script)
            server.join(timeout=3)
            self.assertFalse(server.is_alive())
        self.assertEqual(output.getvalue().splitlines(), [
            "minecraft:planks", "5", "1", "4", "101", "102", "1",
        ])
        self.assertEqual([request[:2] for request in requests], [
            ["fixture-token", "item_by_id"],
            ["fixture-token", "item_id"],
            ["fixture-token", "recipes_for"],
            ["fixture-token", "recipe"],
            ["fixture-token", "register_item"],
            ["fixture-token", "register_block"],
            ["fixture-token", "recipe_gui"],
        ])
        self.assertEqual(requests[4][2:], ["demo_mod", "copper_ingot", "64"])
        self.assertEqual(requests[5][2:], ["demo_mod", "copper_ore", "rock", "3"])

    def test_combat_api_types_and_native_runtime(self):
        source = (
            "create hero as create_combatant with 100 and 5\n"
            "call apply_damage with hero and 20\n"
            "call heal_combatant with hero and 10\n"
            "create max_health as combatant_max_health with hero\n"
            "create armor as combatant_armor with hero\n"
            "call set_combatant_armor with hero and armor\n"
            "call apply_status_effect with hero and text poison end text and 3 and 2\n"
            "call update_status_effects with hero and 0.5\n"
            "create alive as is_combatant_alive with hero\n"
            "create poisoned as has_status_effect with hero and text poison end text\n"
            "create remaining as status_effect_remaining with hero and text poison end text\n"
            "create removed as remove_status_effect with hero and text poison end text\n"
            "call clear_status_effects with hero\n"
            "call destroy_combatant with hero\n"
        )
        validate_source(source)
        generated = CGenerator(parse_source(source)).generate()
        for api in (
            "CREATE_COMBATANT", "APPLY_DAMAGE", "HEAL_COMBATANT",
            "APPLY_STATUS_EFFECT", "UPDATE_STATUS_EFFECTS",
            "IS_COMBATANT_ALIVE", "CLEAR_STATUS_EFFECTS", "DESTROY_COMBATANT",
        ):
            with self.subTest(api=api):
                self.assertIn(f"case Z_GAME_{api}", generated)
        self.assertIn("Damage must be finite and non-negative", generated)
        self.assertIn("Armor must be finite and non-negative", generated)
        self.assertIn("Status-effect delta must be finite and non-negative", generated)
        self.assertIn('TextIsEqual(effect->name, "regeneration")', generated)
        self.assertIn('TextIsEqual(effect->name, "poison")', generated)
        self.assertIn("z_combatants[handle].generation != generation", generated)
        self.assertIn("Maximum number of status effects reached", generated)

        with self.assertRaisesRegex(CompileError, "expects combatant, got sound"):
            validate_source(
                "create effect as load_sound with text effect.wav end text\n"
                "create health as combatant_health with effect\n"
                "call unload_sound with effect\n"
            )
        with self.assertRaisesRegex(CompileError, "expects 4 arguments, got 3"):
            validate_source(
                "create hero as create_combatant with 100 and 0\n"
                "call apply_status_effect with hero and text poison end text and 3\n"
                "call destroy_combatant with hero\n"
            )

    def test_voxel_world_example_and_face_api(self):
        example = Path(__file__).resolve().parents[1] / "examples" / "voxel_world.zelix"
        validate_file(example)
        source = example.read_text(encoding="utf-8")
        self.assertIn("call draw_voxel_world with blocks", source)
        self.assertIn("function terrain_height", source)
        self.assertIn("world_seed as 37", source)
        self.assertIn("call set_voxel_render_distance with render_distance", source)
        self.assertIn("call set_camera_3d with camera_x", source)
        self.assertNotIn("call draw_voxel_face with", source)

        generated = CGenerator(parse_source(
            "call draw_voxel_face with 0 and 0 and 0 and 1 and text top end text "
            "and text green end text\n"
        )).generate()
        self.assertIn("case Z_GAME_DRAW_VOXEL_FACE", generated)
        self.assertEqual(GAME_FUNCTIONS["draw_voxel_face"], 6)
        self.assertIn("DrawTriangle3D(a, b, c, color);", generated)
        self.assertIn("DrawTriangle3D(a, c, d, color);", generated)
        with self.assertRaisesRegex(
            CompileError, "Game API draw_voxel_face expects 6 arguments, got 5"
        ):
            validate_source(
                "call draw_voxel_face with 0 and 0 and 0 and 1 and text top end text\n"
            )

        world_source = (
            "create blocks as list<number> with list with 1\n"
            "call draw_voxel_world with blocks and 1 and 1 and 1 and "
            "text green end text and text brown end text and text gray end text "
            "and text blue end text\n"
        )
        validate_source(world_source)
        world_generated = CGenerator(parse_source(world_source)).generate()
        self.assertIn("case Z_GAME_DRAW_VOXEL_WORLD", world_generated)
        self.assertEqual(GAME_FUNCTIONS["draw_voxel_world"], 8)
        self.assertIn("rlBegin(RL_TRIANGLES);", world_generated)
        self.assertIn("rlEnd();", world_generated)
        self.assertIn("z_game_voxel_face(world_x, world_y, world_z, 0.5f, face);", world_generated)
        self.assertEqual(world_generated.count("rlBegin(RL_TRIANGLES);"), 1)
        with self.assertRaisesRegex(
            CompileError, "Game API draw_voxel_world expects 8 arguments, got 4"
        ):
            validate_source("call draw_voxel_world with blocks and 8 and 4 and 8\n")

        camera_source = (
            "call set_camera_3d with 0 and 8 and 12 and 0 and 0 and 0\n"
            "call set_voxel_render_distance with 48\n"
            "create distance as distance_3d with 0 and 8 and 12 and 0 and 0 and 0\n"
        )
        validate_source(camera_source)
        camera_generated = CGenerator(parse_source(camera_source)).generate()
        for api in ("SET_CAMERA_3D", "SET_VOXEL_RENDER_DISTANCE", "DISTANCE_3D"):
            with self.subTest(api=api):
                self.assertIn(f"case Z_GAME_{api}", camera_generated)
        self.assertIn("z_camera_3d_initialized = true;", camera_generated)
        self.assertIn("dx * dx + dy * dy + dz * dz > render_distance_squared", camera_generated)
        self.assertIn("sqrt(dx * dx + dy * dy + dz * dz)", camera_generated)
        self.assertEqual(GAME_FUNCTIONS["set_camera_3d"], 6)
        self.assertEqual(GAME_FUNCTIONS["set_voxel_render_distance"], 1)
        self.assertEqual(GAME_FUNCTIONS["distance_3d"], 6)
        with self.assertRaisesRegex(CompileError, "expects 6 arguments, got 3"):
            validate_source("call set_camera_3d with 0 and 0 and 0\n")

    def test_raylib_build_adds_headers_and_platform_libraries(self):
        source_text = "call init_window with 640 and 480 and text Game end text\n"
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "game.zelix"
            source.write_text(source_text, encoding="utf-8")
            with patch("compiler.platform.system", return_value="Linux"), \
                    patch("compiler.shutil.which", return_value="cc"), \
                    patch.dict("os.environ", {
                        "RAYLIB_INCLUDE_DIR": "C:/raylib/include",
                        "RAYLIB_LIB_DIR": "C:/raylib/lib",
                    }), \
                    patch("compiler.subprocess.run", return_value=SimpleNamespace(
                        returncode=0, stderr="", stdout=""
                    )) as run:
                executable, _ = compile_file(source, debug=True)
            command = run.call_args.args[0]
            self.assertIn("C:/raylib/include", command)
            self.assertIn("C:/raylib/lib", command)
            self.assertIn("-lraylib", command)
            self.assertIn("-lX11", command)
            generated = executable.with_name(executable.name + ".zelix.c")
            self.assertIn('#include "raylib.h"', generated.read_text(encoding="utf-8"))

    def test_raylib_msvc_build_links_platform_libraries(self):
        source_text = "call init_window with 640 and 480 and text Game end text\n"
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "game.zelix"
            source.write_text(source_text, encoding="utf-8")
            with patch("compiler.platform.system", return_value="Windows"), \
                    patch("compiler.shutil.which", return_value="cl.exe"), \
                    patch.dict("os.environ", {
                        "RAYLIB_INCLUDE_DIR": "C:/raylib/include",
                        "RAYLIB_LIB_DIR": "C:/raylib/lib",
                    }), \
                    patch("compiler.subprocess.run", return_value=SimpleNamespace(
                        returncode=0, stderr="", stdout=""
                    )) as run:
                executable, _ = compile_file(source, debug=True)
            command = run.call_args.args[0]
            self.assertIn("/Zi", command)
            self.assertIn("/Od", command)
            self.assertIn("/DEBUG", command)
            self.assertIn("/IC:/raylib/include", command)
            self.assertIn("/LIBPATH:C:/raylib/lib", command)
            self.assertIn("raylib.lib", command)
            self.assertIn("ws2_32.lib", command)
            self.assertTrue(executable.with_name(executable.name + ".zelix.c").is_file())

    def test_game_examples_validate(self):
        root = Path(__file__).resolve().parents[1]
        for example in (
            "hello.zelix", "basics.zelix", "functions.zelix", "loops.zelix",
            "input.zelix", "game_2d.zelix", "game_3d.zelix", "game_multiplayer.zelix",
            "game_sprites.zelix", "game_combat.zelix", "game_ecs_physics.zelix",
            "game_3d_physics.zelix",
            "game_ai_particles.zelix",
        ):
            with self.subTest(example=example):
                validate_source((root / "examples" / example).read_text(encoding="utf-8"))
        with self.subTest(example="project-packages"):
            entry = root / "examples" / "project-packages" / "src" / "main.zelix"
            validate_file(entry)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(entry)
            self.assertEqual(
                output.getvalue().splitlines(),
                ["Five-round score:", "150", "You reached the target!"],
            )

    def test_extension_manifest_exposes_project_workflow(self):
        root = Path(__file__).resolve().parents[1]
        extension = root / "vscode-zelix"
        manifest = json.loads((extension / "package.json").read_text(encoding="utf-8"))
        commands = {
            entry["command"]: entry["title"]
            for entry in manifest["contributes"]["commands"]
        }
        self.assertIn("zelix.initProject", commands)
        self.assertIn("zelix.installPackages", commands)
        self.assertIn("zelix.command", manifest["contributes"]["configuration"]["properties"])
        self.assertTrue((extension / "README.md").is_file())
        self.assertTrue((extension / "CHANGELOG.md").is_file())
        self.assertTrue((extension / "LICENSE").is_file())

    def test_local_path_package_import_runs_in_interpreter_and_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            app = workspace / "app"
            library = workspace / "math-tools"
            (app / "src").mkdir(parents=True)
            (library / "src").mkdir(parents=True)
            (app / "zelix.toml").write_text(
                '[package]\nname = "app"\nversion = "0.1.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nmath-tools = { path = "../math-tools" }\n',
                encoding="utf-8",
            )
            (library / "zelix.toml").write_text(
                '[package]\nname = "math-tools"\nversion = "1.2.3"\nentry = "src/main.zelix"\n',
                encoding="utf-8",
            )
            entry = app / "src" / "main.zelix"
            entry.write_text(
                "use math-tools\ncreate answer as double with 21\ndisplay answer\n",
                encoding="utf-8",
            )
            (library / "src" / "main.zelix").write_text(
                "function double taking value\n    return value times 2\nend function\n",
                encoding="utf-8",
            )

            lockfile = install_project(app)
            lock_data = json.loads(lockfile.read_text(encoding="utf-8"))
            self.assertEqual(lock_data["dependencies"]["math-tools"]["version"], "1.2.3")
            validate_file(entry)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                Interpreter().run_file(entry)
            self.assertEqual(output.getvalue().strip(), "42")

    def test_local_package_import_requires_a_current_lockfile(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            project = workspace / "app"
            (project / "src").mkdir(parents=True)
            (project / "zelix.toml").write_text(
                '[package]\nname = "app"\nversion = "0.1.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nhelper = { path = "../helper" }\n',
                encoding="utf-8",
            )
            helper = workspace / "helper"
            (helper / "src").mkdir(parents=True)
            (helper / "zelix.toml").write_text(
                '[package]\nname = "helper"\nversion = "1.0.0"\nentry = "src/main.zelix"\n',
                encoding="utf-8",
            )
            (helper / "src" / "main.zelix").write_text(
                "function help\n    return 1\nend function\n",
                encoding="utf-8",
            )
            (project / "src" / "main.zelix").write_text("use helper\n", encoding="utf-8")
            with self.assertRaisesRegex(ZelixError, "run 'zelix install"):
                Interpreter().run_file(project / "src" / "main.zelix")

    def test_local_package_lock_normalizes_source_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            app = workspace / "app"
            library = workspace / "helper"
            (app / "src").mkdir(parents=True)
            (library / "src").mkdir(parents=True)
            (app / "zelix.toml").write_text(
                '[package]\nname = "app"\nversion = "0.1.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nhelper = { path = "../helper" }\n',
                encoding="utf-8",
            )
            library_manifest = library / "zelix.toml"
            library_manifest.write_bytes(
                b'[package]\nname = "helper"\nversion = "1.0.0"\nentry = "src/main.zelix"\n'
            )
            entry = app / "src" / "main.zelix"
            entry.write_text("use helper\n", encoding="utf-8")
            library_entry = library / "src" / "main.zelix"
            library_entry.write_bytes(
                b"function help\n    return 1\nend function\n"
            )
            install_project(app)

            library_manifest.write_bytes(
                library_manifest.read_bytes().replace(b"\n", b"\r\n")
            )
            library_entry.write_bytes(
                library_entry.read_bytes().replace(b"\n", b"\r\n")
            )
            validate_file(entry)

    def test_local_package_lock_detects_dependency_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            app = workspace / "app"
            library = workspace / "helper"
            (app / "src").mkdir(parents=True)
            (library / "src").mkdir(parents=True)
            (app / "zelix.toml").write_text(
                '[package]\nname = "app"\nversion = "0.1.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nhelper = { path = "../helper" }\n',
                encoding="utf-8",
            )
            (library / "zelix.toml").write_text(
                '[package]\nname = "helper"\nversion = "1.0.0"\nentry = "src/main.zelix"\n',
                encoding="utf-8",
            )
            entry = app / "src" / "main.zelix"
            entry.write_text("use helper\n", encoding="utf-8")
            library_entry = library / "src" / "main.zelix"
            library_entry.write_text(
                "function help\n    return 1\nend function\n",
                encoding="utf-8",
            )
            install_project(app)
            library_entry.write_text(
                "function help\n    return 2\nend function\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ZelixError, "zelix.lock is out of date"):
                Interpreter().run_file(entry)

    def test_local_package_cycles_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            for package in (first, second):
                (package / "src").mkdir(parents=True)
                (package / "src" / "main.zelix").write_text(
                    "function helper\n    return 1\nend function\n",
                    encoding="utf-8",
                )
            (first / "zelix.toml").write_text(
                '[package]\nname = "first"\nversion = "1.0.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nsecond = { path = "../second" }\n',
                encoding="utf-8",
            )
            (second / "zelix.toml").write_text(
                '[package]\nname = "second"\nversion = "1.0.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nfirst = { path = "../first" }\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ProjectError, "dependency cycle"):
                install_project(first)

    def test_local_package_import_rejects_executable_library_code(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            app = workspace / "app"
            library = workspace / "helper"
            (app / "src").mkdir(parents=True)
            (library / "src").mkdir(parents=True)
            (app / "zelix.toml").write_text(
                '[package]\nname = "app"\nversion = "0.1.0"\nentry = "src/main.zelix"\n\n'
                '[dependencies]\nhelper = { path = "../helper" }\n',
                encoding="utf-8",
            )
            (library / "zelix.toml").write_text(
                '[package]\nname = "helper"\nversion = "1.0.0"\nentry = "src/main.zelix"\n',
                encoding="utf-8",
            )
            entry = app / "src" / "main.zelix"
            entry.write_text("use helper\n", encoding="utf-8")
            (library / "src" / "main.zelix").write_text(
                "function helper_function\n    return 1\nend function\n"
                "display text this is not library code end text\n",
                encoding="utf-8",
            )
            install_project(app)
            with self.assertRaisesRegex(ZelixError, "function definitions only"):
                Interpreter().run_file(entry)

    def test_init_creates_project_scaffold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "new-project"
            manifest, entry = init_project(root)
            self.assertTrue(manifest.is_file())
            self.assertTrue(entry.is_file())
            with contextlib.redirect_stdout(io.StringIO()):
                Interpreter().run_file(root)

    def test_cli_version_and_package_commands(self):
        from zelix import main

        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["--version"]), 0)
        self.assertIn("Zelix 0.4.0", output.getvalue())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["init", str(root)]), 0)
                self.assertEqual(main(["install", str(root)]), 0)
            self.assertTrue((root / "zelix.lock").is_file())

    def test_debug_build_keeps_generated_source(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "test.zelix"
            source.write_text("display text debug\n", encoding="utf-8")
            with patch("compiler.platform.system", return_value="Linux"), \
                    patch("compiler.shutil.which", return_value="cc"), \
                    patch("compiler.subprocess.run", return_value=SimpleNamespace(
                        returncode=0, stderr="", stdout=""
                    )) as run:
                executable, _ = compile_file(source, debug=True)
            generated = executable.with_name(executable.name + ".zelix.c")
            self.assertTrue(generated.is_file())
            command = run.call_args.args[0]
            self.assertIn("-g", command)
            self.assertIn("-O0", command)
            self.assertIn(str(generated), command)

    def test_debugger_entry_step_stack_and_breakpoint(self):
        class EventStream:
            def __init__(self):
                self.events = queue.Queue()

            def write(self, message):
                self.events.put(json.loads(message))

            def flush(self):
                pass

        output = EventStream()
        controller = DebugController(
            Path("debug-test.zelix"),
            input_stream=io.StringIO(),
            output_stream=output,
        )
        main_env = {"answer": 1}
        controller.push_frame("main", main_env, 1)

        def statement(line, env, errors):
            try:
                controller.before_statement(line, env)
            except DebuggerStopped as exc:
                errors.put(exc)

        errors = queue.Queue()
        first = threading.Thread(target=statement, args=(1, main_env, errors))
        first.start()
        entry = output.events.get(timeout=2)
        self.assertEqual(entry["reason"], "entry")
        self.assertEqual(entry["stack"][0]["locals"]["answer"], 1)
        controller.commands.put({
            "command": "resume", "mode": "stepIn", "line": 1, "depth": 0,
        })
        first.join(timeout=2)
        self.assertFalse(first.is_alive())

        function_env = {"value": 42}
        controller.push_frame("calculate", function_env, 4)
        second = threading.Thread(target=statement, args=(4, function_env, errors))
        second.start()
        stepped = output.events.get(timeout=2)
        self.assertEqual(stepped["reason"], "step")
        self.assertEqual([frame["name"] for frame in stepped["stack"]], ["calculate", "main"])
        self.assertEqual(stepped["stack"][0]["locals"]["value"], 42)
        controller.commands.put({"command": "resume", "mode": "continue", "line": 4, "depth": 1})
        second.join(timeout=2)
        self.assertFalse(second.is_alive())

        controller.commands.put({"command": "breakpoints", "lines": [8]})
        third = threading.Thread(target=statement, args=(8, function_env, errors))
        third.start()
        breakpoint = output.events.get(timeout=2)
        self.assertEqual(breakpoint["reason"], "breakpoint")
        controller.commands.put({"command": "terminate"})
        third.join(timeout=2)
        self.assertFalse(third.is_alive())
        self.assertIsInstance(errors.get_nowait(), DebuggerStopped)

    def test_debug_server_runs_program_and_streams_debug_output(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "step.zelix"
            source.write_text(
                "function total taking amount\n"
                "    create result as amount plus 2\n"
                "    return result\n"
                "end function\n"
                "create answer as total with 40\n"
                "display answer\n",
                encoding="utf-8",
            )
            process = subprocess.Popen(
                [sys.executable, str(root / "zelix.py"), "--debug-server", str(source)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            events = queue.Queue()

            def read_events():
                for line in process.stdout:
                    events.put(json.loads(line))

            reader = threading.Thread(target=read_events, daemon=True)
            reader.start()
            try:
                process.stdin.write(
                    '{"command":"breakpoints","lines":[]}\n'
                    '{"command":"configure"}\n'
                )
                process.stdin.flush()
                entry = events.get(timeout=5)
                self.assertEqual(entry["event"], "stopped")
                self.assertEqual(entry["reason"], "entry")
                self.assertEqual(entry["line"], 5)
                process.stdin.write('{"command":"resume","mode":"stepIn","line":5,"depth":0}\n')
                process.stdin.flush()
                step = events.get(timeout=5)
                self.assertEqual(step["event"], "stopped")
                self.assertEqual(step["line"], 2)
                self.assertEqual(step["stack"][0]["name"], "total")
                self.assertEqual(step["stack"][0]["locals"]["amount"], 40)
                process.stdin.write('{"command":"resume","mode":"continue","line":2,"depth":1}\n')
                process.stdin.flush()
                received = []
                while True:
                    event = events.get(timeout=5)
                    received.append(event)
                    if event["event"] == "terminated":
                        break
                output = "".join(
                    event.get("output", "")
                    for event in received if event["event"] == "output"
                )
                self.assertEqual(output, "42\n")
                self.assertEqual(process.wait(timeout=5), 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdin:
                    process.stdin.close()
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()

    def test_debug_server_can_skip_entry_and_stop_at_breakpoint(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "breakpoint.zelix"
            source.write_text(
                "create answer as 42\n"
                "display answer\n",
                encoding="utf-8",
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(root / "zelix.py"),
                    "--debug-server",
                    str(source),
                    "--debug-no-stop-on-entry",
                ],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            events = queue.Queue()

            def read_events():
                for line in process.stdout:
                    events.put(json.loads(line))

            reader = threading.Thread(target=read_events, daemon=True)
            reader.start()
            try:
                process.stdin.write(
                    '{"command":"breakpoints","lines":[2]}\n'
                    '{"command":"configure"}\n'
                    '{"command":"resume","mode":"continue","line":0,"depth":0}\n'
                )
                process.stdin.flush()
                stopped = events.get(timeout=5)
                self.assertEqual(stopped["event"], "stopped")
                self.assertEqual(stopped["reason"], "breakpoint")
                self.assertEqual(stopped["line"], 2)
                process.stdin.write('{"command":"terminate"}\n')
                process.stdin.flush()
                terminated = events.get(timeout=5)
                self.assertEqual(terminated["event"], "terminated")
                self.assertEqual(process.wait(timeout=5), 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdin:
                    process.stdin.close()
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()

    def test_interactive_input_is_rejected_during_debugging(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.zelix"
            source.write_text("create answer as input number\n", encoding="utf-8")
            class NoOpDebugger:
                def before_statement(self, line, env):
                    pass

                def push_frame(self, name, env, line):
                    pass

                def pop_frame(self):
                    pass

                def capture_exception(self):
                    pass

            with self.assertRaisesRegex(ZelixError, "not supported while debugging"):
                Interpreter(debugger=NoOpDebugger()).run_file(source)

    def test_debug_server_is_in_python_package_and_marketplace_manifest(self):
        root = Path(__file__).resolve().parents[1]
        package = (root / "pyproject.toml").read_text(encoding="utf-8")
        manifest = json.loads((root / "vscode-zelix" / "package.json").read_text(encoding="utf-8"))
        contributes = manifest["contributes"]
        self.assertIn('"debug_server"', package)
        self.assertEqual(manifest["version"], "0.5.0")
        self.assertEqual(manifest["icon"], "images/zelix-icon.png")
        self.assertEqual(contributes["debuggers"][0]["type"], "zelix")
        self.assertIn("zelix.debugCurrentFile", {
            command["command"] for command in contributes["commands"]
        })
        extension_source = (root / "vscode-zelix" / "extension.js").read_text(encoding="utf-8")
        for feature in (
            "draw_sprite", "create_animation", "set_camera_2d", "mouse_world_x",
            "create_combatant", "apply_status_effect", "create_entity",
            "add_box_collider", "entity_collides", "add_transform_3d",
            "add_box_collider_3d", "physics_set_gravity_3d",
            "entity_set_velocity_3d",
            "create_path_grid", "find_path", "emit_particles",
            "update_particle_emitter",
        ):
            self.assertIn(f'"{feature}"', extension_source)
        self.assertIn('"draw_voxel_world"', extension_source)
        self.assertIn('"string"', extension_source)
        grammar = (root / "vscode-zelix" / "syntaxes" / "zelix.tmLanguage.json").read_text(encoding="utf-8")
        self.assertIn("|text|string|", grammar)
        for feature in ("sleep", "spawn_thread", "COLLECTION_FUNCTIONS"):
            self.assertIn(feature, extension_source)
        for feature in (
            "modapi_items", "modapi_recipes", "modapi_recipes_for", "modapi_item_id",
            "getitembyid", "getidforitem", "getrecipe", "getrecipesforid",
            "modapi_register_item", "modapi_register_block", "modapi_recipe_gui",
        ):
            self.assertIn(feature, extension_source)
        extension_snippets = (root / "vscode-zelix" / "snippets" / "zelix.json").read_text(encoding="utf-8")
        self.assertIn('"Zelix async channel producer"', extension_snippets)
        self.assertIn('"Zelix set of string arrays"', extension_snippets)
        self.assertIn('"Zelix batched voxel world"', extension_snippets)
        self.assertIn('"Zelix combatant and status effects"', extension_snippets)
        self.assertIn('"Zelix ECS physics entities"', extension_snippets)
        self.assertIn('"Zelix 3D ECS physics entities"', extension_snippets)
        self.assertIn('"Zelix enemy pathfinding and particles"', extension_snippets)

    def test_benchmark_harness_smoke(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable, str(root / "benchmarks" / "run.py"),
                "--iterations", "3", "--repeats", "1", "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["iterations"], 3)
        self.assertIn("Python", report["median_process_seconds"])
        self.assertIn("Zelix interpreter", report["median_process_seconds"])
        self.assertIn("toolchains", report)
        self.assertIn("zelix_version", report)

    @unittest.skipUnless(shutil.which("cc") or shutil.which("gcc") or shutil.which("clang") or
                         shutil.which("cl"), "native C compiler is not installed")
    def test_native_compile_and_run(self):
        src = (
            "function add taking first and second\n"
            "    return first plus second\n"
            "end function\n"
            "create answer as add with 10 and 20\n"
            "display answer\n"
        )
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "test.zelix"
            source.write_text(src, encoding="utf-8")
            try:
                executable, _ = compile_file(source)
            except CompileError as exc:
                self.fail(str(exc))
            result = subprocess.run([str(executable)], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "30")

if __name__ == "__main__":
    unittest.main()
