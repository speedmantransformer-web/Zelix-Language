package dev.zelix.minecraft;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

final class ModRuntime {
    private static final Pattern EVENT_PATTERN = Pattern.compile("[A-Za-z0-9_]+");

    private final Path modsDirectory;
    private final String minecraftVersion;
    private final String pythonCommand;
    private final Path zelixCli;
    private final List<RunningMod> mods = new ArrayList<RunningMod>();
    private boolean started;

    ModRuntime(Path modsDirectory, String minecraftVersion, String pythonCommand, Path zelixCli) {
        if (!ModDescriptor.SUPPORTED_MINECRAFT_VERSIONS.contains(minecraftVersion)) {
            throw new IllegalArgumentException("Unsupported Minecraft Java version: " + minecraftVersion);
        }
        if (pythonCommand == null || pythonCommand.trim().isEmpty()) {
            throw new IllegalArgumentException("A Python executable is required to run Zelix mods");
        }
        this.modsDirectory = modsDirectory.toAbsolutePath().normalize();
        this.minecraftVersion = minecraftVersion;
        this.pythonCommand = pythonCommand;
        this.zelixCli = zelixCli.toAbsolutePath().normalize();
    }

    synchronized void start() throws IOException {
        if (started) {
            throw new IllegalStateException("Zelix mod runtime has already started");
        }
        if (!Files.isRegularFile(zelixCli)) {
            throw new IOException("Zelix CLI script does not exist: " + zelixCli);
        }
        Files.createDirectories(modsDirectory);

        List<Path> directories;
        try (Stream<Path> paths = Files.list(modsDirectory)) {
            directories = paths.filter(Files::isDirectory)
                    .sorted(Comparator.comparing(path -> path.getFileName().toString()))
                    .collect(Collectors.toList());
        }

        Set<String> ids = new HashSet<String>();
        try {
            for (Path directory : directories) {
                if (!Files.isRegularFile(directory.resolve("mod.properties"))) {
                    continue;
                }
                ModDescriptor descriptor = ModDescriptor.read(directory);
                if (!ids.add(descriptor.id)) {
                    throw new IOException("Duplicate Zelix mod id: " + descriptor.id);
                }
                if (!descriptor.minecraftVersions.contains(minecraftVersion)) {
                    System.out.println(
                            "[Zelix] Skipping " + descriptor.id + ": does not support Minecraft "
                                    + minecraftVersion);
                    continue;
                }
                startMod(descriptor);
            }
            started = true;
            System.out.println("[Zelix] Started " + mods.size() + " Zelix mod(s) for Minecraft "
                    + minecraftVersion);
        } catch (IOException | RuntimeException exception) {
            stopAll();
            throw exception;
        }
    }

    synchronized void dispatch(String event) {
        if (!EVENT_PATTERN.matcher(event).matches()) {
            throw new IllegalArgumentException("Invalid Zelix loader event: " + event);
        }
        Iterator<RunningMod> iterator = mods.iterator();
        while (iterator.hasNext()) {
            RunningMod mod = iterator.next();
            try {
                mod.send(event);
            } catch (IOException exception) {
                System.err.println("[Zelix] Disabling mod " + mod.descriptor.id
                        + " after event delivery failed: " + exception.getMessage());
                mod.stop();
                iterator.remove();
            }
        }
    }

    synchronized void stopAll() {
        for (RunningMod mod : mods) {
            mod.stop();
        }
        mods.clear();
        started = false;
    }

    synchronized int activeModCount() {
        return mods.size();
    }

    private void startMod(ModDescriptor descriptor) throws IOException {
        ProcessBuilder builder = new ProcessBuilder(
                pythonCommand, zelixCli.toString(), descriptor.entry.toString());
        builder.directory(descriptor.root.toFile());
        builder.redirectOutput(ProcessBuilder.Redirect.INHERIT);
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);

        Process process;
        try {
            process = builder.start();
        } catch (IOException exception) {
            throw new IOException("Could not start Zelix mod " + descriptor.id
                    + " using Python command " + pythonCommand, exception);
        }
        RunningMod running = new RunningMod(descriptor, process);
        mods.add(running);
        System.out.println("[Zelix] Loaded " + descriptor.name + " (" + descriptor.id + " "
                + descriptor.version + ")");
    }

    private static final class RunningMod {
        private final ModDescriptor descriptor;
        private final Process process;
        private final BufferedWriter input;

        private RunningMod(ModDescriptor descriptor, Process process) {
            this.descriptor = descriptor;
            this.process = process;
            this.input = new BufferedWriter(
                    new OutputStreamWriter(process.getOutputStream(), StandardCharsets.UTF_8));
        }

        private synchronized void send(String event) throws IOException {
            if (!process.isAlive()) {
                throw new IOException("Zelix mod process exited with code " + process.exitValue());
            }
            input.write(event);
            input.newLine();
            input.flush();
        }

        private synchronized void stop() {
            if (!process.isAlive()) {
                closeInput();
                return;
            }
            try {
                send("stop");
            } catch (IOException exception) {
                System.err.println("[Zelix] Could not send stop event to " + descriptor.id
                        + ": " + exception.getMessage());
            }
            closeInput();
            try {
                if (!process.waitFor(2, TimeUnit.SECONDS)) {
                    process.destroy();
                    if (!process.waitFor(1, TimeUnit.SECONDS)) {
                        process.destroyForcibly();
                    }
                }
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
                process.destroyForcibly();
            }
        }

        private void closeInput() {
            try {
                input.close();
            } catch (IOException exception) {
                System.err.println("[Zelix] Could not close mod input for " + descriptor.id
                        + ": " + exception.getMessage());
            }
        }
    }
}
