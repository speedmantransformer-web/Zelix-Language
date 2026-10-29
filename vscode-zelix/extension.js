const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");
const { ZelixDebugAdapter } = require("./debug_adapter");

const KEYWORDS = [
  "create", "as", "becomes", "display", "input", "text", "number", "use", "if",
  "otherwise", "while", "repeat", "times", "from", "to", "end", "function",
  "taking", "return", "call", "true", "false", "and", "or", "not", "is",
  "greater than", "less than", "greater than or equal to",
  "less than or equal to", "equals", "is not", "plus", "minus", "times",
  "divided by", "remainder",
  "async", "await", "spawn", "number", "boolean", "void", "list", "map",
  "string", "set", "tuple", "channel", "task", "returning",
];
const COLLECTION_FUNCTIONS = [
  "list", "map", "set", "tuple", "empty_list", "empty_map", "empty_set",
  "append", "insert", "add_to_set", "put", "get", "remove", "contains",
  "length", "keys", "values", "channel", "send", "receive", "close_channel",
  "sleep", "spawn_thread",
];
const GAME_FUNCTIONS = [
  "init_window", "close_window", "window_should_close", "frame_time",
  "set_target_fps", "begin_drawing", "end_drawing", "clear_background",
  "draw_rectangle", "draw_circle", "draw_line", "draw_text", "begin_3d",
  "end_3d", "draw_cube", "draw_sphere", "key_pressed", "key_down",
  "key_released", "mouse_x", "mouse_y", "mouse_button_pressed", "mouse_wheel",
  "mouse_button_down", "mouse_button_released", "mouse_world_x", "mouse_world_y",
  "load_texture", "unload_texture", "draw_sprite", "draw_sprite_ex",
  "texture_width", "texture_height", "enable_asset_hot_reload",
  "create_animation", "update_animation", "draw_animation",
  "set_animation_looping", "animation_frame", "create_animation_machine",
  "add_animation_state", "add_animation_transition", "set_animation_state",
  "trigger_animation_event", "update_animation_machine",
  "draw_animation_machine", "set_camera_2d", "begin_camera_2d",
  "end_camera_2d",
  "init_audio", "load_sound", "play_sound", "unload_sound", "close_audio",
  "create_scene", "activate_scene", "create_object", "add_object", "move_object",
  "set_object_position", "draw_scene", "clear_scene", "create_body",
  "physics_set_gravity", "physics_update", "body_set_velocity", "body_apply_force",
  "body_x", "body_y", "body_collides", "network_start", "network_send",
  "network_receive", "network_close",
];

const BLOCK_START = /^(?:if\b|while\b|repeat\b|(?:async\s+)?function\b)/i;
const BLOCK_END = /^end\s+(?:if|loop|function)\b/i;
const BLOCK_MIDDLE = /^otherwise\b/i;

function sourceDefinitions(document) {
  const definitions = new Map();
  const add = (name, line, character) => {
    const key = name.toLowerCase();
    if (!definitions.has(key)) {
      definitions.set(key, new vscode.Location(
        document.uri,
        new vscode.Position(line, character),
      ));
    }
  };
  for (let line = 0; line < document.lineCount; line += 1) {
    const text = document.lineAt(line).text;
    let match = /^\s*create\s+([A-Za-z_]\w*)\s+as\b/i.exec(text);
    if (match) add(match[1], line, text.indexOf(match[1]));
    match = /^\s*(?:async\s+)?function\s+([A-Za-z_]\w*)(?:<[^>]+>)?(?:\s+taking\s+(.+))?/i.exec(text);
    if (match) {
      add(match[1], line, text.indexOf(match[1]));
      if (match[2]) {
        const parameterStart = text.indexOf(match[2]);
        const parameters = match[2].replace(/\s+returning\s+.+$/i, "");
        for (const parameter of parameters.split(/\s+and\s+/i)) {
          const name = parameter.replace(/\s+as\s+.+$/i, "").trim();
          if (/^[A-Za-z_]\w*$/.test(name)) {
            add(name, line, text.indexOf(name, parameterStart));
          }
        }
      }
    }
    match = /^\s*repeat\s+with\s+([A-Za-z_]\w*)\s+from\b/i.exec(text);
    if (match) add(match[1], line, text.indexOf(match[1]));
  }
  return definitions;
}

