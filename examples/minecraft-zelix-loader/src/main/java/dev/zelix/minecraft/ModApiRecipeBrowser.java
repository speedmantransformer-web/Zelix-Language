package dev.zelix.minecraft;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

final class ModApiRecipeBrowser {
    private static volatile ModApiSnapshot snapshot;
    private static volatile boolean open;
    private static final Set<String> CRAFTING_SCREEN_NAMES =
            Collections.newSetFromMap(new ConcurrentHashMap<String, Boolean>());
    private static String search = "";
    private static int page;
    private static String status = "";

    private ModApiRecipeBrowser() {
    }

    static void updateSnapshot(ModApiSnapshot value) {
        snapshot = value;
    }

    static void configureCraftingScreen(String runtimeName, String transformedName) {
        if (runtimeName != null) CRAFTING_SCREEN_NAMES.add(runtimeName.replace('/', '.'));
        if (transformedName != null) {
            CRAFTING_SCREEN_NAMES.add(transformedName.replace('/', '.'));
        }
    }

    static void open() {
        open = true;
        search = "";
        page = 0;
        status = "";
    }

    public static void draw(Object screen) {
        if (!isCraftingScreen(screen)) return;
        try {
            int left = integerField(screen, "guiLeft", "field_147003_i");
            int top = integerField(screen, "guiTop", "field_147009_r");
            int guiWidth = integerField(screen, "xSize", "field_146999_f");
            int screenWidth = integerField(screen, "width", "field_146294_l");
            int screenHeight = integerField(screen, "height", "field_146295_m");
            int buttonX = left + 6;
            int buttonY = top - 15;
            drawRect(screen, buttonX, buttonY, buttonX + 84, buttonY + 13, 0xD0000000);
            drawText(screen, open ? "Recipes [R]" : "Recipes [R]", buttonX + 3, buttonY + 2,
                    0xFFFFFF);
            if (!open) return;

            int panelWidth = 188;
            int panelX = left + guiWidth + 4;
            if (panelX + panelWidth > screenWidth) panelX = left - panelWidth - 4;
            if (panelX < 2) panelX = 2;
            int panelY = Math.max(2, Math.min(top, screenHeight - 170));
            int panelHeight = Math.min(166, screenHeight - panelY - 2);
            drawRect(screen, panelX, panelY, panelX + panelWidth,
                    panelY + panelHeight, 0xE0202020);
            drawRect(screen, panelX, panelY, panelX + panelWidth,
                    panelY + 1, 0xFFFFFFFF);
            drawText(screen, "Recipe browser", panelX + 5, panelY + 4, 0xFFFFFF);
            drawText(screen, "Search: " + search + "_", panelX + 5, panelY + 17, 0xE0E0E0);

            List<RecipeEntry> entries = matchingRecipes();
            int pageSize = Math.max(1, (panelHeight - 62) / 14);
            int pageCount = Math.max(1, (entries.size() + pageSize - 1) / pageSize);
            page = Math.min(page, pageCount - 1);
            int start = page * pageSize;
            int end = Math.min(entries.size(), start + pageSize);
            for (int index = start; index < end; index++) {
                RecipeEntry entry = entries.get(index);
                int y = panelY + 34 + (index - start) * 14;
                drawRect(screen, panelX + 3, y - 1, panelX + panelWidth - 3, y + 12,
                        index % 2 == 0 ? 0x80383838 : 0x80404040);
                String label = entry.item.registryName + " x" + entry.recipe.resultCount;
                drawText(screen, truncate(label, 27), panelX + 6, y + 1, 0xFFFFFF);
            }
            drawText(screen, "< " + (page + 1) + "/" + pageCount + " >", panelX + 5,
                    panelY + panelHeight - 24, 0xD0D0D0);
            drawText(screen, truncate(status, 28), panelX + 5,
                    panelY + panelHeight - 11, 0xFFFF80);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            logFailure("Could not draw recipe browser", exception);
        }
    }

    public static boolean mouseClicked(Object screen, int mouseX, int mouseY, int button) {
        if (!isCraftingScreen(screen)) return false;
        if (button != 0) return false;
        try {
            int left = integerField(screen, "guiLeft", "field_147003_i");
            int top = integerField(screen, "guiTop", "field_147009_r");
            int guiWidth = integerField(screen, "xSize", "field_146999_f");
            int screenWidth = integerField(screen, "width", "field_146294_l");
            int screenHeight = integerField(screen, "height", "field_146295_m");
            if (mouseX >= left + 6 && mouseX <= left + 90
                    && mouseY >= top - 15 && mouseY <= top - 2) {
                open = !open;
                if (!open) status = "";
                return true;
            }
            if (!open) return false;
            int panelWidth = 188;
            int panelX = left + guiWidth + 4;
            if (panelX + panelWidth > screenWidth) panelX = left - panelWidth - 4;
            if (panelX < 2) panelX = 2;
            int panelY = Math.max(2, Math.min(top, screenHeight - 170));
            int panelHeight = Math.min(166, screenHeight - panelY - 2);
            if (mouseX < panelX || mouseX > panelX + panelWidth
                    || mouseY < panelY || mouseY > panelY + panelHeight) {
                return false;
            }
            if (mouseY < panelY + 33) return true;
            if (mouseY >= panelY + panelHeight - 26) {
                if (mouseX < panelX + panelWidth / 2) page = Math.max(0, page - 1);
                else page++;
                return true;
            }
            int pageSize = Math.max(1, (panelHeight - 62) / 14);
            List<RecipeEntry> entries = matchingRecipes();
            int row = (mouseY - (panelY + 33)) / 14;
            int selected = page * pageSize + row;
            if (row >= 0 && selected < entries.size()) {
                transferRecipe(screen, entries.get(selected).recipe);
            }
            return true;
        } catch (ReflectiveOperationException | RuntimeException exception) {
            status = "Action failed: " + exception.getMessage();
            logFailure("Could not handle recipe browser click", exception);
            return true;
        }
    }

    public static boolean keyTyped(Object screen, char character, int keyCode) {
        if (!isCraftingScreen(screen)) return false;
        if (keyCode == 19) {
            open = !open;
            if (!open) status = "";
            return true;
        }
        if (!open) return false;
        if (keyCode == 1) {
            open = false;
            status = "";
            return true;
        }
        if (keyCode == 14) {
            if (!search.isEmpty()) search = search.substring(0, search.length() - 1);
            page = 0;
            return true;
        }
        if (character >= 32 && character <= 126 && search.length() < 30) {
            search += character;
            page = 0;
            return true;
        }
        return true;
    }

    private static List<RecipeEntry> matchingRecipes() {
        ModApiSnapshot current = snapshot;
        List<RecipeEntry> entries = new ArrayList<RecipeEntry>();
        if (current == null) return entries;
        String query = search.toLowerCase(Locale.ROOT);
        for (ModApiSnapshot.RecipeRecord recipe : current.recipes) {
            for (ModApiSnapshot.ItemRecord item : current.items) {
                if (item.id == recipe.resultId
                        && item.registryName.toLowerCase(Locale.ROOT).contains(query)) {
                    entries.add(new RecipeEntry(item, recipe));
                    break;
                }
            }
        }
        return entries;
    }

    private static void transferRecipe(Object screen, ModApiSnapshot.RecipeRecord recipe)
            throws ReflectiveOperationException {
        Object minecraft = minecraftInstance();
        Object currentScreen = fieldValue(minecraft, "currentScreen", "field_71462_r");
        if (currentScreen != screen) {
            status = "Crafting screen is no longer active";
            return;
        }
        Object container = fieldValue(screen, "inventorySlots", "field_147002_h");
        Object slotValues = fieldValue(container, "inventorySlots", "field_75151_b");
        if (!(slotValues instanceof List) || ((List<?>) slotValues).size() < 10) {
            status = "Crafting slots are unavailable";
            return;
        }
        List<?> slots = (List<?>) slotValues;
        for (int index = 1; index <= 9 && index < slots.size(); index++) {
            Object stack = slotStack(slots.get(index));
            if (!isEmptyStack(stack)) {
                status = "Clear the crafting grid before transfer";
                return;
            }
        }

        List<IngredientTarget> targets = ingredientTargets(recipe);
        if (targets.isEmpty()) {
            status = "Recipe has no transferable ingredients";
            return;
        }
        List<Integer> sourceSlots = findSources(slots, targets);
        if (sourceSlots == null) {
            status = "Missing ingredients in inventory";
            return;
        }

        Object controller = fieldValue(minecraft, "playerController", "field_71442_b");
        Object player = fieldValue(minecraft, "thePlayer", "field_71439_g");
        Object windowIdValue = fieldValue(container, "windowId", "field_75152_c");
        if (!(windowIdValue instanceof Number)) {
            status = "Crafting window ID is unavailable";
            return;
        }
        int windowId = ((Number) windowIdValue).intValue();
        for (int index = 0; index < targets.size(); index++) {
            int source = sourceSlots.get(index);
            int target = targets.get(index).slot;
            clickSlot(controller, windowId, source, 0, player);
            clickSlot(controller, windowId, target, 1, player);
            clickSlot(controller, windowId, source, 0, player);
        }
        status = "Recipe transferred; vanilla crafting rules apply";
    }

    private static List<IngredientTarget> ingredientTargets(
            ModApiSnapshot.RecipeRecord recipe) {
        List<IngredientTarget> targets = new ArrayList<IngredientTarget>();
        if (recipe.ingredients.size() == 9) {
            for (int index = 0; index < 9; index++) {
                List<Integer> alternatives = recipe.ingredients.get(index);
                if (!alternatives.isEmpty()) {
                    targets.add(new IngredientTarget(index + 1, alternatives));
                }
            }
            return targets;
        }
        if (recipe.ingredients.size() > 9) return targets;
        for (int index = 0; index < recipe.ingredients.size(); index++) {
            List<Integer> alternatives = recipe.ingredients.get(index);
            if (!alternatives.isEmpty()) {
                targets.add(new IngredientTarget(index + 1, alternatives));
            }
        }
        return targets;
    }

    private static List<Integer> findSources(
            List<?> slots, List<IngredientTarget> targets)
            throws ReflectiveOperationException {
        int[] itemIds = new int[slots.size()];
        int[] remaining = new int[slots.size()];
        for (int index = 10; index < slots.size(); index++) {
            Object stack = slotStack(slots.get(index));
            if (isEmptyStack(stack)) continue;
            Object item = invoke(stack, new String[] {"getItem", "func_77973_b"});
            itemIds[index] = numericResult(invokeStatic(
                    item.getClass(),
                    new String[] {"getIdFromItem", "func_150891_b"}, item));
            remaining[index] = stackCount(stack);
        }
        List<Integer> sources = new ArrayList<Integer>();
        for (IngredientTarget target : targets) {
            int source = -1;
            for (int index = 10; index < slots.size(); index++) {
                if (remaining[index] > 0 && target.alternatives.contains(itemIds[index])) {
                    source = index;
                    remaining[index]--;
                    break;
                }
            }
            if (source < 0) return null;
            sources.add(source);
        }
        return sources;
    }

    private static int stackCount(Object stack) throws ReflectiveOperationException {
        try {
            Object value = invoke(stack,
                    new String[] {"getCount", "func_190916_E", "getStackSize"});
            if (value instanceof Number) return ((Number) value).intValue();
        } catch (NoSuchMethodException exception) {
            Object value = fieldValue(stack, "stackSize", "field_77994_a");
            if (value instanceof Number) return ((Number) value).intValue();
        }
        return 0;
    }

    private static void clickSlot(
            Object controller, int windowId, int slot, int mouseButton, Object player)
            throws ReflectiveOperationException {
        for (Method method : controller.getClass().getMethods()) {
            if (!("windowClick".equals(method.getName())
                    || "func_78753_a".equals(method.getName()))
                    || method.getParameterTypes().length != 5) {
                continue;
            }
            Class<?>[] types = method.getParameterTypes();
            if (types[0] != int.class || types[1] != int.class || types[2] != int.class
                    || !types[4].isInstance(player)) {
                continue;
            }
            Object clickType;
            if (types[3].isEnum()) {
                @SuppressWarnings({"rawtypes", "unchecked"})
                Object pickup = Enum.valueOf((Class<? extends Enum>) types[3], "PICKUP");
                clickType = pickup;
            } else if (types[3] == int.class || types[3] == Integer.class) {
                clickType = 0;
            } else {
                continue;
            }
            try {
                method.invoke(controller, windowId, slot, mouseButton, clickType, player);
                return;
            } catch (IllegalArgumentException exception) {
                continue;
            } catch (java.lang.reflect.InvocationTargetException exception) {
                Throwable cause = exception.getCause();
                throw new ReflectiveOperationException(
                        cause == null ? "Inventory slot click failed" : cause.getMessage(), cause);
            }
        }
        throw new NoSuchMethodException("Could not locate Minecraft's normal inventory click API");
    }

    private static Object slotStack(Object slot) throws ReflectiveOperationException {
        return invoke(slot, new String[] {"getStack", "func_75211_c"});
    }

    private static boolean isEmptyStack(Object stack) throws ReflectiveOperationException {
        if (stack == null) return true;
        try {
            Object empty = invoke(stack, new String[] {"isEmpty", "func_190926_b"});
            if (empty instanceof Boolean) return ((Boolean) empty).booleanValue();
        } catch (NoSuchMethodException exception) {
            // Minecraft 1.8 uses null for an empty slot.
        }
        return false;
    }

