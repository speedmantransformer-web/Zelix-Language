package dev.zelix.minecraft;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Locale;
import java.util.regex.Pattern;

final class ModApiRegistration {
    private static final Pattern NAME_PATTERN = Pattern.compile("[a-z0-9_]{1,48}");
    private static final Set<String> MATERIALS = new HashSet<String>();

    static {
        Collections.addAll(MATERIALS, "rock", "wood", "iron", "cloth", "sand", "ground");
    }

    private ModApiRegistration() {
    }

    static int registerItem(ModDescriptor mod, String name, int stackSize)
            throws ReflectiveOperationException {
        validateName(name);
        if (stackSize < 1 || stackSize > 64) {
            throw new IllegalArgumentException("Item stack size must be from 1 to 64");
        }
        requireAsset(mod, "models/item/" + name + ".json");

        ClassLoader loader = ModApiResourcePack.minecraftClassLoader();
        Class<?> itemType = Class.forName("net.minecraft.item.Item", true, loader);
        Object registry = staticField(itemType, "itemRegistry", "field_150901_e", "REGISTRY");
        String domain = mod.id.toLowerCase(Locale.ROOT);
        Object resourceName = resourceLocation(loader, domain, name);
        if (registryGet(registry, resourceName) != null) {
            throw new IllegalArgumentException(
                    "Item is already registered: " + domain + ":" + name);
        }

        Object item = itemType.getDeclaredConstructor().newInstance();
        invoke(item, new String[] {"setUnlocalizedName", "func_77655_b"}, "item." + name);
        invoke(item, new String[] {"setMaxStackSize", "func_77625_d"}, stackSize);
        invoke(item, new String[] {"setCreativeTab", "func_77637_a"},
                creativeTab(loader, "tabMisc", "field_78027_g"));
        int id = registerObject(registry, resourceName, item);

        registerItemModel(loader, item, domain + ":" + name);
        ModApiResourcePack.refresh();
        return id;
    }

    static int registerBlock(
            ModDescriptor mod, String name, String materialName, float hardness)
            throws ReflectiveOperationException {
        validateName(name);
        if (!MATERIALS.contains(materialName)) {
            throw new IllegalArgumentException(
                    "Unsupported block material " + materialName
                            + "; choose rock, wood, iron, cloth, sand, or ground");
        }
        if (hardness < 0 || hardness > 50) {
            throw new IllegalArgumentException("Block hardness must be from 0 to 50");
        }
        requireAsset(mod, "blockstates/" + name + ".json");
        requireAsset(mod, "models/block/" + name + ".json");
        requireAsset(mod, "models/item/" + name + ".json");

        ClassLoader loader = ModApiResourcePack.minecraftClassLoader();
        String domain = mod.id.toLowerCase(Locale.ROOT);
        Object resourceName = resourceLocation(loader, domain, name);

        Class<?> blockType = Class.forName("net.minecraft.block.Block", true, loader);
        Object blockRegistry = staticField(
                blockType, "blockRegistry", "field_149771_c", "REGISTRY");
        if (registryGet(blockRegistry, resourceName) != null) {
            throw new IllegalArgumentException("Block is already registered: " + domain + ":" + name);
        }
        Class<?> itemType = Class.forName("net.minecraft.item.Item", true, loader);
        Object itemRegistry = staticField(
                itemType,
                "itemRegistry", "field_150901_e", "REGISTRY");
        if (registryGet(itemRegistry, resourceName) != null) {
            throw new IllegalArgumentException(
                    "Block item name is already registered: " + domain + ":" + name);
        }
        Map<Object, Object> blockItems = blockItemMap(itemType, blockType);
        Object blockStateIds = staticField(
                blockType, "BLOCK_STATE_IDS", "field_176229_d");
        Class<?> materialType = Class.forName("net.minecraft.block.material.Material", true, loader);
        Object material = staticField(materialType, materialFields(materialName));
        Constructor<?> blockConstructor = findConstructor(blockType, materialType);
        Object block = blockConstructor.newInstance(material);
        invoke(block, new String[] {"setUnlocalizedName", "func_149663_c"}, "tile." + name);
        invoke(block, new String[] {"setHardness", "func_149711_c"}, hardness);
        invoke(block, new String[] {"setCreativeTab", "func_149647_a"},
                creativeTab(loader, "tabBlock", "field_78027_b"));
        int blockId = registerObject(blockRegistry, resourceName, block);

        Class<?> itemBlockType = Class.forName("net.minecraft.item.ItemBlock", true, loader);
        Object itemBlock = findConstructor(itemBlockType, blockType).newInstance(block);
        invoke(itemBlock, new String[] {"setUnlocalizedName", "func_77655_b"}, "tile." + name);
        invoke(itemBlock, new String[] {"setCreativeTab", "func_77637_a"},
                creativeTab(loader, "tabBlock", "field_78027_b"));
        int itemId = registerObject(itemRegistry, resourceName, itemBlock);
        blockItems.put(block, itemBlock);
        registerBlockStateIds(blockStateIds, block, blockId);

        registerBlockModel(loader, block, domain + ":" + name);
        registerItemModel(loader, itemBlock, domain + ":" + name);
        ModApiResourcePack.refresh();
        return itemId;
    }

