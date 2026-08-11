#!/usr/bin/env /usr/bin/python3
"""
Whiteboard Overlay for Hyprland/Wayland
Transparent full-screen whiteboard with Cairo drawing engine, live text typing,
and reliable click-through input region management.
"""

import sys, os, subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
gi.require_version('cairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, cairo

LAYER_NS = 'whiteboard-overlay'

# Colors: Charcoal, Red, Blue, Yellow, White
COLORS = [
    (0.08, 0.08, 0.10, 1.0),  # Black / Charcoal
    (0.93, 0.27, 0.27, 1.0),  # Bright Red
    (0.23, 0.51, 0.96, 1.0),  # Vibrant Blue
    (0.96, 0.72, 0.15, 1.0),  # Warm Yellow
    (0.98, 0.98, 1.00, 1.0)   # Pure White
]

PEN, ERASER, TEXT = 0, 1, 2

class Stroke:
    def __init__(self, tool, color, width):
        self.tool = tool
        self.color = color
        self.width = width
        self.points = []
        self.text = ""
        self.tx = 0.0
        self.ty = 0.0

class Canvas(Gtk.DrawingArea):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.cur = None
        self.set_can_focus(True)
        self.set_app_paintable(True)
        self.connect('draw', self.on_draw)
        self.connect('motion-notify-event', self.on_motion)
        self.connect('button-press-event', self.on_press)
        self.connect('button-release-event', self.on_release)
        self.set_events(
            Gdk.EventMask.EXPOSURE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK
        )

    def on_draw(self, _w, cr):
        # Clear canvas surface to fully transparent
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.Operator.CLEAR)
        cr.paint()
        cr.set_operator(cairo.Operator.OVER)

        # Draw completed strokes
        for s in self.app.strokes:
            self._draw_stroke(cr, s)

        # Draw active drawing stroke
        if self.cur:
            self._draw_stroke(cr, self.cur)

        # Draw live active text input buffer
        if self.app.tool == TEXT and self.app.text_active:
            cx, cy = self.app.text_pos
            cr.set_source_rgba(*self.app.color)
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(24)

            # Render live text buffer
            cr.move_to(cx, cy)
            cr.show_text(self.app.text_buffer)

            # Calculate cursor position at end of typed text
            extents = cr.text_extents(self.app.text_buffer)
            cursor_x = cx + extents.x_advance

            # Draw glowing cursor bar
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.9)
            cr.set_line_width(2)
            cr.move_to(cursor_x + 2, cy - 20)
            cr.line_to(cursor_x + 2, cy + 4)
            cr.stroke()

        return True

    def _draw_stroke(self, cr, s):
        if s.tool == TEXT:
            if not s.text:
                return
            cr.set_source_rgba(*s.color)
            cr.select_font_face("Sans", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
            cr.set_font_size(24)
            cr.move_to(s.tx, s.ty)
            cr.show_text(s.text)
            return

        if not s.points:
            return

        cr.set_line_cap(cairo.LineCap.ROUND)
        cr.set_line_join(cairo.LineJoin.ROUND)
        cr.set_line_width(s.width)

        if s.tool == ERASER:
            cr.set_operator(cairo.Operator.DEST_OUT)
            cr.set_source_rgba(0, 0, 0, 0)
        else:
            cr.set_operator(cairo.Operator.OVER)
            cr.set_source_rgba(*s.color)

        pts = s.points
        if len(pts) == 1:
            cr.arc(pts[0][0], pts[0][1], s.width / 2, 0, 6.2832)
            cr.fill()
            cr.set_operator(cairo.Operator.OVER)
            return

        cr.move_to(*pts[0])
        for x, y in pts[1:]:
            cr.line_to(x, y)
        cr.stroke()
        cr.set_operator(cairo.Operator.OVER)

    def on_press(self, _w, e):
        if self.app.draw_mode or e.button != 1:
            return

        if self.app.tool == TEXT:
            if self.app.text_active and self.app.text_buffer:
                self.app.commit_text()

            self.app.text_pos = (e.x, e.y)
            self.app.text_buffer = ""
            self.app.text_active = True
            self.grab_focus()
            self.app.win.grab_focus()
            self.queue_draw()
            return

        if self.app.text_active:
            self.app.commit_text()

        self.cur = Stroke(self.app.tool, self.app.color, 24 if self.app.tool == ERASER else 4)
        self.cur.points.append((e.x, e.y))
        self.queue_draw()

    def on_motion(self, _w, e):
        if self.app.draw_mode or not self.cur:
            return
        if e.state & Gdk.ModifierType.BUTTON1_MASK:
            self.cur.points.append((e.x, e.y))
            self.queue_draw()

    def on_release(self, _w, e):
        if self.app.draw_mode or e.button != 1 or not self.cur:
            return
        if self.cur.points:
            self.app.strokes.append(self.cur)
            self.app.redo.clear()
        self.cur = None
        self.queue_draw()


class App:
    def __init__(self):
        self.strokes = []
        self.redo = []
        self.tool = PEN
        self.color_idx = 1
        self.color = COLORS[1]
        self.draw_mode = False  # False = Drawing active, True = Click-through
        self.text_active = False
        self.text_buffer = ""
        self.text_pos = (0, 0)
        self.area = None
        self.bar = None
        self.build()

    def build(self):
        self.win = Gtk.Window()
        self.win.set_title("Whiteboard Overlay")
        self.win.set_keep_above(True)
        self.win.set_skip_taskbar_hint(True)
        self.win.set_skip_pager_hint(True)
        self.win.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.win.set_app_paintable(True)

        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()
        if visual:
            self.win.set_visual(visual)

        GtkLayerShell.init_for_window(self.win)
        GtkLayerShell.set_namespace(self.win, LAYER_NS)
        GtkLayerShell.set_layer(self.win, GtkLayerShell.Layer.OVERLAY)
        for edge in [GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT, GtkLayerShell.Edge.BOTTOM]:
            GtkLayerShell.set_anchor(self.win, edge, True)

        GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        self.win.connect('key-press-event', self.on_key)
        self.win.connect('destroy', Gtk.main_quit)
        self.win.connect('realize', lambda _w: self.update_input())
        self.win.connect('draw', self.on_win_draw)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Centered container for sleek toolbar
        align_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        align_box.set_halign(Gtk.Align.CENTER)
        align_box.set_margin_top(12)

        self.bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.bar.set_margin_start(10)
        self.bar.set_margin_end(10)
        self.bar.set_margin_top(6)
        self.bar.set_margin_bottom(6)
        self.bar.connect('size-allocate', lambda _w, _a: self.update_input())

        # Anti-slop / Taste Design System CSS styling
        css_data = b"""
        window { background: transparent; }
        box { background: transparent; }
        drawingarea { background: transparent; }

        .tb {
            background: rgba(15, 17, 26, 0.88);
            border-radius: 20px;
            padding: 6px 10px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }
        .tb button {
            min-width: 40px;
            min-height: 40px;
            padding: 6px;
            border-radius: 12px;
            border: 1px solid transparent;
            background: rgba(255, 255, 255, 0.05);
            color: rgba(240, 243, 255, 0.8);
            transition: all 0.15s ease;
        }
        .tb button:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.2);
        }
        .tb button.active {
            background: rgba(59, 130, 246, 0.25);
            color: #60a5fa;
            border-color: rgba(96, 165, 250, 0.5);
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        .tb separator {
            margin: 4px 6px;
            background: rgba(255, 255, 255, 0.12);
            min-width: 1px;
            min-height: 24px;
        }
        .swatch {
            border-radius: 50%;
            min-width: 30px;
            min-height: 30px;
            padding: 0;
            border: 2px solid rgba(255, 255, 255, 0.15);
            transition: transform 0.15s ease;
        }
        .swatch:hover {
            transform: scale(1.1);
        }
        .swatch.active {
            border-color: #ffffff;
            box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.4);
            transform: scale(1.12);
        }
        .mode-btn {
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 12px;
        }
        .mode-draw {
            background: rgba(16, 185, 129, 0.2) !important;
            color: #34d399 !important;
            border: 1px solid rgba(52, 211, 153, 0.4) !important;
            box-shadow: 0 0 14px rgba(16, 185, 129, 0.25);
        }
        .mode-passthrough {
            background: rgba(245, 158, 11, 0.18) !important;
            color: #fbbf24 !important;
            border: 1px solid rgba(245, 158, 11, 0.35) !important;
        }
        .btn-quit {
            background: rgba(239, 68, 68, 0.15) !important;
            color: #f87171 !important;
            border: 1px solid rgba(239, 68, 68, 0.3) !important;
        }
        .btn-quit:hover {
            background: rgba(239, 68, 68, 0.3) !important;
            color: #ffffff !important;
        }
        """

        cssp = Gtk.CssProvider()
        cssp.load_from_data(css_data)
        ctx = self.bar.get_style_context()
        ctx.add_class("tb")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), cssp, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Tools buttons
        self.btn_pen = Gtk.Button()
        self.btn_pen.set_image(Gtk.Image.new_from_icon_name("applications-graphics", Gtk.IconSize.BUTTON))
        self.btn_pen.set_tooltip_text("Pen Tool (P)")
        self.btn_pen.connect('clicked', lambda b: self.set_tool(PEN))
        self.bar.pack_start(self.btn_pen, False, False, 0)

        self.btn_eraser = Gtk.Button()
        self.btn_eraser.set_image(Gtk.Image.new_from_icon_name("edit-clear", Gtk.IconSize.BUTTON))
        self.btn_eraser.set_tooltip_text("Eraser Tool (E)")
        self.btn_eraser.connect('clicked', lambda b: self.set_tool(ERASER))
        self.bar.pack_start(self.btn_eraser, False, False, 0)

        self.btn_text = Gtk.Button()
        self.btn_text.set_image(Gtk.Image.new_from_icon_name("insert-text", Gtk.IconSize.BUTTON))
        self.btn_text.set_tooltip_text("Text Tool (T)")
        self.btn_text.connect('clicked', lambda b: self.set_tool(TEXT))
        self.bar.pack_start(self.btn_text, False, False, 0)

        self._sep()

        # Color Swatches
        self.color_btns = []
        for i, c in enumerate(COLORS):
            btn = Gtk.Button()
            btn.set_size_request(30, 30)
            btn.set_tooltip_text(f"Color {i+1} ({i+1})")
            btn.get_style_context().add_class("swatch")
            r, g, b, a = c
            css_c = f".c{i}{{background:rgba({int(r*255)},{int(g*255)},{int(b*255)},{a});}}"
            cp = Gtk.CssProvider()
            cp.load_from_data(css_c.encode())
            btn.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            btn.get_style_context().add_class(f"c{i}")
            btn.connect('clicked', lambda b, idx=i: self.set_color(idx))
            self.color_btns.append(btn)
            self.bar.pack_start(btn, False, False, 0)

        self._sep()

        # Undo / Redo / Clear
        self.btn_undo = Gtk.Button()
        self.btn_undo.set_image(Gtk.Image.new_from_icon_name("edit-undo", Gtk.IconSize.BUTTON))
        self.btn_undo.set_tooltip_text("Undo (Ctrl+Z)")
        self.btn_undo.connect('clicked', lambda b: self.undo())
        self.bar.pack_start(self.btn_undo, False, False, 0)

        self.btn_redo = Gtk.Button()
        self.btn_redo.set_image(Gtk.Image.new_from_icon_name("edit-redo", Gtk.IconSize.BUTTON))
        self.btn_redo.set_tooltip_text("Redo (Ctrl+Y)")
        self.btn_redo.connect('clicked', lambda b: self.redo())
        self.bar.pack_start(self.btn_redo, False, False, 0)

        self.btn_clear = Gtk.Button()
        self.btn_clear.set_image(Gtk.Image.new_from_icon_name("edit-clear-all", Gtk.IconSize.BUTTON))
        self.btn_clear.set_tooltip_text("Clear All")
        self.btn_clear.connect('clicked', lambda b: self.clear())
        self.bar.pack_start(self.btn_clear, False, False, 0)

        self._sep()

        # Draw / Passthrough Mode Toggle Button
        self.btn_mode = Gtk.Button()
        self.btn_mode.get_style_context().add_class("mode-btn")
        self.btn_mode.set_image(Gtk.Image.new_from_icon_name("input-mouse", Gtk.IconSize.BUTTON))
        self.btn_mode.set_label(" Drawing")
        self.btn_mode.set_tooltip_text("Toggle Passthrough / Draw (Space / Ctrl+H)")
        self.btn_mode.connect('clicked', lambda b: self.toggle_mode())
        self.bar.pack_start(self.btn_mode, False, False, 0)

        self._sep()

        self.btn_quit = Gtk.Button()
        self.btn_quit.set_image(Gtk.Image.new_from_icon_name("window-close", Gtk.IconSize.BUTTON))
        self.btn_quit.set_tooltip_text("Quit Overlay (Ctrl+Q)")
        self.btn_quit.get_style_context().add_class("btn-quit")
        self.btn_quit.connect('clicked', lambda b: Gtk.main_quit())
        self.bar.pack_start(self.btn_quit, False, False, 0)

        align_box.pack_start(self.bar, False, False, 0)
        outer.pack_start(align_box, False, False, 0)
        self.win.add(outer)
        self.win.show_all()

        self.set_tool(PEN)
        self.set_color(1)
        GLib.idle_add(self._add_canvas)

    def _add_canvas(self):
        if self.area is None:
            self.area = Canvas(self)
            self.win.get_child().pack_end(self.area, True, True, 0)
            self.win.show_all()
            self.update_input()

    def _sep(self):
        s = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        s.set_margin_start(2)
        s.set_margin_end(2)
        self.bar.pack_start(s, False, False, 0)

    def on_win_draw(self, _w, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.Operator.CLEAR)
        cr.paint()
        cr.set_operator(cairo.Operator.OVER)
        return False

    def update_input(self):
        """
        Updates input region and keyboard interactivity mode based on draw_mode.
        - Passthrough Mode (draw_mode=True): canvas passes mouse clicks to desktop windows underneath.
          Toolbar remains interactive. Keyboard focus is released to desktop apps.
        - Drawing Mode (draw_mode=False): canvas intercepts mouse clicks for drawing strokes & text.
          Keyboard focus is grabbed for shortcuts and text typing.
        """
        w = self.win.get_window()
        if not w:
            return

        if self.draw_mode:
            # Passthrough mode: restrict input region to toolbar area only
            alloc = self.bar.get_allocation()
            if alloc.width > 1 and alloc.height > 1:
                # Add 8px margin around toolbar for easy interaction
                rect = cairo.RectangleInt(
                    max(0, alloc.x - 8),
                    max(0, alloc.y - 8),
                    alloc.width + 16,
                    alloc.height + 16
                )
                region = cairo.Region(rect)
                w.input_shape_combine_region(region, 0, 0)
            else:
                w.input_shape_combine_region(cairo.Region(), 0, 0)

            # Keyboard mode NONE lets active desktop apps receive keyboard focus
            GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.NONE)
        else:
            # Drawing mode: full window receives input
            w.input_shape_combine_region(None, 0, 0)

            # EXCLUSIVE keyboard mode captures shortcuts and text input
            GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.EXCLUSIVE)
            if self.area:
                self.area.grab_focus()

        self.win.queue_draw()

    # ── Actions ──
    def set_tool(self, t):
        if self.text_active and self.text_buffer:
            self.commit_text()
        self.tool = t
        self.text_active = False

        if self.draw_mode:
            self.toggle_mode()

        for btn, active in [(self.btn_pen, t == PEN), (self.btn_eraser, t == ERASER), (self.btn_text, t == TEXT)]:
            ctx = btn.get_style_context()
            if active:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')

        if self.area:
            self.area.queue_draw()

    def set_color(self, i):
        if 0 <= i < len(COLORS):
            self.color_idx = i
            self.color = COLORS[i]
            for idx, btn in enumerate(self.color_btns):
                ctx = btn.get_style_context()
                if idx == i:
                    ctx.add_class('active')
                else:
                    ctx.remove_class('active')
            self.set_tool(PEN)

    def undo(self):
        if self.text_active and self.text_buffer:
            self.commit_text()
        if self.strokes:
            self.redo.append(self.strokes.pop())
        if self.area:
            self.area.queue_draw()

    def redo(self):
        if self.redo:
            self.strokes.append(self.redo.pop())
        if self.area:
            self.area.queue_draw()

    def clear(self):
        self.strokes.clear()
        self.redo.clear()
        self.text_active = False
        self.text_buffer = ""
        if self.area:
            self.area.queue_draw()

    def toggle_mode(self):
        if self.text_active and self.text_buffer:
            self.commit_text()
        self.draw_mode = not self.draw_mode
        ctx = self.btn_mode.get_style_context()

        if self.draw_mode:
            self.btn_mode.set_image(Gtk.Image.new_from_icon_name("input-mouse", Gtk.IconSize.BUTTON))
            self.btn_mode.set_label(" Click-Through")
            ctx.remove_class("mode-draw")
            ctx.add_class("mode-passthrough")
        else:
            self.btn_mode.set_image(Gtk.Image.new_from_icon_name("input-tablet", Gtk.IconSize.BUTTON))
            self.btn_mode.set_label(" Drawing")
            ctx.remove_class("mode-passthrough")
            ctx.add_class("mode-draw")

        self.update_input()

    def commit_text(self):
        if self.text_buffer and self.text_active:
            s = Stroke(TEXT, self.color, 0)
            s.text = self.text_buffer
            s.tx, s.ty = self.text_pos
            self.strokes.append(s)
            self.redo.clear()
        self.text_active = False
        self.text_buffer = ""
        if self.area:
            self.area.queue_draw()

    def on_key(self, _w, e):
        kv = e.keyval
        ctrl = bool(e.state & Gdk.ModifierType.CONTROL_MASK)

        # Global overlay shortcuts (Quit, Undo, Redo)
        if ctrl and kv == Gdk.keyval_from_name('q'):
            Gtk.main_quit()
            return True
        if ctrl and kv == Gdk.keyval_from_name('z'):
            self.undo()
            return True
        if ctrl and kv == Gdk.keyval_from_name('y'):
            self.redo()
            return True
        if ctrl and kv == Gdk.keyval_from_name('h'):
            self.toggle_mode()
            return True

        # Text editing active
        if self.text_active:
            if kv == Gdk.KEY_Escape:
                self.commit_text()
                return True
            if kv == Gdk.KEY_Return or kv == Gdk.KEY_KP_Enter:
                self.commit_text()
                return True
            if kv == Gdk.KEY_BackSpace:
                self.text_buffer = self.text_buffer[:-1]
                if self.area:
                    self.area.queue_draw()
                return True
            
            # Unicode character input
            c = Gdk.keyval_to_unicode(kv)
            if c and 32 <= c < 0x10000:
                self.text_buffer += chr(c)
                if self.area:
                    self.area.queue_draw()
                return True
            return True

        # Shortcuts when drawing active (not typing text)
        if kv == Gdk.KEY_space:
            self.toggle_mode()
            return True

        if not ctrl:
            # Color hotkeys 1-5
            for i in range(5):
                if kv == Gdk.keyval_from_name(str(i + 1)):
                    self.set_color(i)
                    return True

            # Tool hotkeys P, E, T
            if kv in (Gdk.keyval_from_name('p'), Gdk.keyval_from_name('P')):
                self.set_tool(PEN)
                return True
            if kv in (Gdk.keyval_from_name('e'), Gdk.keyval_from_name('E')):
                self.set_tool(ERASER)
                return True
            if kv in (Gdk.keyval_from_name('t'), Gdk.keyval_from_name('T')):
                self.set_tool(TEXT)
                return True

        return False


def main():
    App()
    Gtk.main()


if __name__ == '__main__':
    main()
