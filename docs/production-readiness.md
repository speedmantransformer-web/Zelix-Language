# Production-readiness workflow

## Projects and local packages

Run `zelix init [directory]` to create a project with a `zelix.toml` manifest and `src/main.zelix` entry point. The manifest declares a stable `MAJOR.MINOR.PATCH` version and path-only dependencies:

```toml
[package]
name = "my-game"
version = "0.1.0"
entry = "src/main.zelix"

[dependencies]
math-tools = { path = "../math-tools" }
```

Dependency packages use their own `zelix.toml`; their entry file contains function definitions only. Import those functions at the top level with `use math-tools`. Names from packages share the Zelix function namespace; import aliases and remote registries are not supported.

Run `zelix install [project-directory]` after changing the manifest or any dependency entry. This resolves local paths, checks package names and dependency cycles, and writes `zelix.lock`. Run and compile the project by passing its entry file or project directory. A missing or stale lockfile is an error when the source imports a package. No package is downloaded or copied.

## Benchmarks

Run `python benchmarks/run.py` to compare process-level medians for the same integer-sum workload in Python, interpreted Zelix, native Zelix (when a C compiler is available), and C (when a GCC-compatible compiler is available). Override the workload with `--iterations` (1–1,000,000) and `--repeats`; add `--json` for machine-readable output. JSON includes interpreter/compiler versions and optimization settings when available.

These are reproducible local microbenchmarks, not universal language rankings. They include process startup, exclude compilation time, validate the computed result, and report the host/platform. Compare results only on the same machine and toolchain; use representative application workloads before making performance claims.

## Tests and releases

Run `python -m unittest discover -s tests -v` to execute the offline test suite. CI checks the test suite, examples, Python package installation, and CLI entry point on Windows and Linux across supported Python versions. Native compiler execution is tested only when a compiler is installed; Raylib integration still requires a separate Raylib-enabled build environment.

The package is alpha until language compatibility, native builds, game integration, and benchmarks have been exercised on release targets. A stable release requires a reviewed, dated changelog entry, passing CI, validated Python source/wheel distributions, and native smoke tests on each claimed operating system. Push a version tag matching `zelix.VERSION` (for example `v0.1.0`) to build and attach Python source and wheel distributions to a GitHub Release; `0.x` tags are marked prereleases. The extension has a separate manual Marketplace workflow; its publisher administrator must configure Marketplace Trusted Publishing for the repository and workflow before publishing.
