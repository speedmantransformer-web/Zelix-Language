package dev.zelix.minecraft;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Properties;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

final class ModDescriptor {
    static final Set<String> SUPPORTED_MINECRAFT_VERSIONS =
            Collections.unmodifiableSet(new LinkedHashSet<String>(
                    Arrays.asList("1.8.8", "1.12.2")));

    private static final Pattern ID_PATTERN =
            Pattern.compile("[A-Za-z0-9][A-Za-z0-9_.-]{0,63}");
    private static final Pattern VERSION_PATTERN =
            Pattern.compile("(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)");

    final String id;
    final String name;
    final String version;
    final Set<String> minecraftVersions;
    final Path root;
    final Path entry;

    private ModDescriptor(
            String id,
            String name,
            String version,
            Set<String> minecraftVersions,
            Path root,
            Path entry) {
        this.id = id;
        this.name = name;
        this.version = version;
        this.minecraftVersions = Collections.unmodifiableSet(minecraftVersions);
        this.root = root;
        this.entry = entry;
    }

    static ModDescriptor read(Path directory) throws IOException {
        Path root = directory.toRealPath();
        Path manifest = root.resolve("mod.properties");
        if (!Files.isRegularFile(manifest)) {
            throw new IOException("Missing mod.properties in " + root);
        }

        Properties properties = new Properties();
        try (InputStream input = Files.newInputStream(manifest)) {
            properties.load(input);
        }

        String id = required(properties, "id");
        if (!ID_PATTERN.matcher(id).matches()) {
            throw new IOException("Invalid mod id " + id + " in " + manifest);
        }
        String name = required(properties, "name");
        String version = required(properties, "version");
        if (!VERSION_PATTERN.matcher(version).matches()) {
            throw new IOException("Mod " + id + " must use a MAJOR.MINOR.PATCH version");
        }

        Set<String> minecraftVersions = Arrays.stream(required(properties, "minecraft").split(","))
                .map(String::trim)
                .filter(value -> !value.isEmpty())
                .collect(Collectors.toCollection(LinkedHashSet::new));
        if (minecraftVersions.isEmpty()) {
            throw new IOException("Mod " + id + " must declare at least one Minecraft version");
        }
        for (String target : minecraftVersions) {
            if (!SUPPORTED_MINECRAFT_VERSIONS.contains(target)) {
                throw new IOException(
                        "Mod " + id + " declares unsupported Minecraft version " + target);
            }
        }

        String entryName = properties.getProperty("entry", "main.zelix").trim();
        if (entryName.isEmpty()) {
            throw new IOException("Mod " + id + " must declare a non-empty entry path");
        }
        Path entry = root.resolve(entryName).normalize();
        if (!entry.startsWith(root) || !Files.isRegularFile(entry)) {
            throw new IOException("Mod " + id + " entry must be a file inside " + root);
        }
        Path realEntry = entry.toRealPath();
        if (!realEntry.startsWith(root)) {
            throw new IOException("Mod " + id + " entry resolves outside its mod directory");
        }

        return new ModDescriptor(id, name, version, minecraftVersions, root, realEntry);
    }

    private static String required(Properties properties, String key) throws IOException {
        String value = properties.getProperty(key);
        if (value == null || value.trim().isEmpty()) {
            throw new IOException("mod.properties is missing required field " + key);
        }
        return value.trim();
    }
}
