package dev.zelix.minecraft;

import net.minecraft.launchwrapper.IClassTransformer;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.InsnList;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;

public final class MinecraftEventTransformer implements IClassTransformer {
    private static final String[] TICK_METHODS = {
            "runTick", "func_71407_l", "s"
    };

    @Override
    public byte[] transform(String name, String transformedName, byte[] basicClass) {
        if (basicClass == null
                || !("net.minecraft.client.Minecraft".equals(name)
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