function provideCompletionItems(document, position) {
  const items = [];
  for (const word of KEYWORDS) {
    const item = new vscode.CompletionItem(word, vscode.CompletionItemKind.Keyword);
    item.insertText = word;
    items.push(item);
  }
  for (const name of GAME_FUNCTIONS) {
    const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Function);
    item.insertText = name;
    item.detail = "Zelix game API (Raylib)";
    items.push(item);
  }
  for (const name of COLLECTION_FUNCTIONS) {
    const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Function);
    item.insertText = name;
    item.detail = "Zelix collection or concurrency API";
    items.push(item);
  }
  const text = document.lineAt(position.line).text.slice(0, position.character);
  const functionPattern = /^\s*(?:async\s+)?function\s+([A-Za-z_]\w*)(?:<[^>]+>)?(?:\s+taking\s+(.+))?/i;
  const functionNames = new Set();
  for (let line = 0; line < document.lineCount; line += 1) {
    const sourceLine = document.lineAt(line).text;
    const create = /^\s*create\s+([A-Za-z_]\w*)\s+as\b/i.exec(sourceLine);
    if (create) {
      items.push(new vscode.CompletionItem(create[1], vscode.CompletionItemKind.Variable));
    }
    const fn = functionPattern.exec(sourceLine);
    if (fn) {
      functionNames.add(fn[1].toLowerCase());
      const signature = new vscode.CompletionItem(fn[1], vscode.CompletionItemKind.Function);
      const parameters = fn[2]
        ? fn[2].replace(/\s+returning\s+.+$/i, "")
          .split(/\s+and\s+/i).map((part) => part.replace(/\s+as\s+.+$/i, "").trim())
        : [];
      signature.detail = parameters.length ? `(${parameters.join(", ")})` : "()";
      signature.insertText = parameters.length
        ? new vscode.SnippetString(
          `${fn[1]} with ${parameters.map((_, index) => `\${${index + 1}}`).join(" and ")}`,
        )
        : fn[1];
      items.push(signature);
    }
  }
  for (const [name] of sourceDefinitions(document)) {
    if (!functionNames.has(name)) {
      items.push(new vscode.CompletionItem(name, vscode.CompletionItemKind.Variable));
    }
  }
  if (/^\s*(?:call\s+)?[A-Za-z_]\w*\s+with\b/i.test(text)) {
    return items;
  }
  const seen = new Set();
  return items.filter((item) => {
    const key = item.label.toString().toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function provideDefinition(document, position) {
  const word = document.getWordRangeAtPosition(position, /[A-Za-z_]\w*/);
  if (!word) return undefined;
  const name = document.getText(word).toLowerCase();
  return sourceDefinitions(document).get(name);
}

function provideDocumentFormattingEdits(document, options) {
  let indentation = 0;
  const tab = options.insertSpaces ? " ".repeat(options.tabSize) : "\t";
  const edits = [];
  for (let line = 0; line < document.lineCount; line += 1) {
    const original = document.lineAt(line).text;
    const content = original.trimStart();
    if (!content) {
      if (original) edits.push(vscode.TextEdit.replace(document.lineAt(line).range, ""));
      continue;
    }
    if (BLOCK_END.test(content) || BLOCK_MIDDLE.test(content)) {
      indentation = Math.max(0, indentation - 1);
    }
    const formatted = tab.repeat(indentation) + content;
    if (formatted !== original) {
      edits.push(vscode.TextEdit.replace(document.lineAt(line).range, formatted));
    }
    if (BLOCK_START.test(content) || BLOCK_MIDDLE.test(content)) {
      indentation += 1;
    }
  }
  return edits;
}

function zelixInvocation(context) {
  const config = vscode.workspace.getConfiguration("zelix");
  const configuredScript = config.get("cliPath", "");
  const checkoutScript = path.resolve(context.extensionPath, "..", "zelix.py");
  if (configuredScript) {
    return {
      executable: config.get("pythonPath", "python"),
      prefix: [configuredScript],
    };
  }
  if (fs.existsSync(checkoutScript)) {
    return {
      executable: config.get("pythonPath", "python"),
      prefix: [checkoutScript],
    };
  }
  return { executable: config.get("command", "zelix"), prefix: [] };
}

function createTask(context, workspace, root, action, args) {
  const invocation = zelixInvocation(context);
  const execution = new vscode.ProcessExecution(
    invocation.executable,
    [...invocation.prefix, ...args],
    { cwd: root },
  );
  return new vscode.Task(
    { type: "zelix", action },
    workspace || vscode.TaskScope.Workspace,
    `Zelix: ${action}`,
    "Zelix",
    execution,
    [],
  );
}

function createDocumentTask(context, document, action, args) {
  const workspace = vscode.workspace.getWorkspaceFolder(document.uri);
  const root = workspace ? workspace.uri.fsPath : path.dirname(document.uri.fsPath);
  return createTask(context, workspace, root, action, args);
}

function activeZelixDocument() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "zelix") {
    vscode.window.showWarningMessage("Open a Zelix file to run this command.");
    return undefined;
  }
  return editor.document;
}

function activeProjectWorkspace() {
  const editor = vscode.window.activeTextEditor;
  const workspace = editor
    ? vscode.workspace.getWorkspaceFolder(editor.document.uri)
    : vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
  if (!workspace) {
    vscode.window.showWarningMessage("Open a Zelix project folder to run this command.");
    return undefined;
  }
  return workspace;
}

function sameFilePath(left, right) {
  const first = path.resolve(left);
  const second = path.resolve(right);
  return process.platform === "win32"
    ? first.toLowerCase() === second.toLowerCase()
    : first === second;
}

function activate(context) {
  const diagnostics = vscode.languages.createDiagnosticCollection("zelix");
  const pending = new Map();
  const checkDocument = (document) => {
    if (document.languageId !== "zelix" || document.isClosed) return;
    const key = document.uri.toString();
    const previous = pending.get(key);
    if (previous) {
      clearTimeout(previous.timer);
      if (previous.child) previous.child.kill();
    }
    const entry = { timer: undefined, child: undefined };
    entry.timer = setTimeout(() => {
      const workspace = vscode.workspace.getWorkspaceFolder(document.uri);
      const root = workspace ? workspace.uri.fsPath : path.dirname(document.uri.fsPath);
      const invocation = zelixInvocation(context);
      let output = "";
      let errorOutput = "";
      const child = spawn(
        invocation.executable,
        [
          ...invocation.prefix,
          "--check",
          "--asset-root",
          path.dirname(document.uri.fsPath),
        ],
        { cwd: root, windowsHide: true },
      );
      entry.child = child;
      let spawnFailure = false;
      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk) => { output += chunk; });
      child.stderr.on("data", (chunk) => { errorOutput += chunk; });
      child.stdin.on("error", (error) => {
        if (error.code !== "EPIPE") errorOutput += `\nCould not send source to Zelix validator: ${error.message}`;
      });
      child.on("error", (error) => {
        if (pending.get(key) !== entry || document.isClosed) return;
        spawnFailure = true;
        const message = `Unable to run Zelix validation with '${invocation.executable}': ${error.message}. Install the Zelix CLI or configure zelix.command and zelix.pythonPath.`;
        diagnostics.set(document.uri, [
          new vscode.Diagnostic(
            new vscode.Range(0, 0, 0, Math.max(1, document.lineAt(0).text.length)),
            message,
            vscode.DiagnosticSeverity.Warning,
          ),
        ]);
      });
      child.on("close", (code) => {
        if (spawnFailure || pending.get(key) !== entry || document.isClosed) return;
        if (code === 0) {
          diagnostics.delete(document.uri);
          return;
        }
        const message = `${errorOutput}${output}`.trim();
        const match = /Line\s+(\d+):\s*([\s\S]*)/i.exec(message);
        const line = match ? Math.min(Number(match[1]) - 1, document.lineCount - 1) : 0;
        const range = new vscode.Range(line, 0, line, document.lineAt(line).text.length);
        diagnostics.set(document.uri, [
          new vscode.Diagnostic(
            range,
            match ? match[2].trim() : (message || "Zelix validation failed"),
            vscode.DiagnosticSeverity.Error,
          ),
        ]);
      });
      child.stdin.end(document.getText());
    }, 250);
    pending.set(key, entry);
  };

  context.subscriptions.push(
    diagnostics,
    vscode.debug.registerDebugConfigurationProvider("zelix", {
      resolveDebugConfiguration(_folder, configuration) {
        const editor = vscode.window.activeTextEditor;
        const program = configuration.program
          || (editor && editor.document.languageId === "zelix" ? editor.document.uri.fsPath : undefined);
        if (!program) {
          vscode.window.showErrorMessage("Open a Zelix file or set 'program' in the debug configuration.");
          return undefined;
        }
        return {
          type: "zelix",
          request: "launch",
          name: "Debug Zelix File",
          stopOnEntry: true,
          ...configuration,
          program,
        };
      },
      async resolveDebugConfigurationWithSubstitutedVariables(folder, configuration) {
        let program = configuration.program;
        if (!program) {
          vscode.window.showErrorMessage("Choose a Zelix source file to debug.");
          return undefined;
        }
        program = path.isAbsolute(program)
          ? program
          : path.resolve(folder ? folder.uri.fsPath : process.cwd(), program);
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === "zelix"
          && sameFilePath(editor.document.uri.fsPath, program)) {
          if (!await editor.document.save()) return undefined;
          program = editor.document.uri.fsPath;
        }
        return {
          ...configuration,
          program,
        };
      },
    }),
    vscode.debug.registerDebugAdapterDescriptorFactory("zelix", {
      createDebugAdapterDescriptor() {
        return new vscode.DebugAdapterInlineImplementation(new ZelixDebugAdapter(context));
      },
    }),
    vscode.languages.registerCompletionItemProvider("zelix", { provideCompletionItems }),
    vscode.languages.registerDefinitionProvider("zelix", { provideDefinition }),
    vscode.languages.registerDocumentFormattingEditProvider("zelix", {
      provideDocumentFormattingEdits,
    }),
    vscode.workspace.onDidOpenTextDocument(checkDocument),
    vscode.workspace.onDidChangeTextDocument((event) => checkDocument(event.document)),
    vscode.workspace.onDidCloseTextDocument((document) => {
      const key = document.uri.toString();
      const entry = pending.get(key);
      if (entry) {
        clearTimeout(entry.timer);
        if (entry.child) entry.child.kill();
        pending.delete(key);
      }
      diagnostics.delete(document.uri);
    }),
    vscode.commands.registerCommand("zelix.runCurrentFile", async () => {
      const document = activeZelixDocument();
      if (!document) return;
      await document.save();
      return vscode.tasks.executeTask(createDocumentTask(
        context, document, "Run current file", [document.uri.fsPath],
      ));
    }),
    vscode.commands.registerCommand("zelix.debugCurrentFile", async () => {
      const document = activeZelixDocument();
      if (!document) return;
      await document.save();
      const workspace = vscode.workspace.getWorkspaceFolder(document.uri);
      return vscode.debug.startDebugging(workspace, {
        type: "zelix",
        request: "launch",
        name: "Debug Zelix File",
        program: document.uri.fsPath,
        stopOnEntry: true,
      });
    }),
    vscode.commands.registerCommand("zelix.compileCurrentFile", async () => {
      const document = activeZelixDocument();
      if (!document) return;
      await document.save();
      return vscode.tasks.executeTask(createDocumentTask(
        context, document,
        "Compile current file",
        ["--compile", document.uri.fsPath],
      ));
    }),
    vscode.commands.registerCommand("zelix.showOptimizedIR", async () => {
      const document = activeZelixDocument();
      if (!document) return;
      await document.save();
      return vscode.tasks.executeTask(createDocumentTask(
        context, document,
        "Show optimized IR",
        ["--emit-ir", document.uri.fsPath],
      ));
    }),
    vscode.commands.registerCommand("zelix.initProject", async () => {
      const workspace = activeProjectWorkspace();
      if (!workspace) return;
      return vscode.tasks.executeTask(createTask(
        context, workspace, workspace.uri.fsPath,
        "Initialize project", ["init", workspace.uri.fsPath],
      ));
    }),
    vscode.commands.registerCommand("zelix.installPackages", async () => {
      const workspace = activeProjectWorkspace();
      if (!workspace) return;
      return vscode.tasks.executeTask(createTask(
        context, workspace, workspace.uri.fsPath,
        "Install local packages", ["install", workspace.uri.fsPath],
      ));
    }),
  );

  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 10);
  status.text = "$(play) Zelix";
  status.tooltip = "Run current Zelix file";
  status.command = "zelix.runCurrentFile";
  context.subscriptions.push(status, vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (editor && editor.document.languageId === "zelix") status.show();
    else status.hide();
  }));
  if (vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.languageId === "zelix") {
    status.show();
  }
  for (const document of vscode.workspace.textDocuments) checkDocument(document);
  context.subscriptions.push({
    dispose() {
      for (const entry of pending.values()) {
        clearTimeout(entry.timer);
        if (entry.child) entry.child.kill();
      }
      pending.clear();
    },
  });
}

function deactivate() {}

module.exports = { activate, deactivate };
