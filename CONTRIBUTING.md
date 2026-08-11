# Contributing to Whiteboard Overlay

First off, thank you for considering contributing to **Whiteboard Overlay**! It's people like you that make open source such an amazing place to learn, inspire, and create.

---

## 🚀 How Can I Contribute?

### Reporting Bugs
Before creating bug reports, please check existing issues. When creating a bug report, please include as many details as possible:
- **Use a clear and descriptive title**.
- **Describe the exact steps** to reproduce the problem.
- **Provide specific examples** or screenshots to demonstrate the steps.
- **Describe the behavior you observed** after following the steps and point out what exactly was wrong.
- **Environment details**: Your Linux distro, Hyprland version, Python version.

### Suggesting Enhancements
Feature requests are always welcome! Please provide:
- **Use a clear and descriptive title**.
- **Provide a step-by-step description** of the suggested feature.
- **Explain why this feature would be useful** to most users.

### Pull Requests
1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Ensure your code follows the existing style and design patterns.
3. Test your changes thoroughly on Hyprland:
   ```bash
   python3 -c "import py_compile; py_compile.compile('whiteboard.py', doraise=True)"
   ./run.sh
   ```
4. Issue clear, descriptive commit messages.
5. Push to your fork and submit a Pull Request to `main`.

---

## 🎨 Code Style & Guidelines

- **Clean & Readable**: Follow PEP 8 guidelines where feasible.
- **No Heavy Dependencies**: Keep dependencies minimal (`GTK3`, `GtkLayerShell`, `PyCairo`, `PyGObject`).
- **Wayland Native**: Ensure features remain fully compatible with Wayland compositor standards.

---

## 📜 Code of Conduct

Please note that this project is released with a Code of Conduct to ensure an open, welcoming, and inclusive environment for everyone. Respect all contributors and keep discussions constructive.

Thank you for contributing! ❤️
