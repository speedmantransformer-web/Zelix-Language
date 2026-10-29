import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zelix import Interpreter, ExpressionParser, ZelixError
from compiler import (
    CGenerator, CompileError, ZelixParser, compile_file, emit_ir_file,
    validate_file, validate_source,
)
from project import ProjectError, init_project, install_project

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
        self.assertIn("Zelix 0.1.0", output.getvalue())

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
