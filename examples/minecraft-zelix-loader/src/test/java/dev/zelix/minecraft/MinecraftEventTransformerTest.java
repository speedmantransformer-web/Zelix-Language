package dev.zelix.minecraft;

import org.junit.Test;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;

import static org.junit.Assert.assertEquals;

public class MinecraftEventTransformerTest {
    @Test
    public void injectsClientTickHookForEachSupportedMethodName() {
        String[] methodNames = {"runTick", "func_71407_l", "s"};
        MinecraftEventTransformer transformer = new MinecraftEventTransformer();

        for (String methodName : methodNames) {
            byte[] original = createMinecraftClass(methodName);
            byte[] transformed = transformer.transform(
                    "net.minecraft.client.Minecraft",
                    "net.minecraft.client.Minecraft",
                    original);

            assertEquals(1, countTickHooks(transformed));
        }
    }

    @Test
    public void leavesUnrelatedClassesUnchanged() {
        byte[] original = createMinecraftClass("runTick");

        byte[] transformed = new MinecraftEventTransformer().transform(
                "example.OtherClass",
                "example.OtherClass",
                original);

        assertEquals(original, transformed);
    }

    private static byte[] createMinecraftClass(String methodName) {
        ClassWriter writer = new ClassWriter(0);
        writer.visit(Opcodes.V1_6, Opcodes.ACC_PUBLIC,
                "net/minecraft/client/Minecraft", null, "java/lang/Object", null);
        MethodVisitor method = writer.visitMethod(
                Opcodes.ACC_PUBLIC,
                methodName,
                "()V",
                null,
                null);
        method.visitCode();
        method.visitInsn(Opcodes.RETURN);
        method.visitMaxs(0, 1);
        method.visitEnd();
        writer.visitEnd();
        return writer.toByteArray();
    }

    private static int countTickHooks(byte[] bytecode) {
        ClassNode node = new ClassNode(Opcodes.ASM5);
        new ClassReader(bytecode).accept(node, 0);
        int count = 0;
        for (Object methodValue : node.methods) {
            MethodNode method = (MethodNode) methodValue;
            for (AbstractInsnNode instruction = method.instructions.getFirst();
                    instruction != null;
                    instruction = instruction.getNext()) {
                if (instruction instanceof MethodInsnNode) {
                    MethodInsnNode call = (MethodInsnNode) instruction;
                    if ("dev/zelix/minecraft/RuntimeBridge".equals(call.owner)
                            && "onClientTick".equals(call.name)
                            && "()V".equals(call.desc)) {
                        count++;
                    }
                }
            }
        }
        return count;
    }
}
