package dev.zelix.minecraft;

import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

final class ModApiSnapshot {
    final List<ItemRecord> items;
    final List<RecipeRecord> recipes;
    private final String itemsJson;
    private final String recipesJson;

    ModApiSnapshot(List<ItemRecord> items, List<RecipeRecord> recipes) {
        this.items = Collections.unmodifiableList(new ArrayList<ItemRecord>(items));
        this.recipes = Collections.unmodifiableList(new ArrayList<RecipeRecord>(recipes));
        this.itemsJson = serializeItems(this.items);
        this.recipesJson = serializeRecipes(this.recipes);
    }

    static ModApiSnapshot capture() throws ReflectiveOperationException {
        ClassLoader contextLoader = Thread.currentThread().getContextClassLoader();
        Class<?> itemClass = loadMinecraftClass("net.minecraft.item.Item", contextLoader);
        ClassLoader loader = itemClass.getClassLoader();
        Object registry = staticField(itemClass,
                "itemRegistry", "field_150901_e", "REGISTRY");
        List<ItemRecord> items = readItems(registry);
        Class<?> managerClass = loadMinecraftClass(
                "net.minecraft.item.crafting.CraftingManager", loader);
        Object manager = staticCall(managerClass,
                "getInstance", "func_77594_a", "getInstance");
        Object recipeList = call(manager, "getRecipeList", "func_77592_b");
        List<RecipeRecord> recipes = readRecipes(recipeList, registry);
        return new ModApiSnapshot(items, recipes);
    }

    private static Class<?> loadMinecraftClass(String name, ClassLoader preferred)
            throws ClassNotFoundException {
        if (preferred != null) {
            try {
                return Class.forName(name, false, preferred);
            } catch (ClassNotFoundException ignored) {
                // Try the loader that defined this bridge.
            }
        }
        ClassLoader bridgeLoader = ModApiSnapshot.class.getClassLoader();
        if (bridgeLoader != preferred) {
            return Class.forName(name, false, bridgeLoader);
        }
        throw new ClassNotFoundException("Could not load Minecraft class " + name);
    }

    String itemsJson() {
        return itemsJson;
    }

    String recipesJson() {
        return recipesJson;
    }

    String recipesForJson(int itemId) {
        List<RecipeRecord> matching = new ArrayList<RecipeRecord>();
        for (RecipeRecord recipe : recipes) {
            if (recipe.resultId == itemId) {
                matching.add(recipe);
            }
        }
        return serializeRecipes(matching);
    }

    String itemByIdJson(int itemId) {
        for (ItemRecord item : items) {
            if (item.id == itemId) {
                return serializeItem(item);
            }
        }
        throw new IllegalArgumentException("No item is registered with ID " + itemId);
    }

    String recipeJson(int itemId, int recipeIndex) {
        int currentIndex = 0;
        for (RecipeRecord recipe : recipes) {
            if (recipe.resultId == itemId) {
                if (currentIndex++ == recipeIndex) {
                    String serialized = serializeRecipes(Collections.singletonList(recipe));
                    return serialized.substring(1, serialized.length() - 1);
                }
            }
        }
        throw new IllegalArgumentException(
                "No recipe " + recipeIndex + " produces item ID " + itemId);
    }

    int itemId(String registryName) {
        for (ItemRecord item : items) {
            if (item.registryName.equals(registryName)) {
                return item.id;
            }
        }
        return -1;
    }

    private static List<ItemRecord> readItems(Object registry)
            throws ReflectiveOperationException {
        List<ItemRecord> items = new ArrayList<ItemRecord>();
        Object keys = call(registry, "getKeys", "func_148742_b");
        if (!(keys instanceof Iterable)) {
            throw new ReflectiveOperationException("Minecraft item registry keys are not iterable");
        }
        for (Object key : (Iterable<?>) keys) {
            Object item = call(registry, new String[] {"getObject", "func_82594_a"}, key);
            if (item == null) {
                continue;
            }
            int id = registryId(registry, item);
            String registryName = String.valueOf(key);
            String unlocalizedName = optionalString(item,
                    "getUnlocalizedName", "func_77658_a");
            items.add(new ItemRecord(id, registryName, unlocalizedName));
        }
        Collections.sort(items, Comparator.comparingInt(value -> value.id));
        return items;
    }

    private static List<RecipeRecord> readRecipes(Object recipeList, Object registry)
            throws ReflectiveOperationException {
        if (!(recipeList instanceof Iterable)) {
            throw new ReflectiveOperationException("Minecraft crafting recipes are not iterable");
        }
        List<RecipeRecord> recipes = new ArrayList<RecipeRecord>();
        for (Object recipe : (Iterable<?>) recipeList) {
            if (recipe == null) {
                continue;
            }
            Object output = call(recipe, "getRecipeOutput", "func_77571_b");
            if (output == null) {
                continue;
            }
            Object resultItem = call(output, "getItem", "func_77973_b");
            if (resultItem == null) {
                continue;
            }
            int resultId = registryId(registry, resultItem);
            int resultCount = stackCount(output);
            List<List<Integer>> ingredients = readIngredients(recipe, registry);
            recipes.add(new RecipeRecord(resultId, resultCount, ingredients));
        }
        return recipes;
    }