    private static void registerBlockStateIds(Object stateIds, Object block, int blockId)
            throws ReflectiveOperationException {
        Object blockState = invoke(block, new String[] {"getBlockState", "func_176194_O"});
        Object states;
        try {
            states = invoke(blockState, new String[] {"getValidStates", "func_177619_a"});
        } catch (NoSuchMethodException exception) {
            states = null;
        }
        if (!(states instanceof Iterable)) {
            states = Collections.singletonList(
                    invoke(block, new String[] {"getDefaultState", "func_176223_P"}));
        }
        for (Object state : (Iterable<?>) states) {
            int metadata = 0;
            try {
                Object value = invoke(block,
                        new String[] {"getMetaFromState", "func_176201_c"}, state);
                if (value instanceof Number) metadata = ((Number) value).intValue();
            } catch (NoSuchMethodException ignored) {
                // Generic blocks only define their default state when metadata is unavailable.
            }
            invoke(stateIds, new String[] {"put", "func_148746_a"}, state,
                    (blockId << 4) | (metadata & 15));
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<Object, Object> blockItemMap(Class<?> itemType, Class<?> blockType)
            throws ReflectiveOperationException {
        for (String name : new String[] {"BLOCK_TO_ITEM", "field_150898_a"}) {
            try {
                Object value = staticField(itemType, name);
                if (value instanceof Map) return (Map<Object, Object>) value;
            } catch (NoSuchFieldException ignored) {
                // Try another mapping name or inspect initialized static maps.
            }
        }
        for (Field field : itemType.getDeclaredFields()) {
            if (!Modifier.isStatic(field.getModifiers())
                    || !Map.class.isAssignableFrom(field.getType())) continue;
            field.setAccessible(true);
            Object value = field.get(null);
            if (!(value instanceof Map)) continue;
            for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
                if (blockType.isInstance(entry.getKey())
                        && itemType.isInstance(entry.getValue())) {
                    return (Map<Object, Object>) value;
                }
            }
        }
        throw new NoSuchFieldException("Could not locate Minecraft's block-to-item mapping");
    }

    private static void validateName(String name) {
        if (name == null || !NAME_PATTERN.matcher(name).matches()) {
            throw new IllegalArgumentException(
                    "Registered item and block names must match [a-z0-9_]{1,48}");
        }
    }

    private static void requireAsset(ModDescriptor mod, String relativePath) {
        Path root = mod.root.resolve("assets").resolve(mod.id.toLowerCase(Locale.ROOT)).normalize();
        Path asset = root.resolve(relativePath).normalize();
        if (!asset.startsWith(root) || !Files.isRegularFile(asset)) {
            throw new IllegalArgumentException(
                    "Required mod asset is missing: assets/" + mod.id.toLowerCase(Locale.ROOT)
                            + "/" + relativePath.replace('\\', '/'));
        }
    }

    private static String[] materialFields(String name) {
        switch (name) {
            case "rock": return new String[] {"rock", "field_151576_e"};
            case "wood": return new String[] {"wood", "field_151575_d"};
            case "iron": return new String[] {"iron", "field_151573_f"};
            case "cloth": return new String[] {"cloth", "field_151571_B"};
            case "sand": return new String[] {"sand", "field_151578_c"};
            case "ground": return new String[] {"ground", "field_151577_b"};
            default: throw new IllegalArgumentException("Unsupported block material " + name);
        }
    }

    private static Object resourceLocation(ClassLoader loader, String domain, String path)
            throws ReflectiveOperationException {
        Class<?> type = Class.forName("net.minecraft.util.ResourceLocation", true, loader);
        try {
            return type.getConstructor(String.class, String.class).newInstance(domain, path);
        } catch (NoSuchMethodException exception) {
            return type.getConstructor(String.class).newInstance(domain + ":" + path);
        }
    }

    private static Object creativeTab(ClassLoader loader, String... names)
            throws ReflectiveOperationException {
        Class<?> type = Class.forName(
                "net.minecraft.creativetab.CreativeTabs", true, loader);
        return staticField(type, names);
    }

    private static Object registryGet(Object registry, Object key)
            throws ReflectiveOperationException {
        return invoke(registry, new String[] {"getObject", "func_82594_a"}, key);
    }

    private static int registerObject(Object registry, Object key, Object value)
            throws ReflectiveOperationException {
        int id = nextId(registry);
        invoke(registry, new String[] {"register", "func_177775_a"}, id, key, value);
        return id;
    }

    private static int nextId(Object registry) throws ReflectiveOperationException {
        Object keys = invoke(registry, new String[] {"getKeys", "func_148742_b"});
        if (!(keys instanceof Iterable)) {
            throw new ReflectiveOperationException("Minecraft registry keys are not iterable");
        }
        Set<Integer> used = new HashSet<Integer>();
        for (Object key : (Iterable<?>) keys) {
            Object value = registryGet(registry, key);
            if (value == null) continue;
            Object id = invoke(registry, new String[] {"getIDForObject", "func_148757_b"}, value);
            if (id instanceof Number) used.add(((Number) id).intValue());
        }
        int candidate = 1;
        while (used.contains(candidate)) candidate++;
        if (candidate > 32767) {
            throw new IllegalStateException("Minecraft registry has no free numeric IDs");
        }
        return candidate;
    }

    private static void registerItemModel(ClassLoader loader, Object item, String name)
            throws ReflectiveOperationException {
        Class<?> minecraftType = Class.forName("net.minecraft.client.Minecraft", true, loader);
        Object minecraft = invokeStatic(
                minecraftType, new String[] {"getMinecraft", "func_71410_x"});
        Object renderer = invoke(minecraft, new String[] {"getRenderItem", "func_175599_af"});
        Object mesher = invokeGetter(
                renderer, new String[] {"getItemModelMesher", "func_175034_a"}, "ItemModelMesher");
        Object modelLocation = modelLocation(loader, name, "inventory");
        invokeItemModelRegister(mesher, item, modelLocation);
    }

    private static void registerBlockModel(ClassLoader loader, Object block, String name)
            throws ReflectiveOperationException {
        Class<?> minecraftType = Class.forName("net.minecraft.client.Minecraft", true, loader);
        Object minecraft = invokeStatic(
                minecraftType, new String[] {"getMinecraft", "func_71410_x"});
        Object dispatcher = invoke(
                minecraft, new String[] {"getBlockRendererDispatcher", "func_175602_ab"});
        Object shapes = invokeGetter(
                dispatcher, new String[] {"getBlockModelShapes", "func_175023_a"},
                "BlockModelShapes");
        Method registration = null;
        for (Method method : shapes.getClass().getMethods()) {
            if (method.getParameterTypes().length == 2
                    && method.getParameterTypes()[0].isInstance(block)
                    && isStateMapper(method.getParameterTypes()[1], block.getClass())) {
                registration = method;
                break;
            }
        }
        if (registration == null) {
            throw new NoSuchMethodException("Could not locate the block-state model registration API");
        }
        final Object defaultState = invoke(block, new String[] {"getDefaultState", "func_176223_P"});
        final Object location = modelLocation(loader, name, "normal");
        Object stateMapper = Proxy.newProxyInstance(
                loader,
                new Class<?>[] {registration.getParameterTypes()[1]},
                new InvocationHandler() {
                    @Override
                    public Object invoke(Object proxy, Method method, Object[] args) {
                        if (Map.class.isAssignableFrom(method.getReturnType())) {
                            return Collections.singletonMap(defaultState, location);
                        }
                        if (method.getReturnType() == boolean.class) return false;
                        if (method.getReturnType() == int.class) return 0;
                        return null;
                    }
                });
        registration.setAccessible(true);
        registration.invoke(shapes, block, stateMapper);
    }

    private static Object modelLocation(ClassLoader loader, String name, String variant)
            throws ReflectiveOperationException {
        String[] classes = {
                "net.minecraft.client.renderer.block.model.ModelResourceLocation",
                "net.minecraft.client.resources.model.ModelResourceLocation"
        };
        ClassNotFoundException failure = null;
        for (String className : classes) {
            try {
                Class<?> type = Class.forName(className, true, loader);
                return type.getConstructor(String.class, String.class)
                        .newInstance(name, variant);
            } catch (ClassNotFoundException exception) {
                failure = exception;
            }
        }
        throw failure == null
                ? new ClassNotFoundException("ModelResourceLocation") : failure;
    }

    private static Object invokeGetter(
            Object receiver, String[] names, String returnTypeName)
            throws ReflectiveOperationException {
        try {
            return invoke(receiver, names);
        } catch (NoSuchMethodException exception) {
            for (Method method : receiver.getClass().getMethods()) {
                if (method.getParameterTypes().length == 0
                        && returnTypeName.equals(method.getReturnType().getSimpleName())) {
                    return method.invoke(receiver);
                }
            }
            throw exception;
        }
    }

    private static void invokeItemModelRegister(Object mesher, Object item, Object modelLocation)
            throws ReflectiveOperationException {
        for (Method method : mesher.getClass().getMethods()) {
            Class<?>[] parameters = method.getParameterTypes();
            if (("register".equals(method.getName()) || "func_178083_a".equals(method.getName()))
                    && parameters.length == 3 && parameters[0].isInstance(item)
                    && (parameters[1] == int.class || parameters[1] == Integer.class)
                    && parameters[2].isInstance(modelLocation)) {
                method.invoke(mesher, item, 0, modelLocation);
                return;
            }
        }
        throw new NoSuchMethodException("Could not locate Minecraft item model registration API");
    }

    private static boolean isStateMapper(Class<?> type, Class<?> blockType) {
        if (!type.isInterface()) return false;
        for (Method method : type.getMethods()) {
            if (Map.class.isAssignableFrom(method.getReturnType())
                    && method.getParameterTypes().length == 1
                    && method.getParameterTypes()[0].isAssignableFrom(blockType)) {
                return true;
            }
        }
        return false;
    }

    private static Constructor<?> findConstructor(Class<?> type, Class<?> parameter)
            throws NoSuchMethodException {
        for (Constructor<?> constructor : type.getDeclaredConstructors()) {
            if (constructor.getParameterTypes().length == 1
                    && constructor.getParameterTypes()[0].isAssignableFrom(parameter)) {
                constructor.setAccessible(true);
                return constructor;
            }
        }
        throw new NoSuchMethodException("Could not locate " + type.getName()
                + " constructor for " + parameter.getName());
    }

    private static Object staticField(Class<?> type, String... names)
            throws ReflectiveOperationException {
        for (String name : names) {
            try {
                Field field = type.getDeclaredField(name);
                if (!Modifier.isStatic(field.getModifiers())) continue;
                field.setAccessible(true);
                return field.get(null);
            } catch (NoSuchFieldException ignored) {
                // Try the next mapping name.
            }
        }
        throw new NoSuchFieldException("Could not locate registry or material on " + type.getName());
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
                if (contains(names, method.getName())
                        && method.getParameterTypes().length == args.length
                        && Modifier.isStatic(method.getModifiers()) == isStatic
                        && matches(method.getParameterTypes(), args)) {
                    method.setAccessible(true);
                    return method.invoke(receiver, args);
                }
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

    private static boolean matches(Class<?>[] parameters, Object[] args) {
        for (int index = 0; index < parameters.length; index++) {
            Class<?> parameter = parameters[index];
            if (parameter == int.class) parameter = Integer.class;
            else if (parameter == float.class) parameter = Float.class;
            else if (parameter == boolean.class) parameter = Boolean.class;
            if (args[index] != null && !parameter.isInstance(args[index])) return false;
        }
        return true;
    }

    private static boolean contains(String[] values, String value) {
        for (String candidate : values) {
            if (candidate.equals(value)) return true;
        }
        return false;
    }
}
