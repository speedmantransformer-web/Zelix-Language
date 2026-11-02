package dev.zelix.minecraft;

import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

final class ModApiResourcePack {
    private static final List<Object> PACKS = new ArrayList<Object>();
    private static boolean installed;

    private ModApiResourcePack() {
    }

    @SuppressWarnings("unchecked")
    static synchronized void install(List<ModDescriptor> mods)
            throws ReflectiveOperationException, IOException {
        ClassLoader loader = minecraftClassLoader();
        Class<?> minecraftClass = Class.forName("net.minecraft.client.Minecraft", false, loader);
        Object minecraft = invokeStatic(minecraftClass, new String[] {"getMinecraft", "func_71410_x"});
        Object packs = fieldValue(minecraft, "defaultResourcePacks", "field_110449_ao");
        if (!(packs instanceof List)) {
            throw new ReflectiveOperationException("Minecraft resource-pack list is unavailable");
        }
        boolean hadPacks = !PACKS.isEmpty();
        ((List<Object>) packs).removeAll(PACKS);
        PACKS.clear();

        Class<?> packType = Class.forName(
                "net.minecraft.client.resources.IResourcePack", false, loader);
        for (ModDescriptor mod : mods) {
            Path assets = mod.root.resolve("assets").resolve(mod.id.toLowerCase(Locale.ROOT));
            if (!Files.isDirectory(assets)) {
                continue;
            }
            final Path root = mod.root.toRealPath();
            final String domain = mod.id.toLowerCase(Locale.ROOT);
            Object proxy = Proxy.newProxyInstance(
                    loader, new Class<?>[] {packType},
                    new ResourcePackHandler(root, domain, mod.name));
            ((List<Object>) packs).add(proxy);
            PACKS.add(proxy);
        }
        installed = true;
        if (hadPacks || !PACKS.isEmpty()) {
            refreshResources(minecraft);
        }
    }

    static synchronized void refresh() throws ReflectiveOperationException {
        if (!installed) {
            throw new ReflectiveOperationException(
                    "Zelix resource packs were not installed before content registration");
        }
        ClassLoader loader = minecraftClassLoader();
        Class<?> minecraftClass = Class.forName("net.minecraft.client.Minecraft", false, loader);
        Object minecraft = invokeStatic(minecraftClass, new String[] {"getMinecraft", "func_71410_x"});
        refreshResources(minecraft);
    }

    static ClassLoader minecraftClassLoader() {
        ClassLoader context = Thread.currentThread().getContextClassLoader();
        try {
            Class.forName("net.minecraft.client.Minecraft", false, context);
            return context;
        } catch (ClassNotFoundException exception) {
            return ModApiResourcePack.class.getClassLoader();
        }
    }

    private static void refreshResources(Object minecraft) throws ReflectiveOperationException {
        invoke(minecraft, new String[] {"refreshResources", "func_110436_a"});
    }

    private static Object invokeStatic(Class<?> type, String[] names, Object... args)
            throws ReflectiveOperationException {
        return invokeCompatible(type, null, names, args, true);
    }

    private static Object invoke(Object receiver, String[] names, Object... args)
            throws ReflectiveOperationException {
        return invokeCompatible(receiver.getClass(), receiver, names, args, false);
    }

