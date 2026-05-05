import math
import tkinter as tk
from tkinter import ttk


WIDTH = 900
HEIGHT = 600
PANEL = 230
CANVAS_W = WIDTH - PANEL
POINT_R = 7
SAMPLES = 180


class CurveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab 11 - Parametric curves")

        self.mode = tk.StringVar(value="bezier4")
        self.selected = None
        self.dragging = False
        self.show_polyline = tk.BooleanVar(value=True)

        self.points = [
            [85.0, 420.0],
            [210.0, 95.0],
            [420.0, 95.0],
            [570.0, 420.0],
        ]
        self.weights = [1.0, 1.0, 1.0, 1.0]

        self.build_ui()
        self.bind_events()
        self.redraw()

    def build_ui(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=HEIGHT, bg="#fbfbfb", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        panel = ttk.Frame(self.root, padding=12)
        panel.grid(row=0, column=1, sticky="nsew")

        ttk.Label(panel, text="Задание 11", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Параметрические кривые").pack(anchor="w", pady=(0, 12))

        ttk.Label(panel, text="Тип кривой:").pack(anchor="w")
        modes = [
            ("A: Безье 4 точки", "bezier4"),
            ("B: Безье n точек", "bezier"),
            ("B: B-Spline", "bspline"),
            ("B: Катмулл-Ром", "catmull"),
            ("В: NURBS", "nurbs"),
        ]
        for text, value in modes:
            ttk.Radiobutton(panel, text=text, value=value, variable=self.mode, command=self.on_mode).pack(anchor="w")

        ttk.Checkbutton(panel, text="Ломаная по точкам", variable=self.show_polyline, command=self.redraw).pack(
            anchor="w", pady=(10, 8)
        )

        ttk.Separator(panel).pack(fill="x", pady=8)
        ttk.Label(panel, text="Выбранная точка:").pack(anchor="w")
        self.point_info = ttk.Label(panel, text="нет")
        self.point_info.pack(anchor="w", pady=(0, 6))

        ttk.Label(panel, text="Вес точки (для NURBS):").pack(anchor="w")
        self.weight_var = tk.DoubleVar(value=1.0)
        self.weight_scale = ttk.Scale(panel, from_=0.2, to=6.0, orient="horizontal", variable=self.weight_var)
        self.weight_scale.pack(fill="x")
        self.weight_scale.configure(command=self.change_weight)
        self.weight_text = ttk.Label(panel, text="1.00")
        self.weight_text.pack(anchor="w", pady=(0, 8))

        ttk.Button(panel, text="Добавить точку", command=self.add_point_button).pack(fill="x", pady=2)
        ttk.Button(panel, text="Удалить выбранную", command=self.delete_selected).pack(fill="x", pady=2)
        ttk.Button(panel, text="Сбросить точки", command=self.reset_points).pack(fill="x", pady=2)

        ttk.Separator(panel).pack(fill="x", pady=10)
        text = (
            "Управление:\n"
            "ЛКМ - выбрать/тащить точку\n"
            "Двойной ЛКМ - добавить точку\n"
            "ПКМ - удалить точку\n\n"
            "Для NURBS выберите точку и меняйте ее вес."
        )
        ttk.Label(panel, text=text, justify="left").pack(anchor="w")

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.mouse_down)
        self.canvas.bind("<B1-Motion>", self.mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)
        self.canvas.bind("<Double-Button-1>", self.double_click)
        self.canvas.bind("<Button-3>", self.right_click)

    def on_mode(self):
        if self.mode.get() == "bezier4" and len(self.points) != 4:
            self.points = [
                [85.0, 420.0],
                [210.0, 95.0],
                [420.0, 95.0],
                [570.0, 420.0],
            ]
            self.weights = [1.0, 1.0, 1.0, 1.0]
            self.selected = None
        self.redraw()

    def reset_points(self):
        if self.mode.get() == "bezier4":
            self.points = [[85.0, 420.0], [210.0, 95.0], [420.0, 95.0], [570.0, 420.0]]
        else:
            self.points = [[70.0, 430.0], [160.0, 140.0], [285.0, 250.0], [405.0, 110.0], [555.0, 410.0]]
        self.weights = [1.0 for _ in self.points]
        self.selected = None
        self.redraw()

    def add_point_button(self):
        x = 90 + 70 * len(self.points)
        y = 260 + 120 * math.sin(len(self.points))
        self.add_point(min(x, CANVAS_W - 35), y)

    def add_point(self, x, y):
        if self.mode.get() == "bezier4" and len(self.points) >= 4:
            return
        self.points.append([float(x), float(y)])
        self.weights.append(1.0)
        self.selected = len(self.points) - 1
        self.redraw()

    def delete_selected(self):
        if self.selected is None:
            return
        min_count = 4 if self.mode.get() in ("bezier4", "bspline", "nurbs") else 2
        if len(self.points) <= min_count:
            return
        self.points.pop(self.selected)
        self.weights.pop(self.selected)
        self.selected = None
        self.redraw()

    def mouse_down(self, event):
        idx = self.find_point(event.x, event.y)
        self.selected = idx
        self.dragging = idx is not None
        self.redraw()

    def mouse_drag(self, event):
        if self.dragging and self.selected is not None:
            x = max(POINT_R, min(CANVAS_W - POINT_R, event.x))
            y = max(POINT_R, min(HEIGHT - POINT_R, event.y))
            self.points[self.selected] = [float(x), float(y)]
            self.redraw()

    def mouse_up(self, event):
        self.dragging = False

    def double_click(self, event):
        self.add_point(event.x, event.y)

    def right_click(self, event):
        idx = self.find_point(event.x, event.y)
        if idx is not None:
            self.selected = idx
            self.delete_selected()

    def find_point(self, x, y):
        for i, (px, py) in enumerate(self.points):
            if (px - x) ** 2 + (py - y) ** 2 <= (POINT_R + 5) ** 2:
                return i
        return None

    def change_weight(self, value):
        if self.selected is not None:
            self.weights[self.selected] = float(value)
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        self.draw_grid()

        curve = self.get_curve()
        if self.show_polyline.get() and len(self.points) > 1:
            flat = [coord for p in self.points for coord in p]
            self.canvas.create_line(*flat, fill="#888", width=1, dash=(4, 3))

        if len(curve) > 1:
            flat = [coord for p in curve for coord in p]
            color = "#1864ab" if self.mode.get() != "nurbs" else "#9c36b5"
            self.canvas.create_line(*flat, fill=color, width=3, smooth=True)

        for i, (x, y) in enumerate(self.points):
            if i == self.selected:
                fill = "#ffd43b"
                outline = "#e67700"
            else:
                fill = "#ffffff"
                outline = "#d9480f" if self.mode.get() == "nurbs" and self.weights[i] != 1.0 else "#222222"
            self.canvas.create_oval(x - POINT_R, y - POINT_R, x + POINT_R, y + POINT_R, fill=fill, outline=outline, width=2)
            label = str(i + 1)
            if self.mode.get() == "nurbs":
                label += f" w={self.weights[i]:.1f}"
            self.canvas.create_text(x, y - 18, text=label, fill="#333", font=("Segoe UI", 9))

        self.draw_basis_hint()
        self.update_panel()

    def draw_grid(self):
        for x in range(0, CANVAS_W, 50):
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#eeeeee")
        for y in range(0, HEIGHT, 50):
            self.canvas.create_line(0, y, CANVAS_W, y, fill="#eeeeee")

    def draw_basis_hint(self):
        if self.mode.get() != "bezier4" or len(self.points) != 4:
            return
        p = self.points
        for t in (0.25, 0.5, 0.75):
            a = self.lerp(p[0], p[1], t)
            b = self.lerp(p[1], p[2], t)
            c = self.lerp(p[2], p[3], t)
            d = self.lerp(a, b, t)
            e = self.lerp(b, c, t)
            q = self.lerp(d, e, t)
            self.canvas.create_line(a[0], a[1], b[0], b[1], c[0], c[1], fill="#adb5bd")
            self.canvas.create_line(d[0], d[1], e[0], e[1], fill="#74c0fc")
            self.canvas.create_oval(q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3, fill="#1864ab", outline="")

    def update_panel(self):
        if self.selected is None:
            self.point_info.configure(text="нет")
            self.weight_text.configure(text="-")
        else:
            x, y = self.points[self.selected]
            w = self.weights[self.selected]
            self.point_info.configure(text=f"{self.selected + 1}: x={x:.0f}, y={y:.0f}")
            self.weight_var.set(w)
            self.weight_text.configure(text=f"{w:.2f}")

    def get_curve(self):
        mode = self.mode.get()
        if mode == "bezier4":
            return self.bezier(self.points[:4]) if len(self.points) == 4 else []
        if mode == "bezier":
            return self.bezier(self.points) if len(self.points) >= 2 else []
        if mode == "bspline":
            return self.bspline(self.points) if len(self.points) >= 4 else []
        if mode == "catmull":
            return self.catmull_rom(self.points) if len(self.points) >= 2 else []
        if mode == "nurbs":
            return self.nurbs(self.points, self.weights) if len(self.points) >= 4 else []
        return []

    def bezier(self, pts):
        result = []
        for i in range(SAMPLES + 1):
            t = i / SAMPLES
            work = [p[:] for p in pts]
            while len(work) > 1:
                work = [self.lerp(work[j], work[j + 1], t) for j in range(len(work) - 1)]
            result.append(work[0])
        return result

    def bspline(self, pts):
        degree = 3
        knots = self.open_uniform_knots(len(pts), degree)
        start = knots[degree]
        end = knots[-degree - 1]
        result = []
        for s in range(SAMPLES + 1):
            t = start + (end - start) * s / SAMPLES
            if s == SAMPLES:
                t -= 1e-9
            x = 0.0
            y = 0.0
            for i, p in enumerate(pts):
                b = self.basis(i, degree, t, knots)
                x += p[0] * b
                y += p[1] * b
            result.append([x, y])
        return result

    def nurbs(self, pts, weights):
        degree = 3
        knots = self.open_uniform_knots(len(pts), degree)
        start = knots[degree]
        end = knots[-degree - 1]
        result = []
        for s in range(SAMPLES + 1):
            t = start + (end - start) * s / SAMPLES
            if s == SAMPLES:
                t -= 1e-9
            x_num = 0.0
            y_num = 0.0
            den = 0.0
            for i, p in enumerate(pts):
                b = self.basis(i, degree, t, knots) * weights[i]
                x_num += p[0] * b
                y_num += p[1] * b
                den += b
            if den != 0:
                result.append([x_num / den, y_num / den])
        return result

    def catmull_rom(self, pts):
        if len(pts) == 2:
            return pts[:]
        ext = [pts[0]] + pts + [pts[-1]]
        result = []
        steps = max(12, SAMPLES // (len(pts) - 1))
        for i in range(1, len(ext) - 2):
            p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
            for s in range(steps):
                t = s / steps
                t2 = t * t
                t3 = t2 * t
                x = 0.5 * (
                    2 * p1[0]
                    + (-p0[0] + p2[0]) * t
                    + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                    + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                )
                y = 0.5 * (
                    2 * p1[1]
                    + (-p0[1] + p2[1]) * t
                    + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                    + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                )
                result.append([x, y])
        result.append(pts[-1])
        return result

    def open_uniform_knots(self, n, degree):
        inside = n - degree - 1
        knots = [0.0] * (degree + 1)
        if inside > 0:
            for i in range(1, inside + 1):
                knots.append(i / (inside + 1))
        knots += [1.0] * (degree + 1)
        return knots

    def basis(self, i, degree, t, knots):
        if degree == 0:
            return 1.0 if knots[i] <= t < knots[i + 1] else 0.0

        left_den = knots[i + degree] - knots[i]
        right_den = knots[i + degree + 1] - knots[i + 1]
        left = 0.0
        right = 0.0
        if left_den != 0:
            left = (t - knots[i]) / left_den * self.basis(i, degree - 1, t, knots)
        if right_den != 0:
            right = (knots[i + degree + 1] - t) / right_den * self.basis(i + 1, degree - 1, t, knots)
        return left + right

    def lerp(self, a, b, t):
        return [a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t]


if __name__ == "__main__":
    root = tk.Tk()
    app = CurveApp(root)
    root.mainloop()