    private static boolean isCraftingScreen(Object screen) {
        for (Class<?> type = screen == null ? null : screen.getClass();
                type != null; type = type.getSuperclass()) {
            if (CRAFTING_SCREEN_NAMES.contains(type.getName())
                    || "net.minecraft.client.gui.inventory.GuiCrafting".equals(type.getName())) {
                return true;
            }
        }
        return false;
    }

    private static Object minecraftInstance() throws ReflectiveOperationException {
        ClassLoader loader = ModApiResourcePack.minecraftClassLoader();
        Class<?> type = Class.forName("net.minecraft.client.Minecraft", true, loader);
        return invokeStatic(type, new String[] {"getMinecraft", "func_71410_x"});
    }

    private static int integerField(Object receiver, String... names)
            throws ReflectiveOperationException {
        Object value = fieldValue(receiver, names);
        if (!(value instanceof Number)) {
            throw new ReflectiveOperationException("Minecraft GUI coordinate is not numeric");
        }
        return ((Number) value).intValue();
    }

    private static Object fieldValue(Object receiver, String... names)
            throws ReflectiveOperationException {
        for (Class<?> type = receiver.getClass(); type != null; type = type.getSuperclass()) {
            for (String name : names) {
                try {
                    Field field = type.getDeclaredField(name);
                    field.setAccessible(true);
                    return field.get(receiver);
                } catch (NoSuchFieldException ignored) {
                    // Try the next mapping name.
                }
            }
        }
        throw new NoSuchFieldException("Could not locate field " + names[0]);
    }

    private static void drawRect(Object screen, int left, int top, int right, int bottom, int color)
            throws ReflectiveOperationException {
        for (Class<?> type = screen.getClass(); type != null; type = type.getSuperclass()) {
            for (Method method : type.getDeclaredMethods()) {
                if (("drawRect".equals(method.getName()) || "func_73734_a".equals(method.getName()))
                        && Modifier.isStatic(method.getModifiers())
                        && method.getParameterTypes().length == 5) {
                    method.setAccessible(true);
                    method.invoke(null, left, top, right, bottom, color);
                    return;
                }
            }
        }
        throw new NoSuchMethodException("Minecraft GUI drawRect method was not found");
    }

    private static void drawText(Object screen, String text, int x, int y, int color)
            throws ReflectiveOperationException {
        Object minecraft = minecraftInstance();
        Object font = fieldValue(minecraft, "fontRendererObj", "field_71466_p");
        invoke(font, new String[] {"drawString", "func_78276_b"}, text, x, y, color);
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
                        && argumentsMatch(method.getParameterTypes(), args)) {
                    method.setAccessible(true);
                    return method.invoke(receiver, args);
                }
            }
        }
        for (Method method : type.getMethods()) {
            if (contains(names, method.getName())
                    && method.getParameterTypes().length == args.length
                    && Modifier.isStatic(method.getModifiers()) == isStatic
                    && argumentsMatch(method.getParameterTypes(), args)) {
                return method.invoke(receiver, args);
            }
        }
        throw new NoSuchMethodException("Could not locate " + type.getName() + "." + names[0]);
    }

    private static int numericResult(Object value) throws ReflectiveOperationException {
        if (!(value instanceof Number)) {
            throw new ReflectiveOperationException("Minecraft returned a non-numeric item ID");
        }
        return ((Number) value).intValue();
    }

    private static boolean argumentsMatch(Class<?>[] parameters, Object[] args) {
        for (int index = 0; index < parameters.length; index++) {
            Class<?> parameter = parameters[index];
            if (parameter == int.class) parameter = Integer.class;
            else if (parameter == boolean.class) parameter = Boolean.class;
            if (args[index] != null && !parameter.isInstance(args[index])) return false;
        }
        return true;
    }

    private static boolean contains(String[] names, String name) {
        for (String candidate : names) {
            if (candidate.equals(name)) return true;
        }
        return false;
    }

    private static String truncate(String value, int maxLength) {
        if (value.length() <= maxLength) return value;
        return value.substring(0, Math.max(0, maxLength - 3)) + "...";
    }

    private static void logFailure(String message, Exception exception) {
        System.err.println("[Zelix] " + message + ": " + exception.getMessage());
    }

    private static final class RecipeEntry {
        private final ModApiSnapshot.ItemRecord item;
        private final ModApiSnapshot.RecipeRecord recipe;

        private RecipeEntry(
                ModApiSnapshot.ItemRecord item, ModApiSnapshot.RecipeRecord recipe) {
            this.item = item;
            this.recipe = recipe;
        }
    }

    private static final class IngredientTarget {
        private final int slot;
        private final List<Integer> alternatives;

        private IngredientTarget(int slot, List<Integer> alternatives) {
            this.slot = slot;
            this.alternatives = alternatives;
        }
    }
}
