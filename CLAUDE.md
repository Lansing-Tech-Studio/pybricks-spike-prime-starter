# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A starter repository FIRST LEGO League teams fork to write Pybricks programs for LEGO SPIKE Prime robots. The audience is kids and coaches who are beginner programmers — keep code simple, flat, and heavily commented. Code does **not** run on the host machine — it is uploaded to the hub over BLE and runs there on Pybricks's MicroPython port. Most of the standard library is unavailable on the hub.

## Running code on the robot

Code is uploaded and run via `pybricksdev` (wrapped by `.vscode/run_pybricks.py`, which terminates the debug session cleanly when the program on the hub exits). Use the VS Code debug configurations:

- **Pybricks: Run on Robot** — runs the currently open file on the robot named in `.vscode/settings.json` (`pybricks.robotName`).
- **Pybricks: Run on Robot (Select)** — prompts to pick from a list in `.vscode/launch.json` (teams edit this to match their hubs).

From the CLI, the equivalent is `python -m pybricksdev run --name <RobotName> ble <file.py>`. The hub must be on and in range; `pybricksdev` connects via BLE. `pybricksdev run` bundles sibling-module imports (e.g. `robot`, `menu`, `pix_display`) into the upload, which is why the flat single-directory layout matters.

There are no tests, build step, or lint config wired up. `black` is in `requirements.txt` for manual formatting.

## Architecture

### `robot.py` — single source of truth for hardware config
The only file teams edit when their robot's build changes. An "EDIT THIS SECTION" banner at the top holds constants: wheel ports/directions, `WHEEL_DIAMETER_MM`, `AXLE_TRACK_MM`, attachment motor ports, sensor ports, `USE_GYRO`. Optional hardware uses `None` (some teams have one attachment motor and no sensors). The `Robot` class constructs `hub`, wheel motors, a `DriveBase` (with `use_gyro`), and sets each optional attribute (`attachment_1`, `attachment_2`, `color_sensor`, `distance_sensor`, `force_sensor`) to a device or `None`. Also exports `inches(n)` — Pybricks uses mm, FLL mats are measured in inches. Hardware is deliberately constructed in `Robot.__init__`, not at import time, so a missing motor fails at a clear call site.

### Mission files — `mission_NN_<name>.py`
Every mission has the same shape: a module docstring, `def run(robot):` with the moves, and an `if __name__ == "__main__": run(Robot())` block so it is standalone-runnable (open the file, press F5). The `NN` in the filename matches the `display` given in `menu_config.py` — the number shown on the hub's display. `mission_template.py` is the copy-me skeleton and is intentionally not listed in the menu.

### `menu_config.py` — the menu contract (team-owned; extension-regenerated)
The single source of truth for what appears in the hub menu. File = optional docstring/comments + an optional **bundle-hint block** + exactly one top-level `MENU_ITEMS = [<dict literals>]`. Values are limited to int/str/bool/None/list-of-str so it is machine-parseable (`ast.literal_eval` semantics) — the Pybricks Git extension's menu-manager rewrites the whole file from its own template in a later phase, so **comments inside the `MENU_ITEMS` list are not preserved**. Per-slot schema:

- `display` (required): int `0`–`99`, single-char str, or list of exactly 5 pattern strings (same semantics as `pix_display`).
- `module` (required): bare module name, no `.py`, no dots.
- `function` (optional): absent/`None` = whole-program item.
- `blocks` (optional, default `False`): the function is a My Block from a block file.
- `enabled` (optional, default `True`): disabled items are skipped at load but kept in the file.
- List order = menu order.

**Bundle hints (required for every listed module).** `main.py` reaches missions via `__import__(name)` with a *string* from `MENU_ITEMS`, and both `pybricksdev` bundlers resolve dependencies statically (v1.1: CPython `modulefinder`; v2.x: `IMPORT_NAME` opcodes via mpy-tool), as does code.pybricks.com. A module named only as a string is never uploaded → `ImportError: no module named ...` on CENTER. So `menu_config.py` carries, between the docstring and `MENU_ITEMS`:

```python
_BUNDLE_HINTS = False
if _BUNDLE_HINTS:
    import mission_01_go_out_and_turn
```

The guard **must** be a runtime name lookup — `if False:`/`if 0:` is folded away by both the CPython peephole optimizer and mpy-cross, emitting no `IMPORT_NAME` and bundling nothing. Imports stay guarded (never bare) because importing a whole-program item *runs* it and a `blocks: True` module runs its device setup. The extension's menu-manager must emit this block when it regenerates the file; older versions drop it.

Three item kinds:
1. **Plain function item** — `function` set, `blocks` absent/False. Called as `fn(robot)` (the existing convention).
2. **Whole-program item** — no `function`. Importing the module *runs it* (the official `hub_menu` pattern); works for a Python file or a block program.
3. **My Block item** — `function` set, `blocks: True`. Called with no args; if the result has a `.send` attribute (a coroutine) it is driven with `run_task`, otherwise the return value is the result.

### `main.py` — thin loader over `menu_config.py`
No longer hand-registers missions. It reads `MENU_ITEMS`, builds a `Menu`, and wraps each entry in a runner:

- `_import_fresh(name)`: `del sys.modules[name]` (guarded) before `__import__`, so **whole-program items are re-runnable** — including after a CENTER interrupt leaves a partially-executed module cached. Whole-program items import fresh on every run.
- Function items (kinds 1 and 3) **import once and stay cached** — the module's top-level device setup runs a single time, not per menu press.
- `_make_runner(item)` dispatches the three call shapes above.
- **Lazy `Robot()`**: the shared `Robot` is only constructed if some enabled item is a plain (non-blocks) function item. An **all-blocks** menu never constructs `Robot()`, so it never claims ports via `robot.py` defaults (block modules bring their own setup).
- Broken/malformed config entries print a skip message and the rest of the menu still loads; zero valid items falls through to `Menu`'s existing `?` display.
- Still calls `menu.run(auto_increment=True)` (advance to the next slot after each run — match-friendly).

### `menu.py` — `Menu` class
Hub-side menu shell that lets the user pick and run one of several functions via the hub's buttons. Key conventions enforced by this class:

- **Stop-button swap**: while the menu is showing, the system stop button is set to `Button.BLUETOOTH` so `CENTER` is free to mean "select". When a menu item runs, the stop button is moved to `CENTER` so the user can interrupt it; on exit it is restored to `BLUETOOTH`. Anything that calls `hub.system.set_stop_button` inside a menu item will fight this and must restore it.
- **Interrupt is a `SystemExit`**: pressing the (current) stop button raises `SystemExit` inside the running item. `_execute_current_function` catches this, beeps the speaker for 1ms to silence any in-progress beep, and returns to the menu. Other exceptions blink red and re-raise.
- Menu item `function` callables receive the menu's `context` as their only argument (the `Robot` in this repo); if no context was given, the `hub` is passed instead.
- `display` accepts `int` (0–99), single-character `str`, or a 5-row list-of-strings pattern; rendering is delegated to `pix_display.display_content`.

**Functionally unchanged by the loader rework** — only docstrings updated. The callables `main.py` registers are now runner closures that may wrap a fresh import (whole-program items) or an async `run_task` call (My Block items), but from `Menu`'s side they are still ordinary functions run under the CENTER stop button, so the existing stop-button swap / `SystemExit` / `auto_increment` behavior applies unchanged.

### `pix_display.py` — 5×5 light-matrix rendering
Helpers for drawing on the hub's 5×5 display.

- `display_pattern(hub, pattern)`: `pattern` is exactly 5 strings of length 5. `' '` or `'0'` = off; digits `'1'`–`'9'` = brightness × 10; anything else = 100.
- `display_number(hub, n)` for 0–99: 0–9 use the built-in single-char glyph, 10–19 use hand-drawn patterns from `Patterns.numbers`, 20+ use the built-in scrolling number renderer.
- `Patterns.numbers` only goes up to index 19 — do not index past it.

