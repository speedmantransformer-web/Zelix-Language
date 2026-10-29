package dev.zelix.minecraft;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

public class ModDescriptorTest {
    @Rule
    public final TemporaryFolder temporaryFolder = new TemporaryFolder();

    @Test
    public void readsBothSupportedMinecraftVersions() throws Exception {
        Path mod = createMod("minecraft=1.8.8, 1.12.2\nentry=main.zelix\n");

        ModDescriptor descriptor = ModDescriptor.read(mod);

        assertEquals("hello_world", descriptor.id);
        assertEquals("1.0.0", descriptor.version);
        assertTrue(descriptor.minecraftVersions.contains("1.8.8"));
        assertTrue(descriptor.minecraftVersions.contains("1.12.2"));
        assertTrue(descriptor.entry.startsWith(descriptor.root));
    }

    @Test
    public void rejectsUnsupportedMinecraftVersions() throws Exception {
        Path mod = createMod("minecraft=26.60\n");

        try {
            ModDescriptor.read(mod);
            fail("Expected the unsupported target version to be rejected");
        } catch (IOException exception) {
            assertTrue(exception.getMessage().contains("unsupported Minecraft version"));
        }
    }

    @Test
    public void rejectsEntriesOutsideTheModDirectory() throws Exception {
        Path mod = createMod("minecraft=1.12.2\nentry=../outside.zelix\n");

        try {
            ModDescriptor.read(mod);
            fail("Expected an entry outside the mod directory to be rejected");
        } catch (IOException exception) {
            assertTrue(exception.getMessage().contains("entry must be a file inside"));
        }
    }

    private Path createMod(String extraProperties) throws Exception {
        Path mod = temporaryFolder.newFolder("sample-mod").toPath();
        String properties = "id=hello_world\n"
                + "name=Hello World\n"
                + "version=1.0.0\n"
                + extraProperties;
        Files.write(mod.resolve("mod.properties"),
                properties.getBytes(StandardCharsets.UTF_8));
        Files.write(mod.resolve("main.zelix"),
                "display text Hello end text\n".getBytes(StandardCharsets.UTF_8));
        Files.write(mod.getParent().resolve("outside.zelix"),
                "display text outside end text\n".getBytes(StandardCharsets.UTF_8));
        return mod;
    }
}
