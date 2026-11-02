package net.minecraft.item;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class Item {
    public static final Registry itemRegistry = new Registry();

    static {
        itemRegistry.register(1, "minecraft:stone", new Item("tile.stone"));
        itemRegistry.register(5, "minecraft:planks", new Item("tile.wood"));
    }

    private final String unlocalizedName;

    private Item(String unlocalizedName) {
        this.unlocalizedName = unlocalizedName;
    }

    public String getUnlocalizedName() {
        return unlocalizedName;
    }

    public static int getIdFromItem(Item item) {
        return itemRegistry.getIDForObject(item);
    }

    public static final class Registry {
        private final Map<String, Item> items = new LinkedHashMap<String, Item>();
        private final Map<Item, Integer> ids = new LinkedHashMap<Item, Integer>();

        private void register(int id, String key, Item item) {
            items.put(key, item);
            ids.put(item, id);
        }

        public List<String> getKeys() {
            return new ArrayList<String>(items.keySet());
        }

        public Item getObject(Object key) {
            return items.get(key);
        }

        public int getIDForObject(Object item) {
            Integer id = ids.get(item);
            return id == null ? -1 : id;
        }
    }
}
