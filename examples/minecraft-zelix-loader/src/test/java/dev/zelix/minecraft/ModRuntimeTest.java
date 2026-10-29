package dev.zelix.minecraft;

import java.nio.file.Path;
import java.nio.file.Paths;
import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class ModRuntimeTest {
    @Test
    public void keepsZelixModRunningWhileDispatchingEvents() throws Exception {
        Path repositoryRoot = Paths.get(
                System.getProperty("zelix.repositoryRoot")).toRealPath();
        Path mods = repositoryRoot.resolve(
                "examples/minecraft-zelix-loader/mods");
        Path zelixCli = repositoryRoot.resolve("zelix.py");
        String python = System.getProperty("zelix.pythonCommand", "python");
        ModRuntime runtime = new ModRuntime(mods, "1.12.2", python, zelixCli);

        runtime.start();
        try {
            runtime.dispatch("minecraft_version_1_12_2");
            runtime.dispatch("load");
            runtime.dispatch("tick");
            assertEquals(1, runtime.activeModCount());
        } finally {
            runtime.stopAll();
        }

        assertEquals(0, runtime.activeModCount());
    }
}
