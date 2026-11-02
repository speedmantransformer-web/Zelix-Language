package net.minecraft.item.crafting;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;

public final class CraftingManager {
    private static final CraftingManager INSTANCE = new CraftingManager();
    private final List<Recipe> recipes = Collections.singletonList(new Recipe(
            new ItemStack(Item.itemRegistry.getObject("minecraft:planks"), 4),
            Collections.singletonList(new Ingredient(
                    new ItemStack[] {
                        new ItemStack(Item.itemRegistry.getObject("minecraft:stone"), 1)
                    }))));

    private CraftingManager() {
    }

    public static CraftingManager getInstance() {
        return INSTANCE;
    }

    public List<Recipe> getRecipeList() {
        return recipes;
    }

    public static final class Recipe {
        private final ItemStack output;
        private final List<Ingredient> ingredients;

        Recipe(ItemStack output, List<Ingredient> ingredients) {
            this.output = output;
            this.ingredients = ingredients;
        }

        public ItemStack getRecipeOutput() {
            return output;
        }

        public List<Ingredient> getIngredients() {
            return ingredients;
        }
    }

    public static final class Ingredient {
        private final ItemStack[] stacks;

        Ingredient(ItemStack[] stacks) {
            this.stacks = stacks;
        }

        public ItemStack[] getMatchingStacks() {
            return Arrays.copyOf(stacks, stacks.length);
        }
    }
}
