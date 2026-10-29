import contextlib
import io
import json
import queue
import shutil
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
        self.assertIn("display %answer", ir)

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
        self.assertIn('#include "raylib.h"', generated)
        self.assertIn("InitWindow(", generated)
        self.assertIn("DrawRectangle(", generated)
        self.assertIn("WindowShouldClose()", generated)
        self.assertIn("z_game_shutdown();", generated)

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
                "create hero as load_texture with text assets/hero.png end text\n",
                encoding="utf-8",
            )
            validate_file(source)
            source.write_text(
                "create hero as load_texture with text assets/missing.png end text\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CompileError, "does not exist"):
                validate_file(source)
            source.write_text(
                "create hero as load_texture with text assets/hero.txt end text\n",
                encoding="utf-8",
            )
            (root / "assets" / "hero.txt").write_text("not an image", encoding="utf-8")
            with self.assertRaisesRegex(CompileError, "Unsupported texture asset format"):
                validate_file(source)

    def test_game_api_argument_validation(self):
        with self.assertRaisesRegex(CompileError, "Game API init_window expects 3 arguments, got 2"):
            validate_source("call init_window with 640 and 480\n")

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
            "game_sprites.zelix",
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
        self.assertIn("Zelix 0.3.1", output.getvalue())

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
        self.assertEqual(manifest["version"], "0.4.1")
        self.assertEqual(manifest["icon"], "images/zelix-icon.png")
        self.assertEqual(contributes["debuggers"][0]["type"], "zelix")
        self.assertIn("zelix.debugCurrentFile", {
            command["command"] for command in contributes["commands"]
        })
        extension_source = (root / "vscode-zelix" / "extension.js").read_text(encoding="utf-8")
        for feature in ("draw_sprite", "create_animation", "set_camera_2d", "mouse_world_x"):
            self.assertIn(f'"{feature}"', extension_source)
        for feature in ("sleep", "spawn_thread", "COLLECTION_FUNCTIONS"):
            self.assertIn(feature, extension_source)
        self.assertIn('"Zelix async channel producer"', (root / "vscode-zelix" / "snippets" / "zelix.json").read_text(encoding="utf-8"))

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
