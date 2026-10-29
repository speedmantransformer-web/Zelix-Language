package dev.zelix.minecraft;

import java.io.IOException;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicBoolean;

public final class RuntimeBridge {
    private static final AtomicBoolean SHUTDOWN_HOOK_REGISTERED = new AtomicBoolean();
    private static volatile ModRuntime runtime;
    private static int updateCount;

    private RuntimeBridge() {
    }

    public static synchronized void start(
            Path modsDirectory,
            String minecraftVersion,
            String pythonCommand,
            Path zelixCli) throws IOException {
        if (runtime != null) {
            throw new IllegalStateException("Zelix mod runtime is already initialized");
        }
        ModRuntime newRuntime =
                new ModRuntime(modsDirectory, minecraftVersion, pythonCommand, zelixCli);
        newRuntime.start();
        runtime = newRuntime;
        if (SHUTDOWN_HOOK_REGISTERED.compareAndSet(false, true)) {
            Runtime.getRuntime().addShutdownHook(new Thread(
                    RuntimeBridge::stop, "zelix-mod-shutdown"));
        }
        newRuntime.dispatch("minecraft_version_" + minecraftVersion.replace('.', '_'));
        newRuntime.dispatch("load");
    }

    public static void onClientTick() {
        ModRuntime current = runtime;
        if (current == null) {
            return;
        }
        updateCount++;
        if (updateCount % 20 == 0) {
            current.dispatch("tick");
        }
    }

    public static synchronized void stop() {
        ModRuntime current = runtime;
        runtime = null;
        if (current != null) {
            current.stopAll();
        }
    }
}