    private static List<List<Integer>> readIngredients(Object recipe, Object registry)
            throws ReflectiveOperationException {
        Object value = optionalCall(recipe, "getIngredients", "func_192400_c");
        if (value == null) {
            value = optionalField(recipe, "recipeItems", "field_77574_d", "field_77577_c");
        }
        if (value == null) {
            return Collections.emptyList();
        }
        List<List<Integer>> slots = new ArrayList<List<Integer>>();
        int length = value.getClass().isArray()
                ? Array.getLength(value)
                : value instanceof Iterable ? iterableSize((Iterable<?>) value) : 0;
        if (length == 0) {
            return slots;
        }
        for (int index = 0; index < length; index++) {
            Object ingredient = value.getClass().isArray()
                    ? Array.get(value, index)
                    : iterableAt((Iterable<?>) value, index);
            List<Integer> alternatives = new ArrayList<Integer>();
            if (ingredient != null) {
                Object matching = optionalCall(ingredient,
                        "getMatchingStacks", "func_179532_b");
                if (matching != null) {
                    addStackIds(matching, registry, alternatives);
                } else {
                    addStackId(ingredient, registry, alternatives);
                }
            }
            slots.add(Collections.unmodifiableList(new ArrayList<Integer>(
                    new LinkedHashSet<Integer>(alternatives))));
        }
        return slots;
    }

    private static void addStackIds(
            Object stacks, Object registry, List<Integer> output)
            throws ReflectiveOperationException {
        if (stacks.getClass().isArray()) {
            for (int index = 0; index < Array.getLength(stacks); index++) {
                addStackId(Array.get(stacks, index), registry, output);
            }
        } else if (stacks instanceof Iterable) {
            for (Object stack : (Iterable<?>) stacks) {
                addStackId(stack, registry, output);
            }
        }
    }

    private static void addStackId(Object stack, Object registry, List<Integer> output)
            throws ReflectiveOperationException {
        if (stack == null) {
            return;
        }
        Object item = optionalCall(stack, "getItem", "func_77973_b");
        if (item != null) {
            output.add(registryId(registry, item));
        }
    }

    private static int registryId(Object registry, Object item)
            throws ReflectiveOperationException {
        Object value = optionalCall(registry, "getIDForObject", "func_148757_b");
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        Class<?> itemClass = item.getClass();
        value = staticCallOptional(itemClass,
                new String[] {"getIdFromItem", "func_150891_b"}, item);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        throw new ReflectiveOperationException("Could not resolve a Minecraft item numeric ID");
    }

    private static int stackCount(Object stack) throws ReflectiveOperationException {
        Object value = optionalCall(stack,
                "getCount", "func_190916_E", "getStackSize");
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        value = optionalField(stack, "stackSize", "field_77994_a");
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        return 1;
    }

    private static String optionalString(Object receiver, String... names) {
        try {
            Object value = optionalCall(receiver, names);
            return value == null ? "" : String.valueOf(value);
        } catch (ReflectiveOperationException exception) {
            return "";
        }
    }

    private static Object staticField(Class<?> type, String... names)
            throws ReflectiveOperationException {
        for (String name : names) {
            try {
                Field field = type.getDeclaredField(name);
                if (!Modifier.isStatic(field.getModifiers())) {
                    continue;
                }
                field.setAccessible(true);
                Object value = field.get(null);
                if (value != null) {
                    return value;
                }
            } catch (NoSuchFieldException ignored) {
                // Try the next mapping name.
            }
        }
        throw new ReflectiveOperationException(
                "Could not locate the Minecraft item registry on " + type.getName());
    }

    private static Object staticCall(Class<?> type, String... names)
            throws ReflectiveOperationException {
        Object value = staticCallOptional(type, names);
        if (value == null) {
            throw new ReflectiveOperationException(
                    "Could not locate a static factory on " + type.getName());
        }
        return value;
    }

    private static Object staticCallOptional(Class<?> type, String[] names, Object... args)
            throws ReflectiveOperationException {
        return invoke(type, null, names, args, true);
    }

    private static Object call(Object receiver, String... names)
            throws ReflectiveOperationException {
        return call(receiver, names, new Object[0]);
    }

    private static Object call(Object receiver, String[] names, Object... args)
            throws ReflectiveOperationException {
        return invoke(receiver.getClass(), receiver, names, args, false);
    }

    private static Object optionalCall(Object receiver, String... names)
            throws ReflectiveOperationException {
        return optionalCall(receiver, names, new Object[0]);
    }

    private static Object optionalCall(Object receiver, String[] names, Object... args)
            throws ReflectiveOperationException {
        try {
            return invoke(receiver.getClass(), receiver, names, args, false);
        } catch (NoSuchMethodException exception) {
            return null;
        }
    }

