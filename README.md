# Zelix Programming Language

**Zelix 0.4.0 (alpha)** is a keyword-driven programming language with an interpreter, an optimizing native C compiler for Windows and Linux, static types, generic collections, async concurrency, Raylib game APIs, local path-based packages, and VS Code tooling. Zelix has not declared a stable 1.0 release.

The interpreter remains available for quick iteration. Native compilation lowers Zelix programs into an intermediate representation (IR), propagates local constants, folds constant expressions and branches, inlines small pure functions, specializes statically numeric operations, then emits C for a platform-native compiler. VS Code support includes completion, validation diagnostics, formatting, go-to-definition, run/build commands, and an interpreter-backed source debugger with breakpoints, stepping, stack frames, local variables, and program output. Interactive `input` statements are not supported in a debugger session.

## Requirements

- Python 3.10 or newer
- Visual Studio Code (recommended)
- For native builds: a C compiler on `PATH`:
  - **Windows:** MSVC Build Tools (`cl`), Clang, or GCC
  - **Linux:** GCC, Clang, or `cc`
- For games: Raylib 5.0 or newer (development headers and libraries)

## Quick start

Install Zelix from a source checkout with Python 3.10+:

```bash
python -m pip install .
zelix examples/hello.zelix
```

Alternatively, run directly from a checkout:

```bash
python zelix.py examples/hello.zelix
```

In VS Code, open the repository folder and use the included Zelix extension.
Try the examples with `zelix examples/basics.zelix`, `zelix examples/functions.zelix`, and `zelix examples/loops.zelix`.

To compile a program to a native executable, then run it:

```bash
python zelix.py --compile examples/functions.zelix
./examples/functions
```

On Windows, the default executable has an `.exe` extension. Set a different path with `-o`, choose a compiler with `--cc`, and print the optimized IR with `--emit-ir`:

```bash
python zelix.py --compile --emit-ir examples/functions.zelix -o build/functions
python zelix.py --emit-ir examples/functions.zelix
```

On Windows, `py zelix.py examples/hello.zelix` may work if `python` is not on PATH.

## First program

```text
display text Hello from Zelix
create score as 10
score becomes score plus 5
display score
```

Output:

```text
Hello from Zelix
15
```

## Current syntax

- Variables: `create score as 10`
- Reassignment: `score becomes score plus 5`
- Text: `create message as text Hello world end text`
- Output: `display message`
- Input: `create name as input text`
- Conditions: `if score is greater than 10` ... `otherwise` ... `end if`
- Loops: `repeat 3 times` ... `end loop`
- While: `while score is less than 20` ... `end loop`
- Input expressions: declare input with `create name as input text`, then assign later with `name becomes input text` (use `number` for numeric input)
- Functions: see `examples/functions.zelix`
- Math words: `plus`, `minus`, `times`, `divided by`, `remainder`
- Comparisons: `is`, `is not`, `is greater than`, `is less than`, `is greater than or equal to`, `is less than or equal to`
- Logic: `and`, `or`, `not`
- Boolean values: `true`, `false`
- Type annotations: `create score as number with 3`
- Generic collection types: `list<number>`, `map<text, number>`, `set<number>`, `set<list<text>>`, `tuple<number, text>`
- Concurrency: `async function`, `await`, `spawn`, `spawn_thread`, and typed channels

Statements are line-based and blocks end with explicit keywords. Periods at the end of statements are optional. Commas are available for separating values, but are not required for ordinary statements.

### Important text-literal rule

For unambiguous text, use `text ... end text`:

```text
create greeting as text Hello, world. end text
```

Text content may include punctuation. The comma-and-period restriction applies to Zelix's programming syntax, not the content of a text value. In this prototype, text declarations must fit on one source line.

## Functions

Function declarations use this format:

```text
function add taking first and second
    return first plus second
end function

call add with 10 and 20
```

A function call that returns a value can be assigned:

```text
create answer as add with 10 and 20
display answer
```

Parameters are separated by the word `and`. Function calls accept nested expressions; use parentheses when a nested call contains `and` so argument separators stay unambiguous.

## Types, collections, and concurrency

