# Changelog

## 0.5.0 - 2026-11-02

- Added a direct LLVM IR backend for typed numeric functions, control flow, and numeric lists, with a C ABI bridge for the existing runtime and Raylib APIs.
- Added `--backend llvm`, `--llvm-cc`, and `--emit-llvm-ir` CLI options and documented the supported voxel-world build workflow.
- Added LLVM IR generation, runtime bridge, and Clang compilation regression coverage.

## 0.4.0 - 2026-11-01

- Expanded the authenticated Minecraft ModAPI bridge with item/block registration, mod-local resource-pack assets, JEI-style lookup helpers, and a crafting-table recipe browser that transfers ingredients using vanilla inventory clicks.
- Added persistent 3D camera positioning, voxel render-distance culling, a 3D distance API, and deterministic seeded voxel terrain generation in the world example.
- Added an immediate-mode 2D game UI (panels, labels, buttons, checkboxes, and progress bars) and typed number/text/boolean save-load APIs with bounded encoding and explicit errors.
- Added bounded 2D A* path grids with entity waypoint following and native CPU particle emitters.
- Added generation-checked 2D entities with transform, rigidbody, and box-collider components, plus substepped AABB collision resolution with restitution and friction.
- Extended ECS physics to 3D transforms, velocity, force, box colliders, vector gravity, and substepped 3D AABB collision response.
- Added typed native combatants with health, flat armor, damage/healing, and refreshable poison, burning, and regeneration effects.
- Added opt-in strict type checking, including explicit function-boundary types and rejection of unchecked `any` at typed boundaries.
- Added static texture and sound handle checks against copying, collection/channel escapes, leaks, use after release, and inconsistent branch/loop release; native cleanup now covers runtime errors and rejects double sound unloads.
- Added local project `check`, `build`, `run`, and `test` workflows plus the `assert` test builtin.
- Added local constant propagation, statically typed numeric C-code specialization, and an optional Rust baseline to the benchmark harness.

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
