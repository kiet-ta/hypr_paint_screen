# Whiteboard Overlay

Transparent full-screen whiteboard overlay for Hyprland/Wayland. Draw and write text on top of any screen — perfect for teaching via Zoom/Meet screen share.

## Requirements

- Arch Linux + Hyprland (Wayland)
- `gtk3`, `gtk-layer-shell`, `python-gobject`, `cairo` (all pre-installed)

## Run

```bash
./run.sh
# or
python3 whiteboard.py
```

## Features

| Tool | Description |
|------|-------------|
| ✏️ Pen | Freehand drawing |
| 🧹 Eraser | Erase strokes |
| ⌨️ Text | Click to place text, type, Enter to commit |
| ● Colors | Black, Red, Blue, Yellow, White |
| ↶ ↷ | Undo / Redo |
| 🗑️ | Clear all |
| 👁️ | Toggle click-through (draw vs interact with desktop) |

## Shortcuts

| Key | Action |
|-----|--------|
| `1`-`5` | Switch color (Black/Red/Blue/Yellow/White) |
| `P` | Pen tool |
| `E` | Eraser tool |
| `T` | Text tool |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+H` | Toggle click-through |
| `Ctrl+Q` | Quit |
| `Enter` | Commit text |
| `Esc` | Cancel text |
# hypr_paint_screen
