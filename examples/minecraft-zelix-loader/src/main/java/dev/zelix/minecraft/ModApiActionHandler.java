package dev.zelix.minecraft;

interface ModApiActionHandler {
    String execute(String operation, String[] arguments) throws Exception;
}
