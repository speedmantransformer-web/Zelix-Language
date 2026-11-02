package dev.zelix.minecraft;

import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

public class ModApiServerTest {
    @Test
    public void servesOnlyAuthenticatedReadOnlyQueries() throws Exception {
        ModApiServer server = new ModApiServer();
        try {
            ModApiSnapshot snapshot = new ModApiSnapshot(
                    Arrays.asList(new ModApiSnapshot.ItemRecord(
                            5, "minecraft:planks", "tile.wood")),
                    Arrays.asList(new ModApiSnapshot.RecipeRecord(
                            5, 4, Collections.singletonList(Collections.singletonList(17)))));
            server.updateSnapshot(snapshot);
            String token = server.token();
            String modToken = server.registerMod("sample_mod");

            assertEquals(
                    "[{\"id\":5,\"registry_name\":\"minecraft:planks\","
                            + "\"unlocalized_name\":\"tile.wood\"}]",
                    server.handleRequest(token + "\titems"));
            assertEquals(
                    "[{\"result_id\":5,\"result_count\":4,\"ingredients\":[[17]]}]",
                    server.handleRequest(token + "\trecipes_for\t5"));
            assertEquals("5", server.handleRequest(token + "\titem_id\tminecraft:planks"));
            assertEquals(
                    "{\"id\":5,\"registry_name\":\"minecraft:planks\","
                            + "\"unlocalized_name\":\"tile.wood\"}",
                    server.handleRequest(token + "\titem_by_id\t5"));
            assertEquals(
                    "{\"result_id\":5,\"result_count\":4,\"ingredients\":[[17]]}",
                    server.handleRequest(token + "\trecipe\t5\t0"));
            assertTrue(server.handleRequest("wrong-token\titems").contains("not authorized"));
            assertEquals(
                    "[{\"id\":5,\"registry_name\":\"minecraft:planks\","
                            + "\"unlocalized_name\":\"tile.wood\"}]",
                    server.handleRequest(modToken + "\titems"));
            assertTrue(server.handleRequest(token + "\tunknown").contains("Unknown ModAPI query"));
        } finally {
            server.close();
        }
    }

    @Test
    public void reportsUnavailableSnapshotInsteadOfReturningEmptyData() throws Exception {
        ModApiServer server = new ModApiServer();
        try {
            assertTrue(server.handleRequest(server.token() + "\titems")
                    .contains("not ready yet"));
            server.setSnapshotError("unsupported mapped registry");
            assertTrue(server.handleRequest(server.token() + "\titems")
                    .contains("unsupported mapped registry"));
        } finally {
            server.close();
        }
    }

    @Test
    public void executesGameplayActionsOnTheClientThread() throws Exception {
        final Thread clientThread = Thread.currentThread();
        final java.util.concurrent.atomic.AtomicReference<Thread> actionThread =
                new java.util.concurrent.atomic.AtomicReference<Thread>();
        ModApiServer server = new ModApiServer((operation, arguments) -> {
            actionThread.set(Thread.currentThread());
            return "42";
        });
        try {
            String modToken = server.registerMod("demo_mod");
            assertTrue(server.handleRequest(
                    modToken + "\tregister_item\tother_mod\tcopper_ingot\t64")
                    .contains("another mod's namespace"));
            final java.util.concurrent.FutureTask<String> request =
                    new java.util.concurrent.FutureTask<String>(() -> server.handleRequest(
                            modToken + "\tregister_item\tdemo_mod\tcopper_ingot\t64"));
            Thread worker = new Thread(request, "modapi-test-client");
            worker.start();
            for (int attempt = 0; attempt < 100 && !request.isDone(); attempt++) {
                server.processPendingActions();
                Thread.sleep(5);
            }
            assertEquals("42", request.get(1, java.util.concurrent.TimeUnit.SECONDS));
            assertEquals(clientThread, actionThread.get());
        } finally {
            server.close();
        }
    }
}
