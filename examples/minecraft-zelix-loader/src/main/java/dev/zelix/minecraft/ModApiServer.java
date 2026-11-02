package dev.zelix.minecraft;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

final class ModApiServer implements AutoCloseable {
    private static final int MAX_REQUEST_BYTES = 512;
    private static final int MAX_RESPONSE_BYTES = 16 * 1024 * 1024;
    private static final long ACTION_TIMEOUT_SECONDS = 45;

    private final ServerSocket server;
    private final String token;
    private final ModApiActionHandler actionHandler;
    private final Map<String, String> modTokens = new ConcurrentHashMap<String, String>();
    private final ArrayBlockingQueue<PendingAction> pendingActions =
            new ArrayBlockingQueue<PendingAction>(64);
    private volatile ModApiSnapshot snapshot;
    private volatile String snapshotError;
    private volatile boolean closed;

    ModApiServer() throws IOException {
        this(null);
    }

    ModApiServer(ModApiActionHandler actionHandler) throws IOException {
        server = new ServerSocket(0, 16, InetAddress.getByName("127.0.0.1"));
        this.actionHandler = actionHandler;
        byte[] secret = new byte[32];
        new SecureRandom().nextBytes(secret);
        token = Base64.getUrlEncoder().withoutPadding().encodeToString(secret);
    }

    int port() {
        return server.getLocalPort();
    }

    String token() {
        return token;
    }

    String registerMod(String modId) {
        byte[] secret = new byte[32];
        new SecureRandom().nextBytes(secret);
        String modToken = Base64.getUrlEncoder().withoutPadding().encodeToString(secret);
        modTokens.put(modId, modToken);
        return modToken;
    }

    void updateSnapshot(ModApiSnapshot value) {
        snapshot = value;
        snapshotError = null;
    }

    void setSnapshotError(String message) {
        snapshotError = message;
        snapshot = null;
    }

    void processPendingActions() {
        PendingAction action;
        while ((action = pendingActions.poll()) != null) {
            try {
                action.result.complete(actionHandler.execute(
                        action.operation, action.arguments));
            } catch (Exception exception) {
                action.result.completeExceptionally(exception);
            }
        }
    }

    void start() {
        Thread listener = new Thread(this::serve, "zelix-modapi-bridge");
        listener.setDaemon(true);
        listener.start();
    }

    @Override
    public void close() {
        closed = true;
        PendingAction pending;
        while ((pending = pendingActions.poll()) != null) {
            pending.result.completeExceptionally(
                    new IOException("ModAPI server closed before processing the action"));
        }
        try {
            server.close();
        } catch (IOException exception) {
            System.err.println("[Zelix] Could not close ModAPI bridge: " + exception.getMessage());
        }
    }

    private void serve() {
        while (!closed) {
            try (Socket client = server.accept()) {
                client.setSoTimeout(2000);
                String request = readRequest(client);
                String response = handleRequest(request);
                byte[] bytes = (response + "\n").getBytes(StandardCharsets.UTF_8);
                if (bytes.length > MAX_RESPONSE_BYTES) {
                    bytes = "{\"error\":\"ModAPI response exceeds the size limit\"}\n"
                            .getBytes(StandardCharsets.UTF_8);
                }
                client.getOutputStream().write(bytes);
                client.getOutputStream().flush();
            } catch (IOException exception) {
                if (!closed) {
                    System.err.println("[Zelix] ModAPI bridge request failed: "
                            + exception.getMessage());
                }
            }
        }
    }

