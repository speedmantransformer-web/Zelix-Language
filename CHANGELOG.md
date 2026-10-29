# Changelog

## 0.3.2 - 2026-10-29

- Added set support for string arrays, comparing array contents for duplicates, membership, and removal.
- Added optional prompts for interactive input expressions.
- Added an experimental LaunchWrapper event bridge example for Zelix Minecraft Java mods.
- Updated the VS Code extension to 0.4.2 with string-array set syntax support.

## 0.3.1 - 2026-10-29

- Fixed native C code generation for closing a channel.
- Added static type checking for annotations, generic function calls, typed collection operations, tasks, and channels.
- Added generic lists, maps, sets, and tuples, plus collection bounds and key/element validation.
- Added async/await tasks, `sleep`, channels, and isolated worker-thread functions to the interpreter and native C backend.
- Added the VS Code 0.4.1 extension update with new completions, syntax highlighting, snippets, documentation, and end-to-end examples.
- Added a shared Zelix lexer, parser, and intermediate representation for interpretation and compilation.
- Added Raylib sprite, texture, animation, camera, input, and hot-reload APIs.
- Added the Zelix interpreter, IR-based native compiler, Raylib game APIs, and VS Code extension.
- Added local project manifests and path-based package dependencies.
- Added test automation, a comparative benchmark harness, and Python package metadata.

Zelix is not yet a stable 1.0 release. Native Raylib builds and performance results must be verified on supported target environments before declaring stability.
