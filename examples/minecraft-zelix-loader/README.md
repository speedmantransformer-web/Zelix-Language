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

The example in `mods/hello-world/main.zelix` shows how to receive events and dispatch them to Zelix functions. Keep the loop alive by reading the next event until `stop`.

## Current boundaries

This is an experimental event bridge, not a Forge or Fabric replacement. The current API only reports loader lifecycle and periodic client-update events; it does not expose Minecraft objects, rendering, input, world state, or methods for changing gameplay. It also cannot load existing Java mods. The hook deliberately fails fast if the target Minecraft class or expected `runTick()V` method cannot be found, instead of silently starting without events.

Run the metadata, bytecode-hook, and runtime integration tests with `gradle test`. If Python is not named `python` on `PATH`, set `-Dzelix.pythonCommand=C:\path\to\python.exe`.