    private static Object invoke(
            Class<?> type, Object receiver, String[] names, Object[] args, boolean requireStatic)
            throws ReflectiveOperationException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            for (Method method : current.getDeclaredMethods()) {
                if (!contains(names, method.getName())
                        || method.getParameterTypes().length != args.length
                        || Modifier.isStatic(method.getModifiers()) != requireStatic
                        || !argumentsMatch(method.getParameterTypes(), args)) {
                    continue;
                }
                method.setAccessible(true);
                return method.invoke(receiver, args);
            }
        }
        for (Method method : type.getMethods()) {
            if (contains(names, method.getName())
                    && method.getParameterTypes().length == args.length
                    && Modifier.isStatic(method.getModifiers()) == requireStatic
                    && argumentsMatch(method.getParameterTypes(), args)) {
                method.setAccessible(true);
                return method.invoke(receiver, args);
            }
        }
        throw new NoSuchMethodException("Could not locate " + type.getName() + "." + names[0]);
    }

    private static boolean argumentsMatch(Class<?>[] parameters, Object[] args) {
        for (int index = 0; index < parameters.length; index++) {
            if (args[index] != null && !wrap(parameters[index]).isInstance(args[index])) {
                return false;
            }
        }
        return true;
    }

    private static Class<?> wrap(Class<?> type) {
        if (!type.isPrimitive()) return type;
        if (type == int.class) return Integer.class;
        if (type == long.class) return Long.class;
        if (type == boolean.class) return Boolean.class;
        if (type == float.class) return Float.class;
        if (type == double.class) return Double.class;
        if (type == short.class) return Short.class;
        if (type == byte.class) return Byte.class;
        if (type == char.class) return Character.class;
        return type;
    }

    private static Object optionalField(Object receiver, String... names)
            throws ReflectiveOperationException {
        for (Class<?> current = receiver.getClass(); current != null;
                current = current.getSuperclass()) {
            for (String name : names) {
                try {
                    Field field = current.getDeclaredField(name);
                    field.setAccessible(true);
                    return field.get(receiver);
                } catch (NoSuchFieldException ignored) {
                    // Try the next mapping name.
                }
            }
        }
        return null;
    }

    private static int iterableSize(Iterable<?> values) {
        int count = 0;
        for (Object ignored : values) count++;
        return count;
    }

    private static Object iterableAt(Iterable<?> values, int index) {
        int current = 0;
        for (Object value : values) {
            if (current++ == index) return value;
        }
        return null;
    }

    private static boolean contains(String[] values, String candidate) {
        for (String value : values) {
            if (value.equals(candidate)) return true;
        }
        return false;
    }

    private static String serializeItems(List<ItemRecord> items) {
        StringBuilder json = new StringBuilder("[");
        for (int index = 0; index < items.size(); index++) {
            if (index > 0) json.append(',');
            json.append(serializeItem(items.get(index)));
        }
        return json.append(']').toString();
    }

    private static String serializeItem(ItemRecord item) {
        return new StringBuilder("{\"id\":").append(item.id)
                .append(",\"registry_name\":").append(quote(item.registryName))
                .append(",\"unlocalized_name\":").append(quote(item.unlocalizedName))
                .append('}').toString();
    }

    private static String serializeRecipes(List<RecipeRecord> recipes) {
        StringBuilder json = new StringBuilder("[");
        for (int index = 0; index < recipes.size(); index++) {
            if (index > 0) json.append(',');
            RecipeRecord recipe = recipes.get(index);
            json.append("{\"result_id\":").append(recipe.resultId)
                    .append(",\"result_count\":").append(recipe.resultCount)
                    .append(",\"ingredients\":[");
            for (int slot = 0; slot < recipe.ingredients.size(); slot++) {
                if (slot > 0) json.append(',');
                json.append('[');
                List<Integer> alternatives = recipe.ingredients.get(slot);
                for (int item = 0; item < alternatives.size(); item++) {
                    if (item > 0) json.append(',');
                    json.append(alternatives.get(item));
                }
                json.append(']');
            }
            json.append("]}");
        }
        return json.append(']').toString();
    }

    private static String quote(String value) {
        StringBuilder output = new StringBuilder("\"");
        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);
            if (character == '"' || character == '\\') {
                output.append('\\').append(character);
            } else if (character < 32) {
                output.append(String.format("\\u%04x", (int) character));
            } else {
                output.append(character);
            }
        }
        return output.append('"').toString();
    }

    static final class ItemRecord {
        final int id;
        final String registryName;
        final String unlocalizedName;

        ItemRecord(int id, String registryName, String unlocalizedName) {
            this.id = id;
            this.registryName = registryName;
            this.unlocalizedName = unlocalizedName;
        }
    }

    static final class RecipeRecord {
        final int resultId;
        final int resultCount;
        final List<List<Integer>> ingredients;

        RecipeRecord(int resultId, int resultCount, List<List<Integer>> ingredients) {
            this.resultId = resultId;
            this.resultCount = resultCount;
            this.ingredients = Collections.unmodifiableList(
                    new ArrayList<List<Integer>>(ingredients));
        }
    }
}