The static checker verifies annotated declarations and function signatures, generic calls, collection element/key types, and task/channel types before interpretation or native compilation. Unannotated values remain dynamically typed (`any`). Use `--strict` with `--check`, `--compile`, or a project command to require typed function parameters/returns and reject unchecked `any` at typed boundaries. Generic functions use uppercase type variables:

```zelix
function first<T> taking items as list<T> returning T
    return get with items and 0
end function

create scores as list<number> with list with 7 and 12
display first with scores
```

Collection constructors and operations include `list`, `map`, `set`, `tuple`, `empty_list`, `empty_map`, `empty_set`, `append`, `insert`, `add_to_set`, `put`, `get`, `remove`, `contains`, `length`, `keys`, and `values`. Lists and tuples use zero-based indexes; invalid indexes and invalid map/set operations produce Zelix errors. Map keys and most set elements must be hashable; sets also accept `list<text>` elements, comparing string arrays by their contents.

Use async functions and channels for tasks. `sleep` yields for a duration in seconds; channel capacity `0` is unbounded:

```zelix
async function produce taking output as channel<number> returning void
    await send with output and 42
    call close_channel with output
end function

create messages as channel<number> with channel with 1
create producer as spawn produce with messages
create answer as await receive with messages
await producer
display answer
```

Use `spawn_thread with function_name and arguments` for a synchronous function that can run independently. Concurrent functions require explicitly typed, concurrency-safe parameters and return types; mutable global access and Raylib calls from concurrent functions are rejected. The interpreter schedules async tasks cooperatively and runs explicit threads on worker threads. The native backend uses operating-system threads for spawned tasks and thread functions, so scheduling details differ by backend.

The interpreter relies on Python-managed memory. Native generated programs check collection bounds/capacity, track their allocations, and reclaim them on process shutdown; this initial arena-style strategy prevents dangling collection references but does not reclaim short-lived allocations during a long-running process. Native game resources are also cleaned up on normal exit and runtime errors. Texture and sound handles have distinct static types and scoped ownership checks: every normally exiting path must release owned handles (or close the owning subsystem); handles cannot be copied or returned, stored in collections/channels, or used after unload/closing their subsystem; path-dependent release is rejected, and resource parameters in functions are borrowed read-only. This is not a general Rust-style borrow checker, and the rest of the language still uses managed/arena-style values.

Run `zelix examples/concurrency_and_collections.zelix` for an end-to-end example covering generic functions, typed collections, channels, async sleep, and a worker thread.

## VS Code integration

The `vscode-zelix` 0.5.0 extension provides syntax highlighting, keyword/variable/function/game/collection/concurrency completions, compiler-backed error highlighting, document formatting, go-to-definition for functions, parameters, variables, and counted-loop variables, plus interpreter-backed debugging. Commands include **Zelix: Run Current File**, **Zelix: Debug Current File**, **Zelix: Compile Current File**, **Zelix: Show Optimized IR**, **Zelix: Initialize Project**, and **Zelix: Install Local Packages**, plus a status-bar Run button. Install the Zelix 0.4.0 CLI separately for execution, validation, and source debugging.

The workspace includes run/build/IR tasks and native debug configurations. VS Code recommends the Zelix extension and the Microsoft C/C++ extension; the latter is needed to debug native builds.

### Install the extension manually

1. Close VS Code.
2. Find your VS Code extensions folder:
   - **Windows:** `%USERPROFILE%\\.vscode\\extensions`
   - **macOS/Linux:** `~/.vscode/extensions`
3. Copy the entire `vscode-zelix` folder into that extensions folder.
4. Rename the copied folder to `zelix-language-0.5.0` if desired.
5. Reopen VS Code.
6. Open a `.zelix` file. The language mode should show **Zelix** in the status bar.
7. If the language CLI is not beside the installed extension, set `zelix.cliPath` to the full path of `zelix.py`. Set `zelix.pythonPath` if the Python command on your system is not `python`.
8. To show the Zelix logo beside `.zelix` files, open the Command Palette, run **Preferences: File Icon Theme**, and choose **Zelix File Icons**.

The extension's Marketplace listing and manual VSIX package include setup and project-package walkthroughs in `vscode-zelix/README.md`.

### Debug Zelix source

1. Install the updated Zelix CLI from the repository root using `python -m pip install .`.
2. Open a `.zelix` file, click beside a statement's line number to add a breakpoint, then run **Zelix: Debug Current File** or press F5.
3. Use Continue, Step Over, Step Into, or Step Out in the Debug toolbar. Inspect the call stack and local variables in the Run and Debug view.
4. To debug without pausing at the first statement, set `"stopOnEntry": false` in a `zelix` launch configuration:

```json
{
  "type": "zelix",
  "request": "launch",
  "name": "Debug current Zelix file",
  "program": "${file}",
  "stopOnEntry": false
}
```

### Debug a native program

1. Install the recommended Microsoft C/C++ extension and a native compiler/debugger (MSVC on Windows; GCC and GDB on Linux).
2. Open the Zelix file you want to debug and run **Zelix: Debug native program** from the Run and Debug view (choose the configuration for your platform).
3. The debug build writes an unoptimized executable with symbols and keeps the generated C source beside it as `<executable>.zelix.c`. Open that generated C file to set breakpoints in generated code, then return focus to the `.zelix` file and start debugging.

Breakpoints currently apply to generated C rather than mapping back to Zelix source lines.

## Command-line usage

```bash
zelix path/to/program.zelix
zelix --version
zelix --check path/to/program.zelix
zelix --emit-ir path/to/program.zelix
zelix --compile --debug path/to/program.zelix
```

`python zelix.py ...` remains available when running from a source checkout.

## Native compiler coverage and limitations

The native backend supports variables, expressions, output, input, conditionals, loops, functions, typed collections, async tasks, channels, and worker threads. It uses the host C compiler to produce a native executable and currently targets the host Windows or Linux platform; cross-compilation is not supported. Generated values use a tagged runtime representation, while the static checker validates annotated types before code generation.

Classes, source-mapped native debugging, and a remote package registry are not implemented yet. Package imports are limited to local path dependencies with globally shared function names.

## Projects and packages

Create a project with `zelix init [directory]`, declare dependencies in `zelix.toml`, then run `zelix install [project-directory]` to resolve local packages and write the reproducible `zelix.lock`. Import a dependency's function definitions with a top-level `use package-name` statement. Project workflows include:

```text
zelix check [project-directory] [--strict]
zelix build [project-directory] [--strict]
zelix run [project-directory] [--strict]
zelix test [project-directory] [--strict]
```

`check` validates Zelix files under `src/` and `tests/`; `build` writes the native executable under `target/`; `run` interprets the project entry point; and `test` runs each `tests/**/*.zelix` file. Tests can use `call assert with condition`. Dependencies and locking remain local path-only; there is no remote registry or package publisher.

See [docs/production-readiness.md](./docs/production-readiness.md) for the manifest format, dependency rules, lockfile behavior, benchmarks, testing, and release process.

## Benchmarks

Run `python benchmarks/run.py` to compare Python, interpreted Zelix, native Zelix, C, and optional Rust on a result-checked integer-sum workload. Native Zelix, C, and Rust measurements are included when their compilers are installed. Compilation is excluded from timed runs; the report includes process startup and median timings. These local microbenchmarks are not universal language rankings or a claim that Zelix outperforms Rust.

For a complete local-package project with comments and execution instructions, see [examples/project-packages](./examples/project-packages).

## Tests and releases

Run `python -m unittest discover -s tests -v`. CI tests Windows and Linux with supported Python versions, checks examples, and verifies that the installed `zelix` CLI works. Native compiler execution is skipped when no compiler is available, and Raylib builds require a separate Raylib-enabled environment.

Zelix remains alpha. See [CHANGELOG.md](./CHANGELOG.md) for release notes and the production-readiness guide for the requirements to declare a stable release.

## Game development (Raylib)

Game APIs run in native-compiled programs; the Python interpreter does not implement these APIs. Install Raylib 5.0+ and make its headers and libraries available to the native compiler. For custom install locations, set `RAYLIB_INCLUDE_DIR` and `RAYLIB_LIB_DIR` to the Raylib include and library directories before compiling.

```powershell
$env:RAYLIB_INCLUDE_DIR = "C:\raylib\include"
$env:RAYLIB_LIB_DIR = "C:\raylib\lib"
python zelix.py --compile examples\game_2d.zelix
```

```bash
export RAYLIB_INCLUDE_DIR=/path/to/raylib/include
export RAYLIB_LIB_DIR=/path/to/raylib/lib
python zelix.py --compile examples/game_2d.zelix
```

The compiler adds the platform's Raylib, OpenGL, audio, window-system, and socket link libraries when it finds game API calls. Standard package-manager installations normally expose these through the compiler's default include and library paths.

### Window, 2D, input, and 3D

Game calls use the existing function-call syntax. Colors and key/button names are text; color names include `white`, `black`, `red`, `green`, `blue`, `orange`, `yellow`, `skyblue`, `raywhite`, and `darkgray`.

```text
call init_window with 800 and 450 and text My Game end text
call set_target_fps with 60

while not window_should_close
    if key_down with text right end text
        display mouse_x
    end if
    call begin_drawing
    call clear_background with text raywhite end text
    call draw_rectangle with 40 and 40 and 60 and 60 and text orange end text
    call draw_text with text Press Escape to close end text and 20 and 20 and 20 and text darkgray end text
    call end_drawing
end loop

call close_window
```

Available drawing/input calls include `draw_circle`, `draw_line`, `draw_text`, `key_pressed`, `key_down`, `key_released`, `mouse_x`, `mouse_y`, `mouse_button_pressed`, `mouse_button_down`, `mouse_button_released`, `mouse_wheel`, `mouse_world_x`, and `mouse_world_y`. Set a 2D camera using `set_camera_2d` (target x/y, offset x/y, zoom, rotation), then bracket world-space drawing with `begin_camera_2d` and `end_camera_2d`. For 3D, bracket `draw_cube`, `draw_sphere`, individual `draw_voxel_face`, or batched `draw_voxel_world` calls with `begin_3d` and `end_3d`; the initial backend supplies a fixed perspective camera.

Run `python zelix.py --compile examples/voxel_world.zelix` with Raylib installed to build the voxel example. It stores air, grass, dirt, stone, and water IDs (0-4) in a flat `list<number>` representing a 3D grid. Inside `begin_3d`/`end_3d`, call `draw_voxel_world` with the block list, width, height, depth, then colors for block IDs 1-4; ID 0 is air. The backend checks six neighbors in native code and batches exposed faces into one Raylib geometry pass, avoiding per-voxel Zelix calls and per-face GPU batch setup. The sample generates seeded rolling terrain and a waterline procedurally.

`set_camera_3d` takes the camera position and target as six world-space coordinates and persists across frames. `set_voxel_render_distance` sets the positive world-unit radius around that camera within which voxel blocks are drawn (default 64, maximum 4096); it skips farther blocks before generating faces. `distance_3d` returns the Euclidean distance between two xyz points. The voxel sample uses WASD to move the camera and Up/Down to adjust render distance.

### Sprites, textures, and animation

`load_texture` loads an image relative to the `.zelix` file and returns a texture handle. Draw it with `draw_sprite` or `draw_sprite_ex`; query its pixel dimensions with `texture_width` and `texture_height`, and release it with `unload_texture`.

`create_animation` takes a texture handle, frame width, frame height, frame count, and frames per second. It reads row-major frames from a sprite sheet. Texture and sound arguments are statically checked; animation and animation-machine handles also have distinct types. `update_animation` advances an animation by a delta in seconds; `draw_animation` draws the current frame at x/y with a scale. Animations loop by default; `set_animation_looping` can make them play once, and `animation_frame` reports the current frame.

An animation machine groups named animations and transitions. Add states with `add_animation_state`, transitions with `add_animation_transition` (machine, from-state, event, to-state), then trigger them with `trigger_animation_event`; it returns true when a transition is taken. Update and draw the active state with `update_animation_machine` and `draw_animation_machine`. Game code decides when to send transition events, for example when movement input changes.

Call `enable_asset_hot_reload` once to check loaded texture file timestamps at each `begin_drawing`; changed valid images replace the old texture while preserving the previous texture if the replacement is invalid. Sounds are not hot-reloaded. `--check` and native compilation verify literal texture/sound asset paths exist next to the source file and use a supported image/audio extension; paths computed at runtime can only be checked when loaded.

