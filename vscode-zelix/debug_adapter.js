const { spawn } = require("child_process");
const fs = require("fs");
const readline = require("readline");
const path = require("path");
const vscode = require("vscode");

class ZelixDebugAdapter {
  constructor(context) {
    this.context = context;
    this.emitter = new vscode.EventEmitter();
    this.onDidSendMessage = this.emitter.event;
    this.sequence = 1;
    this.child = undefined;
    this.program = undefined;
    this.breakpoints = new Set();
    this.breakpointPath = undefined;
    this.stopOnEntry = true;
    this.frames = [];
    this.variableScopes = new Map();
    this.nextReference = 1;
    this.exitSent = false;
  }

  send(message) {
    this.emitter.fire({ ...message, seq: this.sequence++ });
  }

  respond(request, body = {}, success = true, message) {
    const response = {
      type: "response",
      request_seq: request.seq,
      command: request.command,
      success,
      body,
    };
    if (message) response.message = message;
    this.send(response);
  }

  event(event, body = {}) {
    this.send({ type: "event", event, body });
  }

  handleMessage(message) {
    if (message.type !== "request") return;
    try {
      this.handleRequest(message);
    } catch (error) {
      this.respond(message, {}, false, error.message);
    }
  }

  handleRequest(request) {
    const args = request.arguments || {};
    switch (request.command) {
      case "initialize":
        this.respond(request, {
          supportsConfigurationDoneRequest: true,
          supportsTerminateRequest: true,
          supportsEvaluateForHovers: true,
          supportsSetVariable: false,
          supportsConditionalBreakpoints: false,
          supportsFunctionBreakpoints: false,
          supportsStepBack: false,
        });
        this.event("initialized");
        return;
      case "launch":
        this.launch(request, args);
        return;
      case "setBreakpoints":
        this.setBreakpoints(request, args);
        return;
      case "configurationDone":
        this.respond(request, {});
        this.sendBreakpoints();
        this.sendCommand({ command: "configure" });
        if (!this.stopOnEntry) {
          this.sendCommand({ command: "resume", mode: "continue", line: 0, depth: 0 });
        }
        return;
      case "setExceptionBreakpoints":
        this.respond(request, {});
        return;
      case "threads":
        this.respond(request, { threads: [{ id: 1, name: "Zelix program" }] });
        return;
      case "stackTrace":
        this.stackTrace(request, args);
        return;
      case "scopes":
        this.scopes(request, args);
        return;
      case "variables":
        this.variables(request, args);
        return;
      case "evaluate":
        this.evaluate(request, args);
        return;
      case "continue":
      case "next":
      case "stepIn":
      case "stepOut":
        this.resume(request, request.command);
        return;
      case "pause":
        this.respond(request, {});
        this.sendCommand({ command: "pause" });
        return;
      case "terminate":
      case "disconnect":
        this.terminate(request);
        return;
      default:
        this.respond(request, {}, false, `Unsupported Zelix debug request: ${request.command}`);
    }
  }

  launch(request, args) {
    const program = args.program && path.resolve(args.program);
    if (!program || path.extname(program).toLowerCase() !== ".zelix") {
      this.respond(request, {}, false, "Choose a .zelix source file to debug.");
      return;
    }
    if (!fs.existsSync(program)) {
      this.respond(request, {}, false, `Zelix source file does not exist: ${program}`);
      return;
    }
    this.program = program;
    this.stopOnEntry = args.stopOnEntry !== false;
    if (this.breakpointPath && !samePath(this.program, this.breakpointPath)) {
      this.breakpoints.clear();
    }
    const config = vscode.workspace.getConfiguration("zelix");
    const configuredScript = config.get("cliPath", "");
    const checkoutScript = path.resolve(this.context.extensionPath, "..", "zelix.py");
    const invocation = configuredScript
      ? { executable: config.get("pythonPath", "python"), prefix: [configuredScript] }
      : fs.existsSync(checkoutScript)
        ? { executable: config.get("pythonPath", "python"), prefix: [checkoutScript] }
        : { executable: config.get("command", "zelix"), prefix: [] };
    this.child = spawn(
      invocation.executable,
      [
        ...invocation.prefix,
        "--debug-server",
        program,
        ...(args.stopOnEntry === false ? ["--debug-no-stop-on-entry"] : []),
      ],
      { cwd: path.dirname(program), windowsHide: true },
    );
    this.child.stdin.on("error", (error) => {
      if (error.code !== "EPIPE") {
        this.event("output", {
          category: "stderr",
          output: `Debugger command channel failed: ${error.message}\n`,
        });
      }
    });
    this.child.on("error", (error) => {
      this.event("output", {
        category: "stderr",
        output: `Unable to start the Zelix debugger: ${error.message}\n`,
      });
      this.event("terminated");
    });
    const lines = readline.createInterface({ input: this.child.stdout });
    lines.on("line", (line) => this.handleRuntimeMessage(line));
    this.child.stderr.setEncoding("utf8");
    this.child.stderr.on("data", (output) => {
      this.event("output", { category: "stderr", output });
    });
    this.child.on("close", (code) => this.finish(code || 0));
    this.respond(request, {});
    this.event("thread", { reason: "started", threadId: 1 });
  }

