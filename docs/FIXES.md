# Whiteboard Overlay — Bug Fixes & UI Enhancements

## 1. Text Input Fix ("không gõ chữ được")
- **Root Cause**: Previously, when the TEXT tool was activated (`text_active = True`), `Canvas.on_draw()` only rendered completed strokes and a static cursor line. The live buffer (`self.app.text_buffer`) was never rendered during the `draw` call while typing. It only got rendered after `commit_text()` was called. Additionally, the cursor line position did not advance with typed characters.
- **Solution**:
  1. Updated `Canvas.on_draw()` to render `self.app.text_buffer` in real-time at `self.app.text_pos`.
  2. Used Cairo `cr.text_extents(text_buffer)` to compute text width dynamically so the cursor bar moves to the end of the typed text.
  3. Ensured `Canvas` and `Gtk.Window` grab keyboard focus on click (`grab_focus()`), handling Backspace, Enter, Esc, and full Unicode text entry.

## 2. Passthrough & Mode Switching Fix ("Space / Click-Through")
- **Root Cause**: The previous implementation attempted to invoke `hyprctl keyword layerrule "noinput..."` which failed on modern Hyprland versions (`keyword can't work with non-legacy parsers`). Moreover, setting full `noinput` on the Wayland layer surface stripped all input events from the GTK window, causing `on_key` to miss `Space` keypresses during passthrough mode.
- **Solution**:
  1. Replaced broken `hyprctl` subprocess calls with native GDK/Cairo `input_shape_combine_region`.
  2. **Passthrough Mode (`draw_mode = True`)**: Restricts the GTK input shape region exclusively to the toolbar container (`self.bar.get_allocation()`). The drawing canvas area becomes 100% click-through to underlying desktop windows (browser, IDE, Zoom, etc.), while the toolbar remains interactive.
  3. **Keyboard Interactivity**: Switched `GtkLayerShell.set_keyboard_mode` to `KeyboardMode.NONE` during passthrough mode so active desktop apps receive keyboard focus seamlessly, and `KeyboardMode.EXCLUSIVE` during drawing mode for whiteboard shortcuts and text entry.

## 2b. Regression: Click-Through Could Not Type Into Apps Underneath

- **Symptom**: `Space` visibly flipped the badge to `Pass` and mouse clicks passed through
  to the desktop, but keyboard input never reached the app underneath — typing was
  swallowed by the overlay.
- **Root Cause**: Commit `62f17f3` wrapped both `GtkLayerShell.set_keyboard_mode` calls in
  `if HAS_LAYER_SHELL and GtkLayerShell:` — but **`HAS_LAYER_SHELL` was never defined**
  anywhere in the module. `update_input()` therefore raised `NameError` immediately after
  applying the pointer input-shape. Because `update_input()` is reached from GTK signal
  handlers, PyGObject printed the traceback and swallowed it, so the app kept running with:
  - pointer region correctly shrunk to the toolbar (mouse passthrough *appeared* to work), but
  - `KeyboardMode.EXCLUSIVE` still in force — the overlay never released its keyboard grab.
- **Solution**:
  1. Defined `HAS_LAYER_SHELL` via a guarded `try/except` import (the intent of the original
     commit), with `GtkLayerShell = None` and an `X11 fullscreen` fallback so headless CI
     still imports the module.
  2. Extracted `App._set_keyboard_mode()`, which applies the mode **and calls
     `Gdk.Display.flush()`** — without the flush the `wl_surface` commit is deferred to the
     next frame and the grab lingers.
  3. In passthrough, the keyboard grab is now released *before* the pointer region shrinks,
     and `self.win.set_focus(None)` drops GTK's internal focus so the canvas stops claiming
     key events.
  4. Renamed the inverted `draw_mode` flag to `passthrough` (`draw_mode = True` meaning
     "not drawing" is what made this area error-prone in the first place).

## 2c. Returning From Passthrough + Broken Redo

- **Passthrough is a one-way trip for the keyboard**: once the grab is correctly released, the
  overlay receives no key events, so `Space` cannot toggle back. Added a `SIGUSR1` handler
  (`App._on_signal_toggle`) so a compositor keybind works as a global toggle:
  `bind = SUPER, W, exec, pkill -USR1 -f whiteboard.py`. The toolbar `Pass` badge remains
  clickable as the no-config fallback, and a toast now states the way back.
- **Redo was dead code**: `self.redo = []` in `App.__init__` shadowed the `redo()` method, so
  the Redo button and `Ctrl+Y` raised `TypeError: 'list' object is not callable`. The list is
  now `self.redo_stack`.

## 3. UI Design Overhaul (Taste-Skill Integration)
- Integrated modern UI design principles from `taste-skill` anti-slop guidelines:
  - Frosted glassmorphism dark toolbar (`#0f111a` with 88% opacity, blur, soft borders, and inner shadow).
  - High-contrast visual indicators: Glowing emerald badge for **Drawing Mode** (`#34d399`) and warm amber badge for **Click-Through** mode (`#fbbf24`).
  - Tactile button states with hover feedback, blue highlight rings for active tools, and scale animations on color swatches.