    String handleRequest(String request) {
        String[] parts = request.split("\\t", -1);
        if (parts.length < 2) {
            return errorJson("ModAPI request is not authorized");
        }
        String callerId = authenticate(parts[0]);
        if (callerId == null && !constantTimeEquals(token, parts[0])) {
            return errorJson("ModAPI request is not authorized");
        }
        if ("register_item".equals(parts[1])
                || "register_block".equals(parts[1])
                || "recipe_gui".equals(parts[1])) {
            return performAction(parts[1], parts, callerId);
        }
        ModApiSnapshot current = snapshot;
        if (current == null) {
            String message = snapshotError;
            return errorJson(message == null
                    ? "ModAPI item and recipe data is not ready yet"
                    : "ModAPI data unavailable: " + message);
        }
        if ("items".equals(parts[1]) && parts.length == 2) {
            return current.itemsJson();
        }
        if ("recipes".equals(parts[1]) && parts.length == 2) {
            return current.recipesJson();
        }
        if ("recipes_for".equals(parts[1]) && parts.length == 3) {
            try {
                return current.recipesForJson(Integer.parseInt(parts[2]));
            } catch (NumberFormatException exception) {
                return errorJson("ModAPI recipe lookup requires a whole-number item ID");
            }
        }
        if ("item_by_id".equals(parts[1]) && parts.length == 3) {
            try {
                return current.itemByIdJson(Integer.parseInt(parts[2]));
            } catch (IllegalArgumentException exception) {
                return errorJson(exception.getMessage());
            }
        }
        if ("recipe".equals(parts[1]) && parts.length == 4) {
            try {
                int itemId = Integer.parseInt(parts[2]);
                int index = Integer.parseInt(parts[3]);
                if (itemId < 0 || index < 0) {
                    return errorJson("Recipe lookup values must be non-negative");
                }
                return current.recipeJson(itemId, index);
            } catch (IllegalArgumentException exception) {
                return errorJson(exception.getMessage());
            }
        }
        if ("item_id".equals(parts[1]) && parts.length == 3) {
            return Integer.toString(current.itemId(parts[2]));
        }
        return errorJson("Unknown ModAPI query");
    }

    private String performAction(String operation, String[] parts, String callerId) {
        if (actionHandler == null) {
            return errorJson("This ModAPI action is unavailable in the current loader");
        }
        if (closed) return errorJson("ModAPI server is closed");
        String[] arguments = new String[parts.length - 2];
        System.arraycopy(parts, 2, arguments, 0, arguments.length);
        if (callerId != null && !"recipe_gui".equals(operation)
                && (arguments.length == 0 || !callerId.equals(arguments[0]))) {
            return errorJson("ModAPI registration cannot access another mod's namespace");
        }
        PendingAction pending = new PendingAction(operation, arguments);
        if (!pendingActions.offer(pending)) {
            return errorJson("ModAPI action queue is full");
        }
        try {
            return pending.result.get(ACTION_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            pendingActions.remove(pending);
            return errorJson("ModAPI action was interrupted");
        } catch (ExecutionException exception) {
            Throwable cause = exception.getCause();
            return errorJson(cause == null || cause.getMessage() == null
                    ? "ModAPI action failed" : cause.getMessage());
        } catch (TimeoutException exception) {
            pendingActions.remove(pending);
            return errorJson("ModAPI action timed out before the client processed it");
        }
    }

    private String authenticate(String presentedToken) {
        for (Map.Entry<String, String> entry : modTokens.entrySet()) {
            if (constantTimeEquals(entry.getValue(), presentedToken)) {
                return entry.getKey();
            }
        }
        return null;
    }

    private static boolean constantTimeEquals(String expected, String actual) {
        return MessageDigest.isEqual(
                expected.getBytes(StandardCharsets.UTF_8),
                actual.getBytes(StandardCharsets.UTF_8));
    }

    private static String readRequest(Socket client) throws IOException {
        ByteArrayOutputStream request = new ByteArrayOutputStream();
        int value;
        while ((value = client.getInputStream().read()) != -1 && value != '\n') {
            if (request.size() >= MAX_REQUEST_BYTES) {
                throw new IOException("ModAPI request exceeds the size limit");
            }
            if (value != '\r') {
                request.write(value);
            }
        }
        if (value == -1) {
            throw new IOException("ModAPI request ended before its newline");
        }
        return new String(request.toByteArray(), StandardCharsets.UTF_8);
    }

    private static String errorJson(String message) {
        StringBuilder json = new StringBuilder("{\"error\":\"");
        for (int index = 0; index < message.length(); index++) {
            char character = message.charAt(index);
            if (character == '"' || character == '\\') {
                json.append('\\').append(character);
            } else if (character < 32) {
                json.append(' ');
            } else {
                json.append(character);
            }
        }
        return json.append("\"}").toString();
    }

    private static final class PendingAction {
        private final String operation;
        private final String[] arguments;
        private final CompletableFuture<String> result = new CompletableFuture<String>();

        private PendingAction(String operation, String[] arguments) {
            this.operation = operation;
            this.arguments = arguments;
        }
    }
}
