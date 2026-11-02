package dev.zelix.minecraft;

import net.minecraft.launchwrapper.IClassTransformer;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.InsnList;
import org.objectweb.asm.tree.LabelNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;

public final class MinecraftEventTransformer implements IClassTransformer {
    private static final String[] TICK_METHODS = {
            "runTick", "func_71407_l", "s"
    };

    @Override
    public byte[] transform(String name, String transformedName, byte[] basicClass) {
        if (basicClass == null) {
            return basicClass;
        }
        if ("net.minecraft.client.gui.inventory.GuiCrafting".equals(name)
                || "net.minecraft.client.gui.inventory.GuiCrafting".equals(transformedName)) {
            ModApiRecipeBrowser.configureCraftingScreen(name, transformedName);
            return basicClass;
        }
        if ("net.minecraft.client.gui.inventory.GuiContainer".equals(name)
                || "net.minecraft.client.gui.inventory.GuiContainer".equals(transformedName)) {
            return transformGuiContainer(basicClass);
        }
        if (!("net.minecraft.client.Minecraft".equals(name)
                || "net.minecraft.client.Minecraft".equals(transformedName))) {
            return basicClass;
        }

        ClassReader reader = new ClassReader(basicClass);
        ClassNode node = new ClassNode(Opcodes.ASM5);
        reader.accept(node, 0);

        MethodNode target = findTickMethod(node);
        if (target == null) {
            throw new IllegalStateException(
                    "Could not find Minecraft.runTick() in the 1.8.8/1.12.2 client; "
                            + "the Zelix loader cannot attach its tick event");
        }

        int hooks = 0;
        for (AbstractInsnNode instruction = target.instructions.getFirst();
                instruction != null;
                instruction = instruction.getNext()) {
            if (instruction.getOpcode() == Opcodes.RETURN) {
                InsnList hook = new InsnList();
                hook.add(new MethodInsnNode(
                        Opcodes.INVOKESTATIC,
                        "dev/zelix/minecraft/RuntimeBridge",
                        "onClientTick",
                        "()V",
                        false));
                target.instructions.insertBefore(instruction, hook);
                hooks++;
            }
        }
        if (hooks == 0) {
            throw new IllegalStateException("Minecraft.runTick() has no normal return instruction");
        }

        System.out.println("[Zelix] Attached loader event hook to " + target.name + target.desc);
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        node.accept(writer);
        return writer.toByteArray();
    }

    private static byte[] transformGuiContainer(byte[] basicClass) {
        ClassReader reader = new ClassReader(basicClass);
        ClassNode node = new ClassNode(Opcodes.ASM5);
        reader.accept(node, 0);

        MethodNode draw = findMethod(node, new String[] {"drawScreen", "func_73863_a", "a"},
                "(IIF)V");
        MethodNode click = findMethod(node, new String[] {"mouseClicked", "func_73864_a", "a"},
                "(III)V");
        MethodNode key = findMethod(node, new String[] {"keyTyped", "func_73869_a", "a"},
                "(CI)V");
        if (draw == null || click == null || key == null) {
            throw new IllegalStateException(
                    "Could not locate GuiContainer draw/input methods for the recipe browser");
        }

        for (AbstractInsnNode instruction = draw.instructions.getFirst();
                instruction != null;
                instruction = instruction.getNext()) {
            if (instruction.getOpcode() == Opcodes.RETURN) {
                InsnList hook = new InsnList();
                hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ALOAD, 0));
                hook.add(new MethodInsnNode(
                        Opcodes.INVOKESTATIC,
                        "dev/zelix/minecraft/ModApiRecipeBrowser",
                        "draw",
                        "(Ljava/lang/Object;)V",
                        false));
                draw.instructions.insertBefore(instruction, hook);
            }
        }
        injectInputHook(click, "mouseClicked", "(Ljava/lang/Object;III)Z");
        injectInputHook(key, "keyTyped", "(Ljava/lang/Object;CI)Z");

        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        node.accept(writer);
        return writer.toByteArray();
    }

    private static void injectInputHook(
            MethodNode method, String name, String descriptor) {
        InsnList hook = new InsnList();
        hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ALOAD, 0));
        if ("mouseClicked".equals(name)) {
            hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ILOAD, 1));
            hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ILOAD, 2));
            hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ILOAD, 3));
        } else {
            hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ILOAD, 1));
            hook.add(new org.objectweb.asm.tree.VarInsnNode(Opcodes.ILOAD, 2));
        }
        hook.add(new MethodInsnNode(
                Opcodes.INVOKESTATIC,
                "dev/zelix/minecraft/ModApiRecipeBrowser",
                name,
                descriptor,
                false));
        LabelNode continueOriginal = new LabelNode();
        hook.add(new org.objectweb.asm.tree.JumpInsnNode(Opcodes.IFEQ, continueOriginal));
        hook.add(new org.objectweb.asm.tree.InsnNode(Opcodes.RETURN));
        hook.add(continueOriginal);
        method.instructions.insert(hook);
    }

    private static MethodNode findMethod(ClassNode node, String[] names, String descriptor) {
        for (Object value : node.methods) {
            MethodNode method = (MethodNode) value;
            if (method.desc.equals(descriptor) && contains(names, method.name)) return method;
        }
        return null;
    }

    private static boolean contains(String[] values, String candidate) {
        for (String value : values) {
            if (value.equals(candidate)) return true;
        }
        return false;
    }

    private static MethodNode findTickMethod(ClassNode node) {
        for (String methodName : TICK_METHODS) {
            for (Object value : node.methods) {
                MethodNode method = (MethodNode) value;
                if (method.name.equals(methodName) && method.desc.equals("()V")) {
                    return method;
                }
            }
        }
        return null;
    }
}
