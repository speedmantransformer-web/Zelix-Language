#!/usr/bin/env python3
"""Compare Zelix interpreter/native execution with Python and optional C."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_once(command: list[str], cwd: Path, expected: int) -> float:
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - start
    if result.returncode:
        raise RuntimeError(
            f"Benchmark command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stderr.strip()}"
        )
    try:
        actual = int(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Benchmark printed unexpected output: {result.stdout!r}") from exc
    if actual != expected:
        raise RuntimeError(f"Expected benchmark result {expected}, got {actual}")
    return elapsed


def measure(command: list[str], cwd: Path, expected: int, repeats: int) -> float:
    run_once(command, cwd, expected)
    samples = [run_once(command, cwd, expected) for _ in range(repeats)]
    return statistics.median(samples)


def compiler_description(executable: str) -> str:
    result = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, check=False
    )
    output = result.stdout or result.stderr
    return output.splitlines()[0] if output else Path(executable).name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    if not 1 <= args.iterations <= 1_000_000 or args.repeats < 1:
        parser.error("--iterations must be from 1 to 1000000 and --repeats must be positive")

    expected = args.iterations * (args.iterations + 1) // 2
    results: dict[str, float] = {}
    with tempfile.TemporaryDirectory(prefix="zelix-benchmark-") as directory:
        temp = Path(directory)
        zelix_source = temp / "sum.zelix"
        zelix_source.write_text(
            (ROOT / "benchmarks" / "sum.zelix").read_text(encoding="utf-8").replace(
                "__LIMIT__", str(args.iterations)
            ),
            encoding="utf-8",
        )
        python_command = [sys.executable, str(ROOT / "benchmarks" / "sum.py"), str(args.iterations)]
        zelix_interpreter = [sys.executable, str(ROOT / "zelix.py"), str(zelix_source)]
        results["Python"] = measure(python_command, ROOT, expected, args.repeats)
        results["Zelix interpreter"] = measure(zelix_interpreter, ROOT, expected, args.repeats)

        c_compiler = next(
            (shutil.which(name) for name in ("cc", "gcc", "clang") if shutil.which(name)),
            None,
        )
        zelix_compiler = c_compiler or next(
            (shutil.which(name) for name in ("cl",) if shutil.which(name)),
            None,
        )
        if zelix_compiler:
            executable = temp / ("sum-native.exe" if os.name == "nt" else "sum-native")
            build = subprocess.run(
                [
                    sys.executable, str(ROOT / "zelix.py"), "--compile",
                    "--cc", zelix_compiler, "-o", str(executable), str(zelix_source),
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            if build.returncode:
                raise RuntimeError(f"Could not build native Zelix benchmark:\n{build.stderr.strip()}")
            results["Zelix native"] = measure(
                [str(executable)], ROOT, expected, args.repeats
            )

        if c_compiler:
            c_executable = temp / ("sum-c.exe" if os.name == "nt" else "sum-c")
            build = subprocess.run(
                [
                    c_compiler, "-O2", str(ROOT / "benchmarks" / "sum.c"),
                    "-o", str(c_executable),
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            if build.returncode:
                raise RuntimeError(f"Could not build C benchmark:\n{build.stderr.strip()}")
            results["C"] = measure([str(c_executable), str(args.iterations)], ROOT, expected, args.repeats)

    toolchains = {
        "python": {"executable": sys.executable, "version": platform.python_version()},
    }
    zelix_version = subprocess.run(
        [sys.executable, str(ROOT / "zelix.py"), "--version"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    if zelix_compiler:
        compiler_name = Path(zelix_compiler).name.lower()
        native_optimization = (
            "/O2" if os.name == "nt" and compiler_name in {
                "cl", "cl.exe", "clang-cl", "clang-cl.exe"
            } else "-O2"
        )
        toolchains["native_compiler"] = {
            "executable": zelix_compiler,
            "version": compiler_description(zelix_compiler),
            "optimization": native_optimization,
        }
    if c_compiler:
        toolchains["c_compiler"] = {
            "executable": c_compiler,
            "version": compiler_description(c_compiler),
            "optimization": "-O2",
        }
    report = {
        "workload": "sum integers from 1 through N",
        "iterations": args.iterations,
        "repeats": args.repeats,
        "median_process_seconds": results,
        "speedup_vs_python": {
            name: results["Python"] / elapsed for name, elapsed in results.items()
        },
        "platform": platform.platform(),
        "python": platform.python_version(),
        "toolchains": toolchains,
        "zelix_version": zelix_version,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Workload: sum 1..{args.iterations}; median of {args.repeats} process runs")
        for name, elapsed in results.items():
            print(f"{name:20} {elapsed:9.6f} s  ({report['speedup_vs_python'][name]:.2f}x Python)")
        print(f"Platform: {report['platform']} | Python {report['python']}")
        if "Zelix native" not in results:
            print("Native Zelix omitted: no supported C compiler was found.")
        if "C" not in results:
            print("C baseline omitted: no GCC-compatible compiler was found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
