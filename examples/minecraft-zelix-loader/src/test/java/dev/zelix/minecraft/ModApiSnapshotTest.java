package dev.zelix.minecraft;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class ModApiSnapshotTest {
    @Test
    public void capturesItemRegistryAndRecipeIngredients() throws Exception {
        ModApiSnapshot snapshot = ModApiSnapshot.capture();

        assertEquals(2, snapshot.items.size());
        assertEquals(1, snapshot.itemId("minecraft:stone"));
        assertEquals(5, snapshot.itemId("minecraft:planks"));
        assertEquals(-1, snapshot.itemId("minecraft:missing"));
        assertTrue(snapshot.itemsJson().contains("\"unlocalized_name\":\"tile.stone\""));
        assertEquals(
                "[{\"result_id\":5,\"result_count\":4,\"ingredients\":[[1]]}]",
                snapshot.recipesForJson(5));
    }
}