  setBreakpoints(request, args) {
    const lines = (args.breakpoints || [])
      .map((breakpoint) => breakpoint.line)
      .filter((line) => Number.isInteger(line) && line > 0);
    this.breakpointPath = args.source && args.source.path
      ? path.resolve(args.source.path)
      : this.breakpointPath;
    if (this.program && this.breakpointPath && !samePath(this.program, this.breakpointPath)) {
      this.breakpoints.clear();
      this.respond(request, {
        breakpoints: lines.map((line) => ({ verified: false, line })),
      });
      return;
    }
    this.breakpoints = new Set(lines);
    this.respond(request, {
      breakpoints: lines.map((line) => ({ verified: true, line })),
    });
    this.sendBreakpoints();
  }

  sendBreakpoints() {
    if (!this.child || !this.child.stdin.writable) return;
    this.sendCommand({ command: "breakpoints", lines: [...this.breakpoints] });
  }

  sendCommand(command) {
    if (!this.child || !this.child.stdin.writable) return;
    this.child.stdin.write(`${JSON.stringify(command)}\n`);
  }

  handleRuntimeMessage(line) {
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      this.event("output", { category: "stderr", output: `Invalid debugger output: ${line}\n` });
      return;
    }
    if (message.event === "output") {
      this.event("output", {
        category: message.category || "stdout",
        output: message.output || "",
      });
    } else if (message.event === "stopped") {
      this.frames = message.stack || [];
      this.variableScopes.clear();
      this.nextReference = 1;
      this.event("stopped", {
        reason: message.reason || "step",
        threadId: 1,
        allThreadsStopped: true,
        description: message.reason === "entry" ? "Program entry" : undefined,
      });
    } else if (message.event === "exception") {
      this.event("output", { category: "stderr", output: `${message.message}\n` });
      this.frames = message.stack || this.frames;
      this.event("stopped", {
        reason: "exception",
        threadId: 1,
        allThreadsStopped: true,
        text: message.message,
      });
    } else if (message.event === "error") {
      this.event("output", { category: "stderr", output: `${message.message}\n` });
    } else if (message.event === "terminated") {
      this.finish(message.exitCode || 0);
    }
  }

  stackTrace(request, args) {
    const start = args.startFrame || 0;
    const frames = this.frames.slice(start, start + (args.levels || this.frames.length))
      .map((frame, index) => ({
        id: start + index + 1,
        name: frame.name,
        source: { name: path.basename(this.program), path: this.program },
        line: frame.line,
        column: 1,
      }));
    this.respond(request, { stackFrames: frames, totalFrames: this.frames.length });
  }

  scopes(request, args) {
    const frame = this.frames[args.frameId - 1];
    if (!frame) {
      this.respond(request, {}, false, "The selected stack frame is no longer available.");
      return;
    }
    const reference = this.nextReference++;
    this.variableScopes.set(reference, frame.locals || {});
    this.respond(request, {
      scopes: [{
        name: "Locals",
        variablesReference: reference,
        expensive: false,
      }],
    });
  }

  variables(request, args) {
    const variables = this.variableScopes.get(args.variablesReference);
    if (!variables) {
      this.respond(request, { variables: [] });
      return;
    }
    this.respond(request, {
      variables: Object.entries(variables).map(([name, value]) => ({
        name,
        value: String(value),
        type: value === null ? "nil" : typeof value,
        variablesReference: 0,
      })),
    });
  }

  evaluate(request, args) {
    const frame = this.frames[args.frameId ? args.frameId - 1 : 0];
    const name = String(args.expression || "").trim().toLowerCase();
    if (frame && Object.prototype.hasOwnProperty.call(frame.locals || {}, name)) {
      const value = frame.locals[name];
      this.respond(request, {
        result: String(value),
        type: value === null ? "nil" : typeof value,
        variablesReference: 0,
      });
    } else {
      this.respond(request, {}, false, `Unknown Zelix variable: ${args.expression}`);
    }
  }

  resume(request, mode) {
    const frame = this.frames[0];
    this.respond(request, mode === "continue" ? { allThreadsContinued: true } : {});
    this.sendCommand({
      command: "resume",
      mode,
      line: frame ? frame.line : 0,
      depth: Math.max(0, this.frames.length - 1),
    });
  }

  terminate(request) {
    this.respond(request, {});
    this.sendCommand({ command: "terminate" });
    if (this.child && !this.child.killed) {
      const child = this.child;
      setTimeout(() => {
        if (child.exitCode === null) child.kill();
      }, 1000);
    }
  }

  finish(code) {
    if (this.exitSent) return;
    this.exitSent = true;
    this.event("exited", { exitCode: code });
    this.event("terminated");
  }

  dispose() {
    if (this.child && this.child.exitCode === null) {
      this.sendCommand({ command: "terminate" });
      this.child.kill();
    }
    this.emitter.dispose();
  }
}

function samePath(left, right) {
  const first = path.resolve(left);
  const second = path.resolve(right);
  return process.platform === "win32"
    ? first.toLowerCase() === second.toLowerCase()
    : first === second;
}

module.exports = { ZelixDebugAdapter };
