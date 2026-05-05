import os
import tkinter as tk
from tkinter import messagebox
import threading
import sys
import importlib
import time

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# Import các file xử lý
import pdf2img
import main_v4


# ══════════════════════════════════════════════
#  THEME & CONSTANTS
# ══════════════════════════════════════════════
DARK_BG      = "#0d0f14"
PANEL_BG     = "#141720"
CARD_BG      = "#1a1f2e"
BORDER       = "#252b3d"
ACCENT       = "#4f8ef7"
ACCENT_DIM   = "#1e3a6e"
SUCCESS      = "#22c55e"
WARNING      = "#f59e0b"
ERROR_CLR    = "#ef4444"
TEXT_PRI     = "#e8ecf4"
TEXT_SEC     = "#6b7897"
TEXT_MUTED   = "#3d4560"

FONT_TITLE   = ("Consolas", 13, "bold")
FONT_LABEL   = ("Consolas", 9)
FONT_BTN     = ("Consolas", 10, "bold")
FONT_LOG     = ("Consolas", 9)
FONT_STEP    = ("Consolas", 8)


class AnimatedButton(tk.Canvas):
    """Custom animated button với hover effect và ripple."""
    def __init__(self, parent, text, command=None, icon="", state_color=ACCENT, **kwargs):
        super().__init__(parent, bg=PANEL_BG, highlightthickness=0,
                         width=kwargs.pop("width", 190),
                         height=kwargs.pop("height", 54),
                         cursor="hand2")
        self.text = text
        self.icon = icon
        self.command = command
        self.state_color = state_color
        self._enabled = True
        self._hovered = False
        self._progress = 0       # 0.0 – 1.0  (for running animation)
        self._anim_id = None

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _draw(self):
        self.delete("all")
        w = int(self.cget("width"))
        h = int(self.cget("height"))

        if not self._enabled:
            fill = "#1a1f2e"
            border_c = TEXT_MUTED
            text_c = TEXT_MUTED
        elif self._hovered:
            fill = self.state_color
            border_c = self.state_color
            text_c = "#ffffff"
        else:
            fill = CARD_BG
            border_c = self.state_color
            text_c = self.state_color

        # Rounded rect border
        r = 8
        self._rounded_rect(4, 4, w-4, h-4, r, outline=border_c, fill=fill, width=1)

        # Progress bar at bottom (running state)
        if self._progress > 0 and self._enabled:
            bar_w = int((w - 8) * self._progress)
            self.create_rectangle(4, h-6, 4+bar_w, h-3, fill=self.state_color, outline="")

        # Icon + text
        label = f"{self.icon}  {self.text}" if self.icon else self.text
        self.create_text(w//2, h//2 - (3 if self._progress > 0 else 0),
                         text=label, fill=text_c,
                         font=FONT_BTN, anchor="center")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90,  style="arc" if kw.get("fill","") == "" else "pieslice", **{k:v for k,v in kw.items() if k!="fill" or True})
        # Simpler: use polygon approach
        self.delete("all_rr")
        points = [
            x1+r, y1,   x2-r, y1,
            x2, y1,     x2, y1+r,
            x2, y2-r,   x2, y2,
            x2-r, y2,   x1+r, y2,
            x1, y2,     x1, y2-r,
            x1, y1+r,   x1, y1,
        ]
        fill_c = kw.get("fill", "")
        outline_c = kw.get("outline", "")
        width_v = kw.get("width", 1)
        self.create_polygon(points, smooth=True, fill=fill_c, outline=outline_c, width=width_v)

    def _on_enter(self, e):
        if self._enabled:
            self._hovered = True
            self._draw()

    def _on_leave(self, e):
        self._hovered = False
        self._draw()

    def _on_click(self, e):
        if self._enabled and self.command:
            self.command()

    def set_enabled(self, val):
        self._enabled = val
        self._hovered = False
        if not val:
            self._start_pulse()
        else:
            self._stop_pulse()
        self._draw()

    def _start_pulse(self):
        self._progress = 0.0
        self._animate_progress()

    def _animate_progress(self):
        if not self._enabled:
            self._progress = (self._progress + 0.012) % 1.0
            self._draw()
            self._anim_id = self.after(30, self._animate_progress)

    def _stop_pulse(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self._progress = 0
        self._draw()


class StatusDot(tk.Canvas):
    """Animated pulsing status dot."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, width=12, height=12, bg=PANEL_BG, highlightthickness=0)
        self._state = "idle"   # idle | running | done | error
        self._alpha = 1.0
        self._dir = -1
        self._draw()
        self._pulse()

    def _color(self):
        return {
            "idle":    TEXT_MUTED,
            "running": ACCENT,
            "done":    SUCCESS,
            "error":   ERROR_CLR,
        }.get(self._state, TEXT_MUTED)

    def _draw(self):
        self.delete("all")
        c = self._color()
        # Outer glow for running
        if self._state == "running":
            size = int(5 + 3 * (1 - self._alpha))
            self.create_oval(6-size, 6-size, 6+size, 6+size, fill="", outline=c, width=1)
        self.create_oval(3, 3, 9, 9, fill=c, outline="")

    def _pulse(self):
        if self._state == "running":
            self._alpha += self._dir * 0.05
            if self._alpha <= 0.2:
                self._dir = 1
            elif self._alpha >= 1.0:
                self._dir = -1
        self._draw()
        self.after(50, self._pulse)

    def set_state(self, state):
        self._state = state
        self._draw()


class LogConsole(tk.Frame):
    """Styled log console with colored lines."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=DARK_BG, **kwargs)

        # Header bar
        hdr = tk.Frame(self, bg=BORDER, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="◈  CONSOLE OUTPUT", bg=BORDER,
                 fg=TEXT_SEC, font=FONT_STEP).pack(side="left", padx=10, pady=4)

        # Traffic lights
        for col in [ERROR_CLR, WARNING, SUCCESS]:
            tk.Canvas(hdr, width=10, height=10, bg=BORDER,
                      highlightthickness=0).pack(side="right", padx=3, pady=9)
            # draw circle
        dot_frame = tk.Frame(hdr, bg=BORDER)
        dot_frame.pack(side="right", padx=8)
        for col in [ERROR_CLR, WARNING, SUCCESS]:
            c = tk.Canvas(dot_frame, width=10, height=10, bg=BORDER, highlightthickness=0)
            c.pack(side="left", padx=2, pady=9)
            c.create_oval(1, 1, 9, 9, fill=col, outline="")

        # Text area
        self.text = tk.Text(
            self,
            bg="#080a10",
            fg=TEXT_PRI,
            font=FONT_LOG,
            state="disabled",
            wrap="word",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            selectbackground=ACCENT_DIM,
            insertbackground=ACCENT,
            cursor="arrow",
        )
        self.text.pack(fill="both", expand=True)

        # Scrollbar
        sb = tk.Scrollbar(self, command=self.text.yview, bg=BORDER,
                          troughcolor=DARK_BG, width=8)
        self.text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Tags
        self.text.tag_config("sys",     foreground=ACCENT)
        self.text.tag_config("ok",      foreground=SUCCESS)
        self.text.tag_config("warn",    foreground=WARNING)
        self.text.tag_config("err",     foreground=ERROR_CLR)
        self.text.tag_config("dim",     foreground=TEXT_SEC)
        self.text.tag_config("plain",   foreground=TEXT_PRI)

        self._line_buf = ""

    def write(self, text):
        self._line_buf += text
        while "\n" in self._line_buf:
            line, self._line_buf = self._line_buf.split("\n", 1)
            self._append_line(line + "\n")

    def _append_line(self, line):
        self.text.config(state="normal")
        # Detect tag
        low = line.lower()
        if "[hệ thống]" in low or "[system]" in low:
            tag = "sys"
        elif "[lỗi]" in low or "[error]" in low or "error" in low or "exception" in low:
            tag = "err"
        elif "hoàn thành" in low or "done" in low or "success" in low or "✓" in low:
            tag = "ok"
        elif "warning" in low or "cảnh báo" in low:
            tag = "warn"
        elif line.strip().startswith("#") or line.strip() == "":
            tag = "dim"
        else:
            tag = "plain"

        ts = time.strftime("%H:%M:%S")
        self.text.insert("end", f"[{ts}] ", "dim")
        self.text.insert("end", line, tag)
        self.text.see("end")
        self.text.config(state="disabled")

    def flush(self):
        pass

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")


class StepCard(tk.Frame):
    """A workflow step card with number badge + description."""
    def __init__(self, parent, number, title, desc, **kwargs):
        super().__init__(parent, bg=CARD_BG, **kwargs)
        self.config(relief="flat", bd=0)

        # Left accent bar
        tk.Frame(self, bg=ACCENT, width=3).pack(side="left", fill="y")

        inner = tk.Frame(self, bg=CARD_BG, padx=12, pady=8)
        inner.pack(side="left", fill="both", expand=True)

        top = tk.Frame(inner, bg=CARD_BG)
        top.pack(fill="x")

        # Number badge
        badge = tk.Canvas(top, width=22, height=22, bg=CARD_BG, highlightthickness=0)
        badge.pack(side="left", padx=(0, 8))
        badge.create_oval(1, 1, 21, 21, fill=ACCENT_DIM, outline=ACCENT, width=1)
        badge.create_text(11, 11, text=str(number), fill=ACCENT, font=("Consolas", 8, "bold"))

        tk.Label(top, text=title, bg=CARD_BG, fg=TEXT_PRI,
                 font=("Consolas", 9, "bold")).pack(side="left")

        tk.Label(inner, text=desc, bg=CARD_BG, fg=TEXT_SEC,
                 font=FONT_STEP, justify="left", wraplength=480).pack(anchor="w", pady=(2, 0))


class AppGUI:
    def __init__(self, root):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.root = root
        self.root.title("AI OCR — Trích Xuất Văn Bản")
        self.root.geometry("780x680")
        self.root.configure(bg=DARK_BG)
        self.root.resizable(True, True)
        self.root.minsize(680, 580)

        self._build_ui()
        sys.stdout = self.console

    def _build_ui(self):
        # ── Outer padding frame
        outer = tk.Frame(self.root, bg=DARK_BG)
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        # ── HEADER ──────────────────────────────────────────────
        hdr = tk.Frame(outer, bg=DARK_BG)
        hdr.pack(fill="x", pady=(0, 16))

        left_hdr = tk.Frame(hdr, bg=DARK_BG)
        left_hdr.pack(side="left")

        # Logo mark
        logo_c = tk.Canvas(left_hdr, width=38, height=38, bg=DARK_BG, highlightthickness=0)
        logo_c.pack(side="left", padx=(0, 12))
        logo_c.create_rectangle(0, 0, 38, 38, fill=ACCENT_DIM, outline=ACCENT, width=1)
        logo_c.create_text(19, 19, text="AI", fill=ACCENT, font=("Consolas", 14, "bold"))

        title_frame = tk.Frame(left_hdr, bg=DARK_BG)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="TRÍCH XUẤT THÔNG TIN VĂN BẢN",
                 bg=DARK_BG, fg=TEXT_PRI, font=("Consolas", 13, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="AI-powered OCR Document Extractor",
                 bg=DARK_BG, fg=TEXT_SEC, font=FONT_STEP).pack(anchor="w")

        # Version badge
        ver_frame = tk.Frame(hdr, bg=ACCENT_DIM, padx=8, pady=4)
        ver_frame.pack(side="right", anchor="n")
        tk.Label(ver_frame, text="v1.0.0", bg=ACCENT_DIM, fg=ACCENT, font=FONT_STEP).pack()

        # Divider
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))

        # ── DEV INFO ───────────────────────────────────────────
        dev = tk.Frame(outer, bg=PANEL_BG, padx=14, pady=8)
        dev.pack(fill="x", pady=(0, 14))
        info_items = [
            ("DEV", "Nguyễn Thanh Tùng"),
            ("TEL", "0833.270.594"),
            ("EMAIL", "wind.gemini.165@gmail.com"),
        ]
        for i, (lbl, val) in enumerate(info_items):
            col = tk.Frame(dev, bg=PANEL_BG)
            col.pack(side="left", padx=(0 if i == 0 else 20, 0))
            tk.Label(col, text=lbl, bg=PANEL_BG, fg=TEXT_MUTED, font=FONT_STEP).pack(anchor="w")
            tk.Label(col, text=val, bg=PANEL_BG, fg=TEXT_SEC, font=("Consolas", 9)).pack(anchor="w")

        # ── WORKFLOW STEPS ──────────────────────────────────────
        steps_frame = tk.LabelFrame(outer, text="  WORKFLOW  ", bg=DARK_BG,
                                    fg=TEXT_SEC, font=FONT_STEP,
                                    relief="flat", bd=0, labelanchor="nw")
        steps_frame.pack(fill="x", pady=(0, 14))

        steps = [
            (1, "Chuẩn bị",         "Thư mục 'output' và file 'ket_qua_ocr.xlsx' cũ được xóa tự động khi chạy."),
            (2, "Đặt PDF vào thư mục",  "Copy tất cả file PDF cần xử lý vào thư mục  pdf/  ở thư mục gốc."),
            (3, "Xử lý PDF → Ảnh",   "Nhấn nút [1. XỬ LÝ PDF] để chuyển đổi từng trang PDF thành ảnh."),
            (4, "OCR & Trích xuất",  "Nhấn nút [2. TRÍCH XUẤT] để AI đọc & xuất kết quả ra  ket_qua_ocr.xlsx."),
        ]
        for s in steps:
            card = StepCard(steps_frame, *s)
            card.pack(fill="x", pady=2)

        # ── ACTIONS ROW ─────────────────────────────────────────
        action_frame = tk.Frame(outer, bg=DARK_BG)
        action_frame.pack(fill="x", pady=(0, 12))

        # Left: buttons
        btn_area = tk.Frame(action_frame, bg=DARK_BG)
        btn_area.pack(side="left")

        self.btn_pdf = AnimatedButton(btn_area, text="1. XỬ LÝ PDF",
                                      icon="⬛", state_color=ACCENT,
                                      command=self.run_pdf2img,
                                      width=190, height=52)
        self.btn_pdf.pack(side="left", padx=(0, 10))

        self.btn_ocr = AnimatedButton(btn_area, text="2. TRÍCH XUẤT",
                                      icon="◈", state_color=SUCCESS,
                                      command=self.run_ocr,
                                      width=190, height=52)
        self.btn_ocr.pack(side="left")

        # Right: status panel
        status_panel = tk.Frame(action_frame, bg=PANEL_BG, padx=14, pady=8)
        status_panel.pack(side="right")

        tk.Label(status_panel, text="TRẠNG THÁI", bg=PANEL_BG,
                 fg=TEXT_MUTED, font=FONT_STEP).pack(anchor="w")

        st_row = tk.Frame(status_panel, bg=PANEL_BG)
        st_row.pack(anchor="w", pady=(4, 0))
        self.status_dot = StatusDot(st_row)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_lbl = tk.Label(st_row, text="Sẵn sàng", bg=PANEL_BG,
                                   fg=TEXT_SEC, font=("Consolas", 9))
        self.status_lbl.pack(side="left")

        # ── CONSOLE ─────────────────────────────────────────────
        self.console = LogConsole(outer)
        self.console.pack(fill="both", expand=True)

        # Bottom bar
        bottom = tk.Frame(outer, bg=DARK_BG, pady=6)
        bottom.pack(fill="x")
        tk.Label(bottom, text="★ Kết quả lưu tại:  ket_qua_ocr.xlsx  (thư mục gốc)",
                 bg=DARK_BG, fg=TEXT_MUTED, font=FONT_STEP).pack(side="left")

    # ── Helpers ───────────────────────────────────────────────────
    def _set_status(self, text, dot_state="idle"):
        self.status_lbl.config(text=text)
        self.status_dot.set_state(dot_state)

    def check_output_exists(self):
        output_path = os.path.join(self.base_dir, "output")
        if not os.path.exists(output_path):
            return False
        files = [f for f in os.listdir(output_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        return len(files) > 0

    # ── PDF Task ──────────────────────────────────────────────────
    def run_pdf2img(self):
        self.btn_pdf.set_enabled(False)
        self._set_status("Đang xử lý PDF...", "running")
        threading.Thread(target=self._execute_pdf_task, daemon=True).start()

    def _execute_pdf_task(self):
        print("\n[HỆ THỐNG] Đang bắt đầu xử lý PDF...")
        try:
            importlib.reload(pdf2img)
            pdf2img.main()
            self.root.after(0, lambda: self._set_status("PDF xong ✓", "done"))
            print("[HỆ THỐNG] Xử lý PDF hoàn thành ✓")
        except Exception as e:
            print(f"[LỖI] {str(e)}")
            self.root.after(0, lambda: self._set_status("Lỗi PDF", "error"))
        finally:
            self.root.after(0, lambda: self.btn_pdf.set_enabled(True))

    # ── OCR Task ──────────────────────────────────────────────────
    def run_ocr(self):
        if not self.check_output_exists():
            messagebox.showwarning(
                "Cảnh báo",
                "Thư mục 'output' chưa có ảnh!\nVui lòng thực hiện Bước 1 (Xử lý PDF) trước."
            )
            return
        self.btn_ocr.set_enabled(False)
        self._set_status("Đang trích xuất AI...", "running")
        threading.Thread(target=self._execute_ocr_task, daemon=True).start()

    def _execute_ocr_task(self):
        print("[HỆ THỐNG] Đang bắt đầu trích xuất dữ liệu OCR...")
        try:
            importlib.reload(main_v4)
            main_v4.main()
            self.root.after(0, lambda: self._set_status("Hoàn thành ✓", "done"))
            self.root.after(0, lambda: messagebox.showinfo("Hoàn thành", "Đã trích xuất xong!\nKết quả lưu tại ket_qua_ocr.xlsx"))
        except Exception as e:
            print(f"[LỖI] {str(e)}")
            self.root.after(0, lambda: self._set_status("Lỗi OCR", "error"))
        finally:
            self.root.after(0, lambda: self.btn_ocr.set_enabled(True))

    def flush(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()