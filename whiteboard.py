#!/usr/bin/env /usr/bin/python3
"""
Whiteboard Overlay v2.1 for Hyprland/Wayland
Transparent full-screen whiteboard with Cairo drawing engine, live text typing,
Vector shape tools (Rectangle, Circle, Arrow), stroke thickness, PNG export,
and GDK click-through input region management.
Ultra-Compact Refined Floating Pill Design.
"""

import sys, os, time, math, subprocess
import gi
import cairo

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

LAYER_NS = 'whiteboard-overlay'

# Colors: Charcoal, Red, Blue, Yellow, White
COLORS = [
    (0.09, 0.09, 0.11, 1.0),  # Black / Charcoal
    (0.94, 0.27, 0.27, 1.0),  # Bright Red
    (0.23, 0.51, 0.96, 1.0),  # Electric Blue
    (0.96, 0.62, 0.07, 1.0),  # Amber Yellow
    (1.00, 1.00, 1.00, 1.0)   # Pure White
]

# Tools
PEN, ERASER, TEXT, RECTANGLE, CIRCLE, ARROW = 0, 1, 2, 3, 4, 5

# Thickness Presets
THICKNESSES = [2, 4, 8, 14]

# Font Families & Sizes
FONT_FAMILIES = ["Sans", "Serif", "Monospace"]
FONT_SIZES = [18, 24, 32]


