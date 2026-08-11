# Whiteboard Overlay — Bug Fix Plan

## Project
`/home/tak/openclaw/projects/whiteboard-overlay/whiteboard.py`

GTK3 + GtkLayerShell + Cairo whiteboard overlay for Hyprland/Wayland.

## Bugs to Fix

### Bug 1: Text input doesn't work
**Symptom:** Select TEXT tool → click on canvas → type characters → nothing appears.
**Root cause analysis:**
- The `on_key` handler is on `self.win` (Gtk.Window). With `GtkLayerShell.KeyboardMode.EXCLUSIVE`, the window should receive key events.
- When TEXT tool is selected and user clicks canvas, `on_press` sets `text_active = True` and `text_pos`.
- The `on_key` handler checks `if self.text_active:` at the bottom and converts keyval to unicode. This should work IN THEORY.
- **Possible issue:** The `on_key` handler has an early return for `kv == Gdk.KEY_space and not self.text_active` — but space when text IS active falls through correctly. However, the check `if not ctrl and not self.text_active:` block runs BEFORE the text input block. If a key like 'a' is pressed while `text_active`, it matches `kv == Gdk.keyval_from_name('a')` in the tool shortcuts? No — the shortcut loop only checks 'p','P','e','E','t','T'. So 'a' would not match and would fall through. This seems OK.
- **Real issue might be:** The key event might not reach the window. Or `text_active` might get reset. Need to add focus grab.
- **Fix:** After setting `text_active = True` in `on_press`, call `self.win.grab_focus()` and ensure the window has keyboard focus. Also make the canvas `set_can_default(True)` and `grab_focus()`.

### Bug 2: Click-through doesn't work
**Symptom:** Toggle to passthrough mode → clicks still don't pass through to underlying windows.
**Root cause:** `update_input()` uses `hyprctl eval` to run Lua code containing `layerrule = "noinput, ..."`. But `layerrule` is a Hyprland config keyword, NOT a Lua function. `hyprctl eval` runs Lua code, and `layerrule` is not valid Lua.
**Fix:** Use `hyprctl keyword layerrule "noinput, match:namespace whiteboard-overlay"` to add the rule, and `hyprctl keyword layerrule "unset, match:namespace whiteboard-overlay"` to remove it. Since `keyword` adds rules cumulatively, always `unset` first before adding.

## Requirements
- Only modify `/home/tak/openclaw/projects/whiteboard-overlay/whiteboard.py`
- Keep all existing functionality working (pen, eraser, undo/redo, clear, colors, toolbar)
- Write output/notes to `docs/` folder
- Verify syntax with: `python3 -c "import py_compile; py_compile.compile('whiteboard.py', doraise=True)"`

## Environment
- OS: Arch Linux, Hyprland 0.55+ (Lua config)
- `hyprctl keyword <name> <value>` is available for dynamic config
- Python 3, GTK3, GtkLayerShell, pycairo installed