### `.pybricks-git.json` — repo manifest read by the extension
Repo-root JSON, read by the Pybricks Git extension **from the git tree**, never synced into the editor (the extension's `.py`-only filter keeps it out; it's protected so it can't be clobbered). `schemaVersion` gates parsing; unknown keys are ignored. Keys: `menuConfig` (`menu_config.py`), `setupTemplate` (`robot_setup_template.py`), `teamSetup` (`robot_setup.py`), and `protected` — a list of framework paths. **Protected** means: on commit the extension keeps the git tree's version and drops the editor's edits (reporting a skip), and on pull it restores those files — a git-layer guard only, no in-editor enforcement. `robot.py`, `menu_config.py`, sample missions, and the team's `robot_setup.py` are intentionally NOT protected.

## Block programs (blocks files)

A block program authored at code.pybricks.com is saved as a `.py` file whose **line 1 is a `# pybricks blocks file:{...workspace JSON...}` sentinel comment** carrying the entire Blockly workspace, with the generated Python below it. Both live in the one file.

- **Treat line 1 as opaque** — never hand-edit, regenerate, or "tidy" the JSON. Round-trip it byte-for-byte. To change a block program, open it at code.pybricks.com.
- **Block files can't import siblings** — a block program is self-contained and cannot `import robot` (or any other module in the repo), so every block program inlines its own device setup. This is why the menu supports whole-program and My Block items that never receive the shared `Robot`.
- **Setup files** are a special block file whose workspace contains **only** the non-deletable `blockGlobalSetup` chain — no main-program blocks, so the generated Python has no `run_task` and no trailing statements. `robot_setup_template.py` (protected, upstream example) and the team's `robot_setup.py` (its editable copy, the future splice source of truth) are setup files. Distinct from setup files: a My Block item (`blocks: True`) points at a block file whose top level is setup-only (device setup plus My Block definitions, **no main-program blocks**) — setup files themselves contain no My Blocks at all.
- **`robot_setup_template.py` must only ever be authored via code.pybricks.com** — line-1 JSON and the generated Python must stay in sync, which hand-editing breaks.

## `check_project.py` — desktop verifier
CPython-only (does **not** run on the hub). `py_compile`s every `.py`; `ast`-parses `menu_config.py` (docstring + optional `_BUNDLE_HINTS` block + a single `MENU_ITEMS` literal assignment, full schema validation, every referenced module file exists; the hint block is skipped by `_strip_bundle_hints`, which still rejects anything but plain `import` lines inside the guard); validates `.pybricks-git.json` (schema + listed files exist); validates setup files (line-1 sentinel present, JSON parses, has `blockGlobalSetup`, no `run_task`). Run it before committing: `python3 check_project.py`.

## Pybricks/MicroPython gotchas

- **`del sys.modules[name]` re-import idiom is unverified on Pybricks firmware.** `main.py` uses it so whole-program items re-run on each menu press; if it misbehaves on-hub the fallback is "whole-program items run once per boot" (or an `exec`-based loader). **Verify on real hardware** when touching the loader.
- **`usys`/`sys` fallback**: import `usys` and fall back to `sys` — Pybricks exposes the module under both names across firmware versions. `main.py`'s `del sys.modules` lookup must use whichever resolved.
- **Coroutine detection is `hasattr(result, "send")`** — how a `blocks: True` My Block's return value is recognized as async on MicroPython (no `inspect.iscoroutine`). Drive it with `run_task`.
- **Double device construction**: if a block module and `Robot()` both claim the same ports in one session, the port is initialized twice. Mitigated by the lazy `Robot()` (an all-blocks menu never builds one); the full fix arrives with the extension's phase-4 setup-splice. Document, don't fight it, for now.

- `from typing import ...` is wrapped in `try/except ImportError` because the hub's MicroPython has no `typing` module at runtime — type hints are for the host-side editor only. Preserve this pattern when adding modules.
- Only import from `pybricks.*`. Standard-library modules beyond what Pybricks ships will `ImportError` on the hub.
- Button polling uses `hub.buttons.pressed()` returning a set; debounce by waiting for release (see `Menu._wait_for_release`) before treating the next press as new.
- `wait(ms)` from `pybricks.tools` is the only sleep — do not use `time.sleep`.
- No `dataclasses`, limited `collections` — plain classes and dicts only.
