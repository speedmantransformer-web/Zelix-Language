# Zelix Minecraft Script Loader (experimental)

This example pairs a small Java LaunchWrapper adapter with Zelix-authored mod scripts. The Java adapter hooks the client update method; each mod's behavior is a `.zelix` program run by the Zelix CLI.

Supported targets are Minecraft Java 1.8.8 and 1.12.2. This does **not** support Minecraft 26.60, Bedrock Edition, Forge/Fabric Java mod JARs, or vanilla launches that do not use LaunchWrapper. Minecraft 1.8.8 and 1.12.2 must already be configured with a compatible LaunchWrapper-based client. The loader does not install Minecraft or Forge.

## Requirements

- Java 8 or newer for the game; the loader bytecode is compiled for Java 8.
- Gradle 7.6+ to build the adapter.
- A Zelix CLI from this source checkout (the sample uses reassignable input expressions) and its Python runtime.
- A LaunchWrapper-based Minecraft Java 1.8.8 or 1.12.2 client.
- Only install mod scripts you trust; they execute as separate processes with your user permissions.

## Build

From this directory:

```shell
gradle build
```

The adapter JAR is written to `build/libs/zelix-minecraft-loader-0.1.0.jar`. LaunchWrapper and ASM are supplied by the existing legacy game profile and are compile-time dependencies of this project.

## Create the Windows setup EXE

From the Zelix repository root in PowerShell, with a JDK 11+ and the Windows .NET Framework C# compiler installed:

```powershell
.\examples\minecraft-zelix-loader\package-windows.ps1
```

The script creates `build\Zelix-Minecraft-Loader-Setup.exe`. The self-extracting setup bundles the Java adapter, a Python embeddable runtime, the Zelix CLI modules, and the hello-world and content-demo mods. It prompts for an already-installed Minecraft game directory and version, copies loader files, and writes the LaunchWrapper arguments to the install folder. It does **not** include Minecraft, authenticate accounts, or change launcher profiles; add the printed arguments to a supported existing LaunchWrapper profile and put the adapter JAR on that profile's classpath. The generated unsigned EXE may trigger a Windows SmartScreen warning.

## Install and launch

1. Put the adapter JAR on the client's Java classpath.
2. Put each Zelix mod in its own directory under the game's `mods` directory.
3. Configure the launcher to pass the following LaunchWrapper arguments (use the actual paths on your machine):

```text
--tweakClass dev.zelix.minecraft.ZelixTweaker
--zelixVersion 1.12.2
--zelixMods C:\Games\Minecraft\mods
--zelixPython C:\Python\python.exe
--zelixCli C:\path\to\Zelix\zelix.py
```

Change `--zelixVersion` to `1.8.8` for that game profile. `--zelixMods` defaults to `<game directory>/mods`; `--zelixPython` defaults to `python`; `--zelixCli` defaults to `zelix.py` in the launcher's working directory. System properties `zelix.minecraftVersion`, `zelix.mods`, `zelix.python`, and `zelix.cli` can be used instead.

The mod folder needs a `mod.properties` file and a Zelix entry script:

```properties
id=hello_world
name=Hello World
version=1.0.0
minecraft=1.8.8,1.12.2
entry=main.zelix
```

The loader checks the ID, semantic version, supported Minecraft targets, and that the entry script resolves inside its mod directory. A mod that does not list the selected game version is skipped. Duplicate IDs and invalid manifests stop loader initialization.

## Mod event loop

Each `.zelix` entry runs as a separate Zelix CLI process. It receives these newline-delimited event names through standard input:

- `minecraft_version_1_8_8` or `minecraft_version_1_12_2`
- `load`
- `tick` once per 20 client `runTick` calls
- `stop` when the game shuts down

The version and `load` events are delivered on the first client tick. This lets mods request game-thread operations without blocking Minecraft startup. The example in `mods/hello-world/main.zelix` shows how to receive events and dispatch them to Zelix functions. Keep the loop alive by reading the next event until `stop`.

### ModAPI item and recipe helpers

These interpreter-only builtins query the live item and crafting recipe registries:

- `modapi_items()` returns a list of maps with numeric `id`, `registry_name`, and `unlocalized_name` fields.
- `modapi_item_id(registry_name)` resolves a `namespace:path` registry name to its numeric ID, or `-1` when it is not registered.
- `modapi_recipes()` returns recipe maps with `result_id`, `result_count`, and `ingredients`. Ingredients are ordered slots; each slot is a list of acceptable numeric item IDs (including ore-dictionary alternatives).
- `modapi_recipes_for(item_id)` returns recipes producing that item.
- `getItemById(item_id)` returns an item map; `getIdForItem(registry_name)` returns its numeric ID.
- `getRecipesForId(item_id)` and `getRecipe(item_id, recipe_index)` provide the corresponding JEI-style helpers.

The loader snapshots the live item registry and crafting recipes on client updates, before delivering the periodic `tick` event (every 20 client updates). Queries made before the first snapshot, or when the current Minecraft mapping cannot be inspected, fail explicitly instead of returning empty results. Example:

```zelix
create planks_id as modapi_item_id with text minecraft:planks end text
create planks_recipes as modapi_recipes_for with planks_id
create recipe as getRecipe with planks_id and 0
create output_count as get with recipe and text result_count end text
```

`item-recipe-query.zelix` is a standalone entry-script example; copy it to a mod directory with a `mod.properties` manifest to run it. It waits for the first `tick` before making queries, since the initial registry snapshot is built at that point.

### Registering items and blocks

Zelix mods can register simple vanilla `Item` and `Block` instances on the Minecraft client thread:

- `modapi_register_item(name, max_stack_size)` registers an item in the calling mod's namespace and returns its numeric item ID. Stack size must be 1–64.
- `modapi_register_block(name, material, hardness)` registers a generic block and its `ItemBlock`; materials are `rock`, `wood`, `iron`, `cloth`, `sand`, or `ground`; hardness must be 0–50. The returned ID is the block's item ID.

Names use lowercase letters, digits, and underscores. Registrations require resource files under `assets/<mod-id>/` in the mod directory; the loader mounts those files as a resource pack:

- Item: `models/item/<name>.json` and the texture(s) referenced by that model, conventionally under `textures/items/`.
- Block: `blockstates/<name>.json`, `models/block/<name>.json`, `models/item/<name>.json`, and referenced textures, conventionally under `textures/blocks/`.

For example, an item model can use `{"parent":"item/generated","textures":{"layer0":"demo_mod:items/copper_ingot"}}`. A cube block model can use `{"parent":"block/cube_all","textures":{"all":"demo_mod:blocks/copper_ore"}}`. The blockstate's normal variant should point at `demo_mod:copper_ore`, and its item model should use parent `demo_mod:block/copper_ore`. Model syntax follows the selected Minecraft version. Resource paths are local to the mod; registrations cannot load files outside it.

The [content-demo mod](./samples/content-demo) exercises both registration calls and includes local model JSON that reuses vanilla textures.

These are generic vanilla objects, not arbitrary Java subclasses: custom callbacks, tools with new behavior, block entities, custom item metadata variants, server registration, and multiplayer synchronization are not provided. Installations that cannot find the target registry/model APIs report an error rather than silently accepting a registration. Because Minecraft 1.8.8/1.12.2 registries are being modified after vanilla initialization, test content in a disposable world first.

### In-game recipe browser

The vanilla crafting-table screen has a small `Recipes [R]` toggle; `R` also opens/closes the browser. `modapi_recipe_gui()` opens it from a Zelix mod. Type to filter recipes by output registry name and click a result to transfer its ingredients into the 3×3 grid. Transfer uses normal inventory slot clicks, requires every ingredient in the player's inventory, and refuses to overwrite a non-empty grid. It does not create items or craft the result; vanilla crafting and server validation still apply. The browser uses recipe snapshots and is available only in the crafting-table screen, not the player inventory screen.

## Current boundaries

This is an experimental event bridge, not a Forge or Fabric replacement. It exposes a limited registry API and recipe browser, not general Minecraft objects, arbitrary reflection, world editing, custom Java behavior, or existing Java mods. APIs are interpreter-only; calling them from a separately compiled native executable fails with a clear runtime error. The attached EaglerForge script's DOM, remote recipe fetch, icon CDN, and JavaScript reflection are not executed; the native browser uses local Minecraft recipe data and resource assets.

Run the metadata, bytecode-hook, and runtime integration tests with `gradle test`. If Python is not named `python` on `PATH`, set `-Dzelix.pythonCommand=C:\path\to\python.exe`.