See [examples/game_sprites.zelix](./examples/game_sprites.zelix) for a camera, two sprite sheets, keyboard-driven animation state transitions, and hot reload. Add `assets/idle.png` and `assets/walk.png` next to that example before compiling it.

### 2D game UI and save data

Use `ui_panel`, `ui_label`, `ui_button`, `ui_checkbox`, and `ui_progress_bar` inside the normal `begin_drawing`/`end_drawing` frame. These are immediate-mode controls: buttons return true on the frame the left mouse button is pressed over them, and checkboxes return their toggled value when clicked or the supplied value otherwise. The caller owns persistent widget state. Progress bars clamp the displayed value to the range from zero to the supplied positive maximum.

`save_number`, `save_text`, and `save_boolean` append typed values to a save file; their matching `load_*` calls return the latest saved value or the supplied default if the file/key does not exist. Filenames are relative to the `.zelix` source directory and cannot use `..` path segments; keys are 1–64 ASCII letters, digits, dots, underscores, or hyphens. Text values escape control bytes and percent signs. Save records are append-only, and malformed, mismatched, or unreadable records report runtime errors instead of silently returning defaults. Save text is bounded by the native record size; loaded text is limited to 4095 bytes.

See [examples/game_ui_save.zelix](./examples/game_ui_save.zelix) for a small UI loop that loads and saves a score, player name, and checkbox state. The VS Code extension provides the `gameui` snippet.

### Audio

Call `init_audio` before `load_sound`. Sound files are loaded relative to the `.zelix` source file; use `play_sound`, `unload_sound`, and `close_audio` to manage playback and resources.

### Scenes and physics

`create_scene` returns a scene handle. Create 2D rectangle objects with `create_object`, add them with `add_object`, and select/draw a scene with `activate_scene` and `draw_scene`. `move_object`, `set_object_position`, and `clear_scene` update the scene.

The entity/component API provides generation-checked entities with separate transform, rigidbody, and box-collider components. Create an entity and add either a 2D transform (`add_transform`) or a 3D transform (`add_transform_3d`) before its other components. Add a rigidbody (positive mass is dynamic; mass `0` is static) and the matching 2D or 3D box collider. Collider dimensions must be positive; restitution and friction are each between `0` and `1`. Dynamic bodies support velocity and accumulated forces; `entity_collides` and `entity_collides_3d` query AABB overlap in their respective dimensions.

For 3D, query/set the z position with `entity_z` and `set_entity_position_3d`, and use the 3D velocity/force APIs. `physics_set_gravity_3d` accepts an x/y/z acceleration vector; its default is `(0, -9.8, 0)` for Raylib's Y-up convention. Calling the legacy `physics_set_gravity` sets the 3D vector to `(0, value, 0)` as well. `physics_update` advances ECS and legacy `create_body` bodies in substeps no larger than 1/120 second (frame delta remains 0–0.25 seconds). It resolves pairwise AABB penetration and velocity impulses with restitution and friction; ECS colliders without a rigidbody act as immovable obstacles. This is a discrete 3D AABB solver, not a production rigid-body engine: continuous collision detection, joints, rotation, and broad-phase acceleration are not included.

See [examples/game_ecs_physics.zelix](./examples/game_ecs_physics.zelix) for ECS components and a static platform.
See [examples/game_3d_physics.zelix](./examples/game_3d_physics.zelix) for a 3D rigidbody, static box collider, vector gravity, and Raylib rendering.

### Enemy navigation and particles

`create_path_grid` makes one of up to eight bounded 1–64 cell grids with a positive world-space cell size. Mark obstacles with `set_path_blocked`, then call `find_path` with grid and start/goal cell coordinates. The native A* search uses four-way movement and unit traversal costs. Up to 32 paths can be alive at once. `path_length`, `path_x`, and `path_y` inspect the resulting cell route; no route is represented by length zero. Grid coordinates must be in bounds. Changing an obstacle invalidates paths already computed from that grid.