def create_shape_pixbuf(shape_type):
    """Generates a crisp 16x16 vector Cairo Pixbuf for shape tools."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 16, 16)
    cr = cairo.Context(surface)
    cr.set_source_rgba(0.9, 0.92, 0.98, 0.85)
    cr.set_line_width(1.5)

    if shape_type == 'rect':
        cr.rectangle(2.5, 2.5, 11, 11)
        cr.stroke()
    elif shape_type == 'circle':
        cr.arc(8, 8, 5.5, 0, 6.2832)
        cr.stroke()
    elif shape_type == 'arrow':
        cr.move_to(3, 13)
        cr.line_to(13, 3)
        cr.stroke()
        cr.move_to(13, 3)
        cr.line_to(7, 3)
        cr.move_to(13, 3)
        cr.line_to(13, 9)
        cr.stroke()

    return Gdk.pixbuf_get_from_surface(surface, 0, 0, 16, 16)


class Stroke:
    def __init__(self, tool, color, width, font_family="Sans", font_size=24):
        self.tool = tool
        self.color = color
        self.width = width
        self.points = []
        self.text = ""
        self.tx = 0.0
        self.ty = 0.0
        self.font_family = font_family
        self.font_size = font_size


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
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Draw completed strokes
        for s in self.app.strokes:
            self._draw_stroke(cr, s)

        # Draw active drawing stroke or shape
        if self.cur:
            self._draw_stroke(cr, self.cur)

        # Draw live active text input buffer
        if self.app.tool == TEXT and self.app.text_active:
            cx, cy = self.app.text_pos
            font_fam = FONT_FAMILIES[self.app.font_family_idx]
            font_sz = FONT_SIZES[self.app.font_size_idx]

            cr.set_source_rgba(*self.app.color)
            cr.select_font_face(font_fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(font_sz)

            # Render live text buffer
            cr.move_to(cx, cy)
            cr.show_text(self.app.text_buffer)

            # Calculate cursor position at end of typed text
            extents = cr.text_extents(self.app.text_buffer)
            cursor_x = cx + extents.x_advance

            # Draw glowing cursor bar
            cr.set_source_rgba(0.23, 0.51, 0.96, 0.9)
            cr.set_line_width(2)
            cr.move_to(cursor_x + 2, cy - (font_sz - 4))
            cr.line_to(cursor_x + 2, cy + 4)
            cr.stroke()

        return True

    def _draw_stroke(self, cr, s):
        if s.tool == TEXT:
            if not s.text:
                return
            cr.set_source_rgba(*s.color)
            cr.select_font_face(s.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(s.font_size)
            cr.move_to(s.tx, s.ty)
            cr.show_text(s.text)
            return

        if not s.points:
            return

        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_line_width(s.width)

        if s.tool == ERASER:
            cr.set_operator(cairo.OPERATOR_DEST_OUT)
            cr.set_source_rgba(0, 0, 0, 0)
        else:
            cr.set_operator(cairo.OPERATOR_OVER)
            cr.set_source_rgba(*s.color)

        pts = s.points

        # Shape rendering: RECTANGLE, CIRCLE, ARROW
        if s.tool in (RECTANGLE, CIRCLE, ARROW):
            if len(pts) < 2:
                return
            p0, p1 = pts[0], pts[-1]

            if s.tool == RECTANGLE:
                x = min(p0[0], p1[0])
                y = min(p0[1], p1[1])
                w = abs(p1[0] - p0[0])
                h = abs(p1[1] - p0[1])
                cr.rectangle(x, y, w, h)
                cr.stroke()

            elif s.tool == CIRCLE:
                cx = (p0[0] + p1[0]) / 2.0
                cy = (p0[1] + p1[1]) / 2.0
                rx = abs(p1[0] - p0[0]) / 2.0
                ry = abs(p1[1] - p0[1]) / 2.0
                if rx > 0 and ry > 0:
                    cr.save()
                    cr.translate(cx, cy)
                    cr.scale(rx, ry)
                    cr.arc(0, 0, 1, 0, 2 * math.pi)
                    cr.restore()
                    cr.stroke()

            elif s.tool == ARROW:
                cr.move_to(*p0)
                cr.line_to(*p1)
                cr.stroke()

                # Draw arrowhead
                angle = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                head_len = max(14, s.width * 3)
                wing1 = (p1[0] - head_len * math.cos(angle - 0.45), p1[1] - head_len * math.sin(angle - 0.45))
                wing2 = (p1[0] - head_len * math.cos(angle + 0.45), p1[1] - head_len * math.sin(angle + 0.45))

                cr.move_to(*p1)
                cr.line_to(*wing1)
                cr.move_to(*p1)
                cr.line_to(*wing2)
                cr.stroke()

            cr.set_operator(cairo.OPERATOR_OVER)
            return

        # Freehand Pen / Eraser stroke
        if len(pts) == 1:
            cr.arc(pts[0][0], pts[0][1], s.width / 2.0, 0, 6.2832)
            cr.fill()
            cr.set_operator(cairo.OPERATOR_OVER)
            return

        cr.move_to(*pts[0])
        for x, y in pts[1:]:
            cr.line_to(x, y)
        cr.stroke()
        cr.set_operator(cairo.OPERATOR_OVER)

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

        tool_width = THICKNESSES[self.app.thickness_idx]
        if self.app.tool == ERASER:
            tool_width = max(24, tool_width * 3)

        font_fam = FONT_FAMILIES[self.app.font_family_idx]
        font_sz = FONT_SIZES[self.app.font_size_idx]

        self.cur = Stroke(self.app.tool, self.app.color, tool_width, font_fam, font_sz)
        self.cur.points.append((e.x, e.y))
        self.queue_draw()

    def on_motion(self, _w, e):
        if self.app.draw_mode or not self.cur:
            return
        if e.state & Gdk.ModifierType.BUTTON1_MASK:
            if self.app.tool in (RECTANGLE, CIRCLE, ARROW):
                if len(self.cur.points) == 1:
                    self.cur.points.append((e.x, e.y))
                else:
                    self.cur.points[-1] = (e.x, e.y)
            else:
                self.cur.points.append((e.x, e.y))
            self.queue_draw()

    def on_release(self, _w, e):
        if self.app.draw_mode or e.button != 1 or not self.cur:
            return
        if self.app.tool in (RECTANGLE, CIRCLE, ARROW):
            if len(self.cur.points) == 1:
                self.cur.points.append((e.x, e.y))
            else:
                self.cur.points[-1] = (e.x, e.y)

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
        self.thickness_idx = 1  # 4px default
        self.font_family_idx = 0  # Sans
        self.font_size_idx = 1    # 24px (Medium)
        self.draw_mode = False    # False = Drawing active, True = Click-through
        self.text_active = False
        self.text_buffer = ""
        self.text_pos = (0, 0)
        self.toast_timer = None
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
        
        # Centered container for sleek compact floating toolbar
        align_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        align_box.set_halign(Gtk.Align.CENTER)
        align_box.set_margin_top(6)

        self.bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.bar.set_valign(Gtk.Align.CENTER)
        self.bar.set_margin_start(4)
        self.bar.set_margin_end(4)
        self.bar.set_margin_top(2)
        self.bar.set_margin_bottom(2)
        self.bar.connect('size-allocate', lambda _w, _a: self.update_input())

        # Ultra-Compact Refined High-End GTK3 CSS System
        css_data = b"""
        window { background: transparent; }
        box { background: transparent; }
        drawingarea { background: transparent; }

        /* Sleek Floating Island Toolbar */
        .tb {
            background-color: rgba(12, 14, 20, 0.94);
            border-radius: 14px;
            padding: 3px 6px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
        }

        /* Tool & Action buttons - Strict 26px compact size */
        button.tool-btn {
            background-image: none;
            background-color: transparent;
            min-width: 26px;
            min-height: 26px;
            padding: 2px;
            border-radius: 6px;
            border: 1px solid transparent;
            color: rgba(240, 243, 255, 0.8);
        }
        button.tool-btn:hover {
            background-color: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }
        button.tool-btn.active {
            background-color: rgba(59, 130, 246, 0.25);
            color: #60a5fa;
            border-color: rgba(96, 165, 250, 0.45);
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
        }

        /* Subtle vertical separators */
        .tb separator {
            margin: 2px 3px;
            background-color: rgba(255, 255, 255, 0.10);
            min-width: 1px;
            min-height: 16px;
        }

        /* Color Swatches - Perfect 16px solid circles */
        button.swatch-btn {
            background-image: none;
            min-width: 16px;
            min-height: 16px;
            border-radius: 50px;
            padding: 0;
            margin: 0 2px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: none;
        }
        button.swatch-btn:hover {
            border-color: rgba(255, 255, 255, 0.8);
        }
        button.swatch-btn.active {
            border: 2px solid #ffffff;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.85);
        }

        button.swatch-0 { background-color: #18181b; background-image: none; }
        button.swatch-1 { background-color: #ef4444; background-image: none; }
        button.swatch-2 { background-color: #3b82f6; background-image: none; }
        button.swatch-3 { background-color: #f59e0b; background-image: none; }
        button.swatch-4 { background-color: #ffffff; background-image: none; }

        /* Compact Options Button */
        button.opt-btn {
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            min-height: 22px;
            border-radius: 5px;
            background-color: rgba(255, 255, 255, 0.05);
            color: rgba(240, 243, 255, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        button.opt-btn:hover {
            background-color: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }

        /* Compact Mode status badge button */
        button.mode-btn {
            font-weight: bold;
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 6px;
            min-height: 22px;
        }
        button.mode-draw {
            background-color: rgba(16, 185, 129, 0.20);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.40);
        }
        button.mode-passthrough {
            background-color: rgba(245, 158, 11, 0.18);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }

        /* Quit button */
        button.btn-quit {
            background-color: rgba(239, 68, 68, 0.12);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.25);
        }
        button.btn-quit:hover {
            background-color: rgba(239, 68, 68, 0.30);
            color: #ffffff;
        }

        /* Toast notification label */
        label.toast-label {
            color: #60a5fa;
            font-weight: bold;
            font-size: 10px;
            padding: 1px 6px;
        }
        """

        cssp = Gtk.CssProvider()
        cssp.load_from_data(css_data)
        ctx = self.bar.get_style_context()
        ctx.add_class("tb")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), cssp, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Helper to pack button with strict VAlign CENTER
        def pack_btn(btn):
            btn.set_valign(Gtk.Align.CENTER)
            self.bar.pack_start(btn, False, False, 0)

        # 1. Main Tools buttons (Pen, Eraser, Text)
        self.btn_pen = Gtk.Button()
        self.btn_pen.get_style_context().add_class("tool-btn")
        self.btn_pen.set_image(Gtk.Image.new_from_icon_name("applications-graphics", Gtk.IconSize.MENU))
        self.btn_pen.set_tooltip_text("Pen Tool (P)")
        self.btn_pen.connect('clicked', lambda b: self.set_tool(PEN))
        pack_btn(self.btn_pen)

        self.btn_eraser = Gtk.Button()
        self.btn_eraser.get_style_context().add_class("tool-btn")
        self.btn_eraser.set_image(Gtk.Image.new_from_icon_name("edit-clear", Gtk.IconSize.MENU))
        self.btn_eraser.set_tooltip_text("Eraser Tool (E)")
        self.btn_eraser.connect('clicked', lambda b: self.set_tool(ERASER))
        pack_btn(self.btn_eraser)

        self.btn_text = Gtk.Button()
        self.btn_text.get_style_context().add_class("tool-btn")
        self.btn_text.set_image(Gtk.Image.new_from_icon_name("insert-text", Gtk.IconSize.MENU))
        self.btn_text.set_tooltip_text("Text Tool (T)")
        self.btn_text.connect('clicked', lambda b: self.set_tool(TEXT))
        pack_btn(self.btn_text)

        self._sep()

        # 2. Shape Tools with Crisp Vector Pixbufs (Rectangle, Circle, Arrow)
        self.btn_rect = Gtk.Button()
        self.btn_rect.get_style_context().add_class("tool-btn")
        self.btn_rect.set_image(Gtk.Image.new_from_pixbuf(create_shape_pixbuf('rect')))
        self.btn_rect.set_tooltip_text("Rectangle Shape (R)")
        self.btn_rect.connect('clicked', lambda b: self.set_tool(RECTANGLE))
        pack_btn(self.btn_rect)

        self.btn_circle = Gtk.Button()
        self.btn_circle.get_style_context().add_class("tool-btn")
        self.btn_circle.set_image(Gtk.Image.new_from_pixbuf(create_shape_pixbuf('circle')))
        self.btn_circle.set_tooltip_text("Circle Shape (C)")
        self.btn_circle.connect('clicked', lambda b: self.set_tool(CIRCLE))
        pack_btn(self.btn_circle)

        self.btn_arrow = Gtk.Button()
        self.btn_arrow.get_style_context().add_class("tool-btn")
        self.btn_arrow.set_image(Gtk.Image.new_from_pixbuf(create_shape_pixbuf('arrow')))
        self.btn_arrow.set_tooltip_text("Arrow Shape (A)")
        self.btn_arrow.connect('clicked', lambda b: self.set_tool(ARROW))
        pack_btn(self.btn_arrow)

        self._sep()

        # 3. Color Swatches (16px Round Dots)
        self.color_btns = []
        for i, c in enumerate(COLORS):
            btn = Gtk.Button()
            btn.set_tooltip_text(f"Color {i+1} ({i+1})")
            btn_ctx = btn.get_style_context()
            btn_ctx.add_class("swatch-btn")
            btn_ctx.add_class(f"swatch-{i}")
            btn.connect('clicked', lambda b, idx=i: self.set_color(idx))
            self.color_btns.append(btn)
            pack_btn(btn)

        self._sep()

        # 4. Ultra-Compact Combined Options Button (Thickness • Font)
        self.btn_opt = Gtk.Button()
        self.btn_opt.get_style_context().add_class("opt-btn")
        self.btn_opt.set_label("4px")
        self.btn_opt.set_tooltip_text("Stroke & Font Options (Keys 6-9)")
        self.btn_opt.connect('clicked', lambda b: self.cycle_options())
        pack_btn(self.btn_opt)

        self._sep()

        # 5. Actions (Undo, Redo, Clear, Save PNG)
        self.btn_undo = Gtk.Button()
        self.btn_undo.get_style_context().add_class("tool-btn")
        self.btn_undo.set_image(Gtk.Image.new_from_icon_name("edit-undo", Gtk.IconSize.MENU))
        self.btn_undo.set_tooltip_text("Undo (Ctrl+Z)")
        self.btn_undo.connect('clicked', lambda b: self.undo())
        pack_btn(self.btn_undo)

        self.btn_redo = Gtk.Button()
        self.btn_redo.get_style_context().add_class("tool-btn")
        self.btn_redo.set_image(Gtk.Image.new_from_icon_name("edit-redo", Gtk.IconSize.MENU))
        self.btn_redo.set_tooltip_text("Redo (Ctrl+Y)")
        self.btn_redo.connect('clicked', lambda b: self.redo())
        pack_btn(self.btn_redo)

        self.btn_clear = Gtk.Button()
        self.btn_clear.get_style_context().add_class("tool-btn")
        self.btn_clear.set_image(Gtk.Image.new_from_icon_name("edit-clear-all", Gtk.IconSize.MENU))
        self.btn_clear.set_tooltip_text("Clear All")
        self.btn_clear.connect('clicked', lambda b: self.clear())
        pack_btn(self.btn_clear)

        self.btn_save = Gtk.Button()
        self.btn_save.get_style_context().add_class("tool-btn")
        self.btn_save.set_image(Gtk.Image.new_from_icon_name("document-save", Gtk.IconSize.MENU))
        self.btn_save.set_tooltip_text("Export PNG (Ctrl+S)")
        self.btn_save.connect('clicked', lambda b: self.export_png())
        pack_btn(self.btn_save)

        self._sep()

        # 6. Draw / Passthrough Mode Toggle Button
        self.btn_mode = Gtk.Button()
        self.btn_mode.get_style_context().add_class("tool-btn")
        self.btn_mode.get_style_context().add_class("mode-btn")
        self.btn_mode.set_label("Draw")
        self.btn_mode.set_tooltip_text("Toggle Passthrough / Draw (Space / Ctrl+H)")
        self.btn_mode.connect('clicked', lambda b: self.toggle_mode())
        pack_btn(self.btn_mode)

        self._sep()

        # 7. Quit Button
        self.btn_quit = Gtk.Button()
        self.btn_quit.get_style_context().add_class("tool-btn")
        self.btn_quit.get_style_context().add_class("btn-quit")
        self.btn_quit.set_image(Gtk.Image.new_from_icon_name("window-close", Gtk.IconSize.MENU))
        self.btn_quit.set_tooltip_text("Quit Overlay (Ctrl+Q)")
        self.btn_quit.connect('clicked', lambda b: Gtk.main_quit())
        pack_btn(self.btn_quit)

        # Toast Label for Feedback Messages
        self.toast_label = Gtk.Label()
        self.toast_label.get_style_context().add_class("toast-label")
        self.toast_label.set_valign(Gtk.Align.CENTER)
        self.toast_label.set_no_show_all(True)
        self.bar.pack_start(self.toast_label, False, False, 0)

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
        s.set_valign(Gtk.Align.CENTER)
        s.set_margin_start(1)
        s.set_margin_end(1)
        self.bar.pack_start(s, False, False, 0)

    def show_toast(self, msg):
        self.toast_label.set_text(msg)
        self.toast_label.show()
        if self.toast_timer:
            GLib.source_remove(self.toast_timer)
        self.toast_timer = GLib.timeout_add(3000, lambda: self.toast_label.hide() or False)

    def update_options_label(self):
        th = f"{THICKNESSES[self.thickness_idx]}px"
        if self.tool == TEXT:
            fam = FONT_FAMILIES[self.font_family_idx]
            sz = FONT_SIZES[self.font_size_idx]
            self.btn_opt.set_label(f"{th} • {fam} {sz}")
        else:
            self.btn_opt.set_label(th)

    def cycle_options(self):
        if self.tool == TEXT:
            self.font_size_idx = (self.font_size_idx + 1) % len(FONT_SIZES)
        else:
            self.thickness_idx = (self.thickness_idx + 1) % len(THICKNESSES)
        self.update_options_label()

    def on_win_draw(self, _w, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
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
                region = cairo.Region()
                w.input_shape_combine_region(region, 0, 0)

            # Keyboard mode NONE lets active desktop apps receive keyboard focus
            if HAS_LAYER_SHELL and GtkLayerShell:
                GtkLayerShell.set_keyboard_mode(self.win, GtkLayerShell.KeyboardMode.NONE)
        else:
            # Drawing mode: full window receives input
            rect = cairo.RectangleInt(0, 0, 32767, 32767)
            region = cairo.Region(rect)
            w.input_shape_combine_region(region, 0, 0)

            # EXCLUSIVE keyboard mode captures shortcuts and text input
            if HAS_LAYER_SHELL and GtkLayerShell:
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

        tool_btns = [
            (self.btn_pen, t == PEN),
            (self.btn_eraser, t == ERASER),
            (self.btn_text, t == TEXT),
            (self.btn_rect, t == RECTANGLE),
            (self.btn_circle, t == CIRCLE),
            (self.btn_arrow, t == ARROW)
        ]

        for btn, active in tool_btns:
            ctx = btn.get_style_context()
            if active:
                ctx.add_class('active')
            else:
                ctx.remove_class('active')

        self.update_options_label()

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

    def set_thickness(self, idx):
        if 0 <= idx < len(THICKNESSES):
            self.thickness_idx = idx
            self.update_options_label()

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

    def export_png(self):
        if self.text_active and self.text_buffer:
            self.commit_text()

        pictures_dir = os.path.expanduser("~/Pictures")
        if not os.path.exists(pictures_dir):
            target_dir = os.path.expanduser("~")
        else:
            target_dir = pictures_dir

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(target_dir, f"whiteboard_{timestamp}.png")

        w_size = self.win.get_size()
        width = max(800, w_size[0])
        height = max(600, w_size[1])

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)

        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        if self.area:
            for s in self.strokes:
                self.area._draw_stroke(cr, s)

        surface.write_to_png(filepath)
        filename = os.path.basename(filepath)
        self.show_toast(f"💾 Saved {filename}")

    def toggle_mode(self):
        if self.text_active and self.text_buffer:
            self.commit_text()
        self.draw_mode = not self.draw_mode
        ctx = self.btn_mode.get_style_context()

        if self.draw_mode:
            self.btn_mode.set_label("Pass")
            ctx.remove_class("mode-draw")
            ctx.add_class("mode-passthrough")
        else:
            self.btn_mode.set_label("Draw")
            ctx.remove_class("mode-passthrough")
            ctx.add_class("mode-draw")

        self.update_input()

    def commit_text(self):
        if self.text_buffer and self.text_active:
            font_fam = FONT_FAMILIES[self.font_family_idx]
            font_sz = FONT_SIZES[self.font_size_idx]
            s = Stroke(TEXT, self.color, 0, font_fam, font_sz)
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

        # Global overlay shortcuts (Quit, Undo, Redo, Save PNG)
        if ctrl and kv == Gdk.keyval_from_name('q'):
            Gtk.main_quit()
            return True
        if ctrl and kv == Gdk.keyval_from_name('z'):
            self.undo()
            return True
        if ctrl and kv == Gdk.keyval_from_name('y'):
            self.redo()
            return True
        if ctrl and kv == Gdk.keyval_from_name('s'):
            self.export_png()
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

            # Thickness hotkeys 6-9
            for idx, key_num in enumerate(range(6, 10)):
                if kv == Gdk.keyval_from_name(str(key_num)):
                    self.set_thickness(idx)
                    return True

            # Tool hotkeys P, E, T, R, C, A
            if kv in (Gdk.keyval_from_name('p'), Gdk.keyval_from_name('P')):
                self.set_tool(PEN)
                return True
            if kv in (Gdk.keyval_from_name('e'), Gdk.keyval_from_name('E')):
                self.set_tool(ERASER)
                return True
            if kv in (Gdk.keyval_from_name('t'), Gdk.keyval_from_name('T')):
                self.set_tool(TEXT)
                return True
            if kv in (Gdk.keyval_from_name('r'), Gdk.keyval_from_name('R')):
                self.set_tool(RECTANGLE)
                return True
            if kv in (Gdk.keyval_from_name('c'), Gdk.keyval_from_name('C')):
                self.set_tool(CIRCLE)
                return True
            if kv in (Gdk.keyval_from_name('a'), Gdk.keyval_from_name('A')):
                self.set_tool(ARROW)
                return True

        return False


def main():
    App()
    Gtk.main()


if __name__ == '__main__':
    main()