    private static Object invokeCompatible(
            Class<?> type, Object receiver, String[] names, Object[] args, boolean isStatic)
            throws ReflectiveOperationException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            for (Method method : current.getDeclaredMethods()) {
                if (!contains(names, method.getName())
                        || method.getParameterTypes().length != args.length
                        || Modifier.isStatic(method.getModifiers()) != isStatic
                        || !matches(method.getParameterTypes(), args)) {
                    continue;
                }
                method.setAccessible(true);
                return method.invoke(receiver, args);
            }
        }
        for (Method method : type.getMethods()) {
            if (contains(names, method.getName())
                    && method.getParameterTypes().length == args.length
                    && Modifier.isStatic(method.getModifiers()) == isStatic
                    && matches(method.getParameterTypes(), args)) {
                return method.invoke(receiver, args);
            }
        }
        throw new NoSuchMethodException("Could not locate " + type.getName() + "." + names[0]);
    }

    private static Object fieldValue(Object receiver, String... names)
            throws ReflectiveOperationException {
        for (Class<?> current = receiver.getClass(); current != null;
                current = current.getSuperclass()) {
            for (String name : names) {
                try {
                    Field field = current.getDeclaredField(name);
                    field.setAccessible(true);
                    return field.get(receiver);
                } catch (NoSuchFieldException ignored) {
                    // Try the next mapped name.
                }
            }
        }
        throw new NoSuchFieldException("Could not locate " + receiver.getClass().getName()
                + "." + names[0]);
    }

    private static boolean matches(Class<?>[] parameters, Object[] args) {
        for (int index = 0; index < parameters.length; index++) {
            if (args[index] != null && !wrap(parameters[index]).isInstance(args[index])) {
                return false;
            }
        }
        return true;
    }

    private static Class<?> wrap(Class<?> type) {
        if (type == int.class) return Integer.class;
        if (type == boolean.class) return Boolean.class;
        if (type == long.class) return Long.class;
        if (type == float.class) return Float.class;
        if (type == double.class) return Double.class;
        return type;
    }

    private static boolean contains(String[] values, String value) {
        for (String candidate : values) {
            if (candidate.equals(value)) return true;
        }
        return false;
    }

    private static final class ResourcePackHandler implements InvocationHandler {
        private final Path modRoot;
        private final Path assetsRoot;
        private final Set<String> domains;
        private final String packName;

        private ResourcePackHandler(Path modRoot, String domain, String name) {
            this.modRoot = modRoot;
            this.assetsRoot = modRoot.resolve("assets").resolve(domain).normalize();
            this.domains = Collections.singleton(domain);
            this.packName = "Zelix: " + name;
        }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            String name = method.getName();
            if ("toString".equals(name)) return packName;
            if ("hashCode".equals(name)) return System.identityHashCode(proxy);
            if ("equals".equals(name)) return proxy == args[0];
            if (method.getReturnType() == String.class && method.getParameterTypes().length == 0) {
                return packName;
            }
            if (Set.class.isAssignableFrom(method.getReturnType())) {
                return new LinkedHashSet<String>(domains);
            }
            if (method.getParameterTypes().length == 1
                    && args != null && args[0] != null) {
                if (InputStream.class.isAssignableFrom(method.getReturnType())) {
                    Path resource = resolve(args[0]);
                    return Files.newInputStream(checkedFile(resource));
                }
                if (method.getReturnType() == boolean.class
                        || method.getReturnType() == Boolean.class) {
                    try {
                        Path resource = resolve(args[0]);
                        return Files.isRegularFile(resource)
                                && checkedFile(resource) != null;
                    } catch (IOException exception) {
                        return false;
                    }
                }
            }
            if (BufferedImage.class.isAssignableFrom(method.getReturnType())) return null;
            return null;
        }

        private Path resolve(Object resourceLocation) throws IOException, ReflectiveOperationException {
            String domain = String.valueOf(invokeCompatible(
                    resourceLocation.getClass(), resourceLocation,
                    new String[] {"getResourceDomain", "func_110624_b"}, new Object[0], false));
            String path = String.valueOf(invokeCompatible(
                    resourceLocation.getClass(), resourceLocation,
                    new String[] {"getResourcePath", "func_110623_a"}, new Object[0], false));
            if (!domains.contains(domain) || path.startsWith("/") || path.contains("\\")) {
                throw new IOException("Resource is outside the Zelix mod resource pack");
            }
            Path resolved = assetsRoot.resolve(path).normalize();
            if (!resolved.startsWith(assetsRoot)) {
                throw new IOException("Resource path escapes the Zelix mod resource pack");
            }
            return resolved;
        }

        private Path checkedFile(Path resource) throws IOException {
            Path real = resource.toRealPath();
            if (!real.startsWith(modRoot) || !Files.isRegularFile(real)) {
                throw new IOException("Mod resource is not a regular file");
            }
            return real;
        }
    }
}