`follow_path` moves a 2D entity transform toward each cell center at the requested world-units-per-second speed. A path is bound to the first entity that follows it; use its boolean result to detect arrival, and destroy the path and grid when finished. This provides basic waypoint steering, not behavior trees, perception, or dynamic replanning.

`create_particle_emitter` creates one of up to 32 bounded emitters with capacity 1–256. `emit_particles` spawns up to the available capacity with a position, count, lifetime, speed, and color; it returns the number actually spawned. `update_particle_emitter` advances particles using the emitter's configurable vertical gravity, and `draw_particle_emitter` renders circles in a 2D drawing pass. Emitters can be queried, cleared, and destroyed. This is a lightweight CPU particle system, not a GPU/VFX graph.

See [examples/game_ai_particles.zelix](./examples/game_ai_particles.zelix) for an enemy following an A* route around blocked cells while responding to a particle-emission input.

### Combat and status effects

`create_combatant` creates a typed combatant handle from maximum health and starting armor. Query health, maximum health, armor, and alive state with `combatant_health`, `combatant_max_health`, `combatant_armor`, and `is_combatant_alive`; change armor with `set_combatant_armor`. `apply_damage` subtracts flat armor from each hit and returns the health actually lost. `heal_combatant` returns the amount restored, clamps to maximum health, and can revive a defeated combatant.

Apply one of the built-in effects `poison`, `burning`, or `regeneration` with `apply_status_effect` (combatant, name, duration in seconds, strength per second). Reapplying an effect refreshes its duration and strength instead of stacking it. Advance effects once per frame with `update_status_effects` and `frame_time`; damage-over-time bypasses armor, and regeneration does not revive defeated combatants. Use `has_status_effect`, `status_effect_remaining`, `remove_status_effect`, and `clear_status_effects` to inspect and manage effects. Each combatant supports up to eight simultaneous effects. Release a handle with `destroy_combatant` when it is no longer needed.

See [examples/game_combat.zelix](./examples/game_combat.zelix) for a runnable Raylib damage/healing/status-effect loop.

### Multiplayer networking

`network_start` opens a non-blocking IPv4 UDP socket on a local port. `network_send` sends a text datagram to an IPv4 address and port; `network_receive` returns the next message or empty text if none is available; `network_close` closes the socket. UDP is connectionless and does not guarantee delivery or ordering, so applications should add acknowledgement/retry logic if their game requires it.

See [examples/game_2d.zelix](./examples/game_2d.zelix), [examples/game_sprites.zelix](./examples/game_sprites.zelix), [examples/game_3d.zelix](./examples/game_3d.zelix), [examples/game_multiplayer.zelix](./examples/game_multiplayer.zelix), [examples/game_combat.zelix](./examples/game_combat.zelix), [examples/game_ecs_physics.zelix](./examples/game_ecs_physics.zelix), [examples/game_3d_physics.zelix](./examples/game_3d_physics.zelix), [examples/game_ai_particles.zelix](./examples/game_ai_particles.zelix), and [examples/game_ui_save.zelix](./examples/game_ui_save.zelix). The VS Code extension includes `game2d`, `draw3d`, `scene`, `body`, `combat`, `ecs`, `ecs3d`, `enemyai`, and `gameui` snippets.

## Minecraft Java mod scripts (experimental)

The experimental [Minecraft Zelix loader](./examples/minecraft-zelix-loader) pairs a Java LaunchWrapper adapter with Zelix `.zelix` mod scripts for Minecraft Java 1.8.8 and 1.12.2. It requires an existing LaunchWrapper-based game profile and a separately installed Zelix CLI. It provides lifecycle/tick events, item/block registration with local assets, item/recipe helpers, and a native crafting-table recipe browser (see the [ModAPI documentation](./examples/minecraft-zelix-loader/README.md)). It is not a Forge/Fabric replacement, does not execute EaglerForge JavaScript, and does not support custom Java subclasses or multiplayer synchronization. Only install mod scripts you trust.

## Remaining roadmap

1. Add native source-mapped debugging and extend ownership analysis to more resource APIs and control-flow cases.
2. Expand native compiler optimizations and verify generated concurrency code with Windows and Linux toolchains.
3. Add remote package registry support and package namespaces.
4. Continue expanding game APIs and examples based on tested platform support.
