package dev.zelix.minecraft;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.launchwrapper.ITweaker;
import net.minecraft.launchwrapper.LaunchClassLoader;

public final class ZelixTweaker implements ITweaker {
    private final List<String> launchArguments = new ArrayList<String>();
    private String minecraftVersion = System.getProperty("zelix.minecraftVersion");
    private String pythonCommand = System.getProperty("zelix.python", "python");
    private String modsDirectory = System.getProperty("zelix.mods", "mods");
    private String zelixCli = System.getProperty("zelix.cli", "zelix.py");

    @Override
    public void acceptOptions(
            List<String> arguments, File gameDirectory, File assetsDirectory, String profile) {
        for (int index = 0; index < arguments.size(); index++) {
            String argument = arguments.get(index);
            if (argument.startsWith("--zelixVersion=")) {
                minecraftVersion = argument.substring("--zelixVersion=".length());
            } else if (argument.startsWith("--zelixMods=")) {
                modsDirectory = argument.substring("--zelixMods=".length());
            } else if (argument.startsWith("--zelixPython=")) {
                pythonCommand = argument.substring("--zelixPython=".length());
            } else if (argument.startsWith("--zelixCli=")) {
                zelixCli = argument.substring("--zelixCli=".length());
            } else if (isOption(argument)) {
                if (index + 1 >= arguments.size()) {
                    throw new IllegalArgumentException("Missing value for " + argument);
                }
                String value = arguments.get(++index);
                if ("--zelixVersion".equals(argument)) {
                    minecraftVersion = value;
                } else if ("--zelixMods".equals(argument)) {
                    modsDirectory = value;
                } else if ("--zelixPython".equals(argument)) {
                    pythonCommand = value;
                } else if ("--zelixCli".equals(argument)) {
                    zelixCli = value;
                }
            } else {
                launchArguments.add(argument);
            }
        }
        if (modsDirectory.equals("mods") && gameDirectory != null) {
            modsDirectory = new File(gameDirectory, "mods").getPath();
        }
    }

    @Override
    public void injectIntoClassLoader(LaunchClassLoader classLoader) {
        if (minecraftVersion == null
                || !ModDescriptor.SUPPORTED_MINECRAFT_VERSIONS.contains(minecraftVersion)) {
            throw new IllegalArgumentException(
                    "Set --zelixVersion to 1.8.8 or 1.12.2; got " + minecraftVersion);
        }

        classLoader.registerTransformer(
                "dev.zelix.minecraft.MinecraftEventTransformer");

        Path cli = Paths.get(zelixCli);
        if (!cli.isAbsolute()) {
            cli = Paths.get(System.getProperty("user.dir")).resolve(cli);
        }
        try {
            RuntimeBridge.start(
                    Paths.get(modsDirectory),
                    minecraftVersion,
                    pythonCommand,
                    cli);
        } catch (IOException exception) {
            throw new IllegalStateException("Could not initialize Zelix Minecraft mods", exception);
        }
    }

    @Override
    public String getLaunchTarget() {
        return "net.minecraft.client.main.Main";
    }

    @Override
    public String[] getLaunchArguments() {
        return launchArguments.toArray(new String[launchArguments.size()]);
    }

    private static boolean isOption(String argument) {
        return "--zelixVersion".equals(argument)
                || "--zelixMods".equals(argument)
                || "--zelixPython".equals(argument)
                || "--zelixCli".equals(argument);
    }
}
