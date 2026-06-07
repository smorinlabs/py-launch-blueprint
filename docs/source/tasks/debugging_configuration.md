# Debugging Configuration Guide

This guide helps you set up and run debugging sessions across common editors.

## General Debugging Steps

1. Open your project folder in your editor.
2. Open the Debug panel:

   * VS Code: Use the **Run & Debug** tab.
   * Cursor: Search for "Debug: Select and Start Debugging".
   * Windsurf: Use the debug view.
3. Choose a configuration:

   * `Python: Launch Main`
   * `Python: Launch Main (With Args)`
4. Add breakpoints by clicking to the left of line numbers.
5. Start the debugger.

---

## VS Code

VS Code uses the `.vscode/launch.json` file.

### Launching

Open the **Run & Debug** panel and select one of the configurations:

```json
"configurations": [
  {
    "name": "Python: Launch Main",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/py_launch_blueprint/projects.py"
  },
  {
    "name": "Python: Launch Main (With Args)",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/py_launch_blueprint/projects.py",
    "args": ["--workspace", "test", "--limit", "10"]
  }
]
```

Set breakpoints and start debugging using the green ▶️ button or `F5`.

---

## Cursor

Cursor uses the same `.vscode/launch.json` format.

### Steps

1. Open the project.
2. Open the command palette and run `Debug: Select and Start Debugging`.
3. Pick a configuration.
4. Add breakpoints and start debugging.

---

## Windsurf

Windsurf also supports `.vscode/launch.json`.

### Steps

1. Open your project.
2. Go to the debug view.
3. Select a launch configuration.
4. Place breakpoints.
5. Start debugging.

---

For more help, see the documentation of each editor:
