# 🎨 Whiteboard Overlay for Hyprland / Wayland

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Wayland%20%7C%20Hyprland-brightgreen.svg)](https://hyprland.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![GTK](https://img.shields.io/badge/GTK-3.0-orange.svg)](https://www.gtk.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-red.svg)](#-contributing)

A lightweight, high-performance, transparent full-screen whiteboard overlay designed for **Hyprland** and **Wayland** environments. Draw, erase, and write text annotations directly on top of your screen in real time — ideal for online teaching, Zoom/Teams/Meet presentations, live coding, and quick screen demonstrations.

---

## ✨ Features

- **✏️ Freehand Pen Tool**: Smooth vector-style drawing powered by Cairo graphics.
- **🧹 Eraser Tool**: Precise stroke/area removal using Cairo `DEST_OUT` alpha blending.
- **⌨️ Interactive Text Tool**: Click anywhere on screen to type text directly onto the canvas.
- **👁️ Dynamic Click-Through (Passthrough)**: Seamlessly switch between drawing mode and desktop passthrough mode with a single keypress (`Space`), utilizing Hyprland dynamic layer rules (`hyprctl`).
- **🎨 5 Presets Palette**: Quick color swatches (Black, Red, Blue, Yellow, White).
- **↶ ↷ History Management**: Full Undo (`Ctrl+Z`) and Redo (`Ctrl+Y`) stack.
- **🗑️ Canvas Clearing**: Instantly clear all annotations with a single click.
- **🪟 Native Wayland Layer**: Built on GTK3 and `GtkLayerShell` for native performance without visual artifacts or heavy Xwayland overhead.

---

## 🖥️ Preview & Interface

| Tool / Action | Icon / Shortcut | Description |
| :--- | :---: | :--- |
| **Pen Tool** | ✏️ (`P`) | Freehand drawing with custom stroke width |
| **Eraser Tool** | 🧹 (`E`) | Erase drawings seamlessly |
| **Text Tool** | ⌨️ (`T`) | Click to place cursor, type text, press `Enter` to commit |
| **Colors** | ● (`1`-`5`) | Switch between 5 vibrant colors |
| **Undo / Redo** | ↶ ↷ (`Ctrl+Z` / `Ctrl+Y`) | Step backward or forward through stroke history |
| **Clear All** | 🗑️ | Wipe the screen clean |
| **Passthrough Toggle** | 👁️ (`Space`) | Toggle between drawing mode and clicking through to background windows |
| **Quit** | ❌ (`Ctrl+Q`) | Exit overlay application |

---

## ⚙️ Prerequisites & System Requirements

### Platform Requirements
- **OS**: Linux (Arch Linux, Fedora, Ubuntu, Debian, etc.)
- **Compositor**: [Hyprland](https://hyprland.org/) (Wayland compositor supporting layer rules)

### System Dependencies
Ensure the following packages are installed on your system:

#### Arch Linux
```bash
sudo pacman -S python gtk3 gtk-layer-shell python-gobject python-cairo
```

#### Fedora
```bash
sudo dnf install python3 gtk3 gtk-layer-shell python3-gobject python3-cairo
```

#### Ubuntu / Debian
```bash
sudo apt update
sudo apt install python3 libgtk-3-dev libgtk-layer-shell-dev python3-gi python3-cairo
```

---

## 🚀 Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/kiet-ta/hypr_paint_screen.git
   cd hypr_paint_screen
   ```

2. **Make the Launch Script Executable**:
   ```bash
   chmod +x run.sh
   ```

3. **Launch the Overlay**:
   ```bash
   ./run.sh
   ```
   *Or launch directly via Python:*
   ```bash
   python3 whiteboard.py
   ```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Space` | Toggle drawing vs. desktop click-through mode |
| `P` | Activate Pen tool |
| `E` | Activate Eraser tool |
| `T` | Activate Text tool |
| `1` - `5` | Quick select color (1: Black, 2: Red, 3: Blue, 4: Yellow, 5: White) |
| `Ctrl + Z` | Undo last stroke |
| `Ctrl + Y` | Redo stroke |
| `Enter` | Commit text entry |
| `Esc` | Cancel / Commit active text entry |
| `Ctrl + Q` | Exit application |

---

## 💡 Hyprland Configuration Tip

To launch Whiteboard Overlay with a keybinding directly in your Hyprland configuration (`~/.config/hypr/hyprland.conf`), add:

```ini
# Toggle Whiteboard Overlay with Super + Shift + W
bind = SUPER SHIFT, W, exec, /path/to/whiteboard-overlay/run.sh
```

---

## 🤝 Contributing

We welcome contributions from the open-source community! Whether you are fixing bugs, improving documentation, or proposing new features, your help is greatly appreciated.

### How to Contribute

1. **Fork the Repository** on GitHub.
2. **Clone your Fork**:
   ```bash
   git clone https://github.com/kiet-ta/hypr_paint_screen.git
   cd hypr_paint_screen
   ```
3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/amazing-new-feature
   ```
4. **Test your Changes**:
   Verify python syntax and test the application on Hyprland:
   ```bash
   python3 -c "import py_compile; py_compile.compile('whiteboard.py', doraise=True)"
   ./run.sh
   ```
5. **Commit your Changes**:
   ```bash
   git commit -m "feat: add amazing new feature"
   ```
6. **Push to your Branch**:
   ```bash
   git push origin feature/amazing-new-feature
   ```
7. **Open a Pull Request**: Submit a PR to the `main` branch with a clear summary of your changes.

Read our [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 📄 License

This project is open source and available under the **[MIT License](LICENSE)**. Feel free to modify, distribute, and use it in your own projects!

---

## 🙏 Acknowledgments

- [Hyprland](https://hyprland.org/) — Wayland compositor providing dynamic layer rules.
- [GtkLayerShell](https://github.com/wmww/gtk-layer-shell) — Library for Wayland desktop components using GTK.
- [PyCairo / Cairo](https://www.cairographics.org/) — 2D graphics library for high-quality rendering.
