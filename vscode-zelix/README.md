# Zelix Language Support

Zelix Language Support brings the Zelix programming language and project workflow into Visual Studio Code.

## Features

- Syntax highlighting for Zelix programs and Raylib game APIs.
- Interpreter-backed debugging with breakpoints, Continue, Step Over, Step Into, Step Out, call stacks, local variables, and program output.
- Keyword, function, variable, and game API completions.
- Live diagnostics from the Zelix CLI as you edit.
- Document formatting and go-to-definition for local functions, variables, parameters, and loop variables.
- Commands and tasks to run a program, compile a native executable, inspect optimized IR, initialize a Zelix project, and lock local path dependencies.
- A Zelix debugger with breakpoints, step controls, call stacks, local variables, and program output.
- Snippets for common language constructs, 2D/3D drawing, scenes, physics, and UDP messaging.
- A Zelix file icon theme.

Native compiler commands need a C compiler. Raylib game programs additionally need Raylib 5.0+ headers and libraries.

## Install the extension

In VS Code, search the Extensions view for **Zelix Language** by publisher **CloudZ**, or install `CloudZ.zelix-language`.

## Install Zelix

Install the Zelix CLI from a Zelix source checkout's repository root using Python 3.10 or later:

```shell
python -m pip install .
```

The extension uses the installed `zelix` command automatically. The CLI must be installed separately from the Marketplace extension. To use a development checkout instead, open the repository in VS Code. Alternatively, set `zelix.cliPath` to `zelix.py` and `zelix.pythonPath` to the Python executable that runs it. If the CLI is installed under a non-standard executable name, set `zelix.command`.

## Start a project

1. Open a workspace folder in VS Code.
2. Run **Zelix: Initialize Project** from the Command Palette, or in a terminal run `zelix init .`.
3. Use **Zelix: Run Current File** on `src/main.zelix`.
4. Declare local packages in `zelix.toml`, then run **Zelix: Install Local Packages** to update `zelix.lock`.
5. Use **Zelix: Compile Current File** when you have a native compiler installed.
6. Use **Zelix: Debug Current File** or press F5 to set breakpoints and step through the active file.

The debugger pauses at the first executable statement by default. Use Continue, Step Over, Step Into, and Step Out in VS Code's Debug toolbar. Debugging uses the installed Zelix CLI or the configured source checkout, so the CLI must be updated to a version that includes debugger support. Interactive Zelix `input` statements are not supported in a debug session; run the program normally to provide console input.

The repository includes a two-package walkthrough under `examples/project-packages` and `examples/score-tools`. Here is its structure:

```text
game-score/
├── zelix.toml
└── src/main.zelix
score-tools/
├── zelix.toml
└── src/main.zelix
```

In the game project's `zelix.toml`, declare a local dependency:

```toml
[package]
name = "game-score"
version = "0.1.0"
entry = "src/main.zelix"

[dependencies]
score-tools = { path = "../score-tools" }
```

The dependency's manifest names its package and entry file:

```toml
[package]
name = "score-tools"
version = "1.0.0"
entry = "src/main.zelix"
```

Its entry file contains reusable functions:

```zelix
function points_for taking round and points_per_round
    return round times points_per_round
end function
```

Use the function in the app entry, validate the project, and run it:

```zelix
use score-tools

create total as 0
create round_score as 0
repeat with round from 1 to 5
    round_score becomes points_for with round and 10
    total becomes total plus round_score
end loop
display total
```

Run **Zelix: Install Local Packages** (or `zelix install .`) whenever a manifest or dependency entry changes. This writes `zelix.lock`; execution rejects missing or stale lock data. Run **Zelix: Run Current File** to see the result. The repository example adds comments, a target check, and expected project files.

## Debug a Zelix file

Open a `.zelix` file, click in the editor gutter to set a breakpoint, then choose **Zelix: Debug Current File** or press F5. The debugger stops at the first executable statement by default. Use VS Code's Debug toolbar to continue or step through the source, then inspect the call stack and local variables in the Run and Debug view.

To skip the initial pause, add this launch configuration to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "zelix",
      "request": "launch",
      "name": "Debug current Zelix file",
      "program": "${file}",
      "stopOnEntry": false
    }
  ]
}
```

The debugger requires the updated Zelix CLI. Interactive `input text` and `input number` statements are currently unsupported in debug sessions.

## Example

```zelix
function score_for taking rounds and points
    return rounds times points
end function

create score as score_for with 3 and 10
if score is greater than or equal to 30
    display text Excellent work end text
otherwise
    display text Keep practicing end text
end if
```

## Commands

| Command | Purpose |
|---|---|
| Zelix: Run Current File | Run the active `.zelix` file with the interpreter |
| Zelix: Debug Current File | Start a debugger session for the active `.zelix` file |
| Zelix: Compile Current File | Compile the active file to a native executable |
| Zelix: Show Optimized IR | Show the compiler's optimized intermediate representation |
| Zelix: Initialize Project | Create `zelix.toml` and `src/main.zelix` in the workspace |
| Zelix: Install Local Packages | Resolve local path dependencies and update `zelix.lock` |

## Settings

| Setting | Default | Description |
|---|---|---|
| `zelix.command` | `zelix` | Installed CLI command used outside a checkout |
| `zelix.cliPath` | empty | Optional path to `zelix.py` |
| `zelix.pythonPath` | `python` | Python executable used to run `zelix.py` |

Project imports require an up-to-date `zelix.lock`. Package dependencies are local paths only; there is no remote registry or package publisher yet.

## Publishing

The Marketplace publisher ID in the manifest is `CloudZ`. A publisher administrator must configure Marketplace Trusted Publishing for the repository and `.github/workflows/publish-vscode-extension.yml` before the publishing workflow can run. The workflow publishes only when the requested version matches this extension's manifest.

## License

MIT. See [`LICENSE`](LICENSE).
