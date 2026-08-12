# Whiteboard Overlay v2.0

Transparent full-screen whiteboard overlay for Hyprland/Wayland. Draw, type text, add geometric shapes, and export drawings — perfect for teaching, code reviews, and presentations via Zoom/Meet.

## Features in v2.0

| Tool | Icon / Key | Description |
|------|------------|-------------|
| ✏️ Pen | `P` | Freehand drawing |
| 🧹 Eraser | `E` | Erase strokes |
| ⌨️ Text | `T` | Click to place text, type, Enter to commit |
| 🔲 Rectangle | `R` | Click & drag to draw boxes |
| ⚪ Circle | `C` | Click & drag to draw circles / ellipses |
| ➔ Arrow | `A` | Click & drag to draw directional arrows |
| ● Colors | `1`-`5` | Black, Red, Blue, Yellow, White |
| 📏 Thickness | `6`-`9` | Adjust stroke size (2px, 4px, 8px, 14px) |
| 🔤 Text Style | Toolbar | Cycle Font Family (Sans / Serif / Mono) & Size (18pt, 24pt, 32pt) |
| 💾 Export PNG | `Ctrl+S` | Save whiteboard drawing to `~/Pictures/whiteboard_<timestamp>.png` |
| ↶ ↷ | `Ctrl+Z` / `Ctrl+Y` | Undo / Redo |
| 🗑️ Clear | Toolbar | Clear all strokes |
| 👁️ Passthrough | `Space` / `Ctrl+H` | Toggle between Drawing vs Click-Through desktop |

## Shortcuts Quick Reference

| Key | Action |
|-----|--------|
| `1`-`5` | Select Color |
| `6`-`9` | Select Stroke Thickness (2px / 4px / 8px / 14px) |
| `P` / `E` / `T` | Pen / Eraser / Text Tool |
| `R` / `C` / `A` | Rectangle / Circle / Arrow Shape Tool |
| `Space` / `Ctrl+H` | Toggle Click-Through vs Drawing Mode |
| `Ctrl+Z` / `Ctrl+Y` | Undo / Redo |
| `Ctrl+S` | Export PNG Image |
| `Ctrl+Q` | Quit Overlay |
| `Enter` | Commit text |
| `Esc` | Cancel text |

## Passthrough (Click-Through) Mode

`Space` switches the overlay into click-through mode: the canvas stops intercepting
the pointer, and the overlay **releases its keyboard grab** so the app underneath
receives your typing normally. Only the floating toolbar stays interactive.

Because the overlay no longer receives key events in this mode, `Space` cannot bring
you back. There are two ways out:

1. Click the amber **`Pass`** badge in the toolbar.
2. Send `SIGUSR1` — bind this in `~/.config/hypr/hyprland.conf` for a true global toggle:

```ini
bind = SUPER, W, exec, pkill -USR1 -f whiteboard.py
```

## Run

```bash
./run.sh
# or from Wofi launcher: type "Whiteboard Overlay"
```
