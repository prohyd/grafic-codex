import math
import random
import tkinter as tk


WIDTH = 1350
HEIGHT = 520


def rotate(x, y, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return x * c - y * s, x * s + y * c


def to_local(point, center, angle):
    x = point[0] - center[0]
    y = point[1] - center[1]
    return rotate(x, y, -angle)


def to_world(point, center, angle):
    x, y = rotate(point[0], point[1], angle)
    return center[0] + x, center[1] + y


def rect_points(center, w, h, angle):
    pts = [
        (-w / 2, -h / 2),
        (w / 2, -h / 2),
        (w / 2, h / 2),
        (-w / 2, h / 2),
    ]
    return [to_world(p, center, angle) for p in pts]


def flatten(points):
    result = []
    for x, y in points:
        result.extend([x, y])
    return result


def code(x, y, xmin, ymin, xmax, ymax):
    c = 0
    if x < xmin:
        c |= 1
    elif x > xmax:
        c |= 2
    if y < ymin:
        c |= 4
    elif y > ymax:
        c |= 8
    return c


def cohen_sutherland(p1, p2, xmin, ymin, xmax, ymax):
    x1, y1 = p1
    x2, y2 = p2
    c1 = code(x1, y1, xmin, ymin, xmax, ymax)
    c2 = code(x2, y2, xmin, ymin, xmax, ymax)

    while True:
        if c1 == 0 and c2 == 0:
            return (x1, y1), (x2, y2)
        if c1 & c2:
            return None

        out = c1 if c1 != 0 else c2

        if out & 8:
            x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
            y = ymax
        elif out & 4:
            x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
            y = ymin
        elif out & 2:
            y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
            x = xmax
        else:
            y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
            x = xmin

        if out == c1:
            x1, y1 = x, y
            c1 = code(x1, y1, xmin, ymin, xmax, ymax)
        else:
            x2, y2 = x, y
            c2 = code(x2, y2, xmin, ymin, xmax, ymax)


def liang_barsky(p1, p2, xmin, ymin, xmax, ymax):
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    p = [-dx, dx, -dy, dy]
    q = [x1 - xmin, xmax - x1, y1 - ymin, ymax - y1]
    u1 = 0.0
    u2 = 1.0

    for pi, qi in zip(p, q):
        if abs(pi) < 1e-9:
            if qi < 0:
                return None
            continue
        t = qi / pi
        if pi < 0:
            u1 = max(u1, t)
        else:
            u2 = min(u2, t)
        if u1 > u2:
            return None

    return (x1 + u1 * dx, y1 + u1 * dy), (x1 + u2 * dx, y1 + u2 * dy)


def clip_segment_rotated_rect(p1, p2, center, w, h, angle, method):
    p1_local = to_local(p1, center, angle)
    p2_local = to_local(p2, center, angle)
    xmin, ymin, xmax, ymax = -w / 2, -h / 2, w / 2, h / 2

    if method == "cohen":
        cut = cohen_sutherland(p1_local, p2_local, xmin, ymin, xmax, ymax)
    else:
        cut = liang_barsky(p1_local, p2_local, xmin, ymin, xmax, ymax)

    if cut is None:
        return None

    a, b = cut
    return to_world(a, center, angle), to_world(b, center, angle)


def intersect(a, b, axis, value):
    x1, y1 = a
    x2, y2 = b
    if axis == "x":
        t = 0 if abs(x2 - x1) < 1e-9 else (value - x1) / (x2 - x1)
        return value, y1 + t * (y2 - y1)
    t = 0 if abs(y2 - y1) < 1e-9 else (value - y1) / (y2 - y1)
    return x1 + t * (x2 - x1), value


def clip_side(poly, axis, value, less_equal):
    if not poly:
        return []

    def inside(p):
        c = p[0] if axis == "x" else p[1]
        return c <= value + 1e-9 if less_equal else c >= value - 1e-9

    result = []
    prev = poly[-1]
    prev_inside = inside(prev)
    for cur in poly:
        cur_inside = inside(cur)
        if cur_inside:
            if not prev_inside:
                result.append(intersect(prev, cur, axis, value))
            result.append(cur)
        elif prev_inside:
            result.append(intersect(prev, cur, axis, value))
        prev = cur
        prev_inside = cur_inside
    return result


def clip_polygon_rotated_rect(points, center, w, h, angle):
    poly = [to_local(p, center, angle) for p in points]
    xmin, ymin, xmax, ymax = -w / 2, -h / 2, w / 2, h / 2
    poly = clip_side(poly, "x", xmin, False)
    poly = clip_side(poly, "x", xmax, True)
    poly = clip_side(poly, "y", ymin, False)
    poly = clip_side(poly, "y", ymax, True)
    return [to_world(p, center, angle) for p in poly]


def draw_rect(canvas, points, color, width):
    for i in range(4):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % 4]
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width)


def draw_case_a(canvas, ox):
    canvas.create_text(ox + 210, 25, text="Задача A: Сазерленд-Коэн", font=("Arial", 14, "bold"))
    center = (ox + 210, 270)
    clip_w, clip_h, clip_angle = 180, 180, 0
    clip_pts = rect_points(center, clip_w, clip_h, clip_angle)
    canvas.create_polygon(flatten(clip_pts), outline="orange", fill="", width=3)

    for i in range(24):
        size = 40 + i * 10
        cx = center[0] - 110 + i * 7
        cy = center[1] - 80 + i * 5
        pts = rect_points((cx, cy), size, size, 0)
        draw_rect(canvas, pts, "#b0b0b0", 1)
        for j in range(4):
            p1 = pts[j]
            p2 = pts[(j + 1) % 4]
            cut = clip_segment_rotated_rect(p1, p2, center, clip_w, clip_h, clip_angle, "cohen")
            if cut:
                canvas.create_line(cut[0][0], cut[0][1], cut[1][0], cut[1][1], fill="green", width=2)


def draw_case_b(canvas, ox):
    canvas.create_text(ox + 210, 25, text="Задача Б: Лианг-Барски", font=("Arial", 14, "bold"))
    center = (ox + 210, 270)
    clip_w, clip_h, clip_angle = 200, 140, math.radians(22)
    clip_pts = rect_points(center, clip_w, clip_h, clip_angle)
    canvas.create_polygon(flatten(clip_pts), outline="orange", fill="", width=3)

    for i in range(24):
        w = 50 + i * 7
        h = 30 + i * 5
        angle = math.radians((i * 14) % 180)
        cx = center[0] - 100 + i * 6
        cy = center[1] - 90 + i * 6
        pts = rect_points((cx, cy), w, h, angle)
        draw_rect(canvas, pts, "#b0b0b0", 1)
        for j in range(4):
            p1 = pts[j]
            p2 = pts[(j + 1) % 4]
            cut = clip_segment_rotated_rect(p1, p2, center, clip_w, clip_h, clip_angle, "liang")
            if cut:
                canvas.create_line(cut[0][0], cut[0][1], cut[1][0], cut[1][1], fill="green", width=2)


def draw_case_c(canvas, ox):
    canvas.create_text(ox + 210, 25, text="Задача В: хаотично + заливка", font=("Arial", 14, "bold"))
    center = (ox + 210, 270)
    clip_w, clip_h, clip_angle = 200, 150, math.radians(-18)
    clip_pts = rect_points(center, clip_w, clip_h, clip_angle)
    canvas.create_polygon(flatten(clip_pts), outline="orange", fill="", width=3)

    random.seed(7)
    for _ in range(28):
        w = random.randint(45, 150)
        h = random.randint(35, 120)
        angle = math.radians(random.randint(0, 179))
        cx = center[0] + random.randint(-140, 140)
        cy = center[1] + random.randint(-120, 120)
        pts = rect_points((cx, cy), w, h, angle)

        visible = clip_polygon_rotated_rect(pts, center, clip_w, clip_h, clip_angle)
        if len(visible) >= 3:
            canvas.create_polygon(flatten(visible), fill="#9ecbff", outline="", stipple="gray25")

        draw_rect(canvas, pts, "#b0b0b0", 1)
        for j in range(4):
            p1 = pts[j]
            p2 = pts[(j + 1) % 4]
            cut = clip_segment_rotated_rect(p1, p2, center, clip_w, clip_h, clip_angle, "liang")
            if cut:
                canvas.create_line(cut[0][0], cut[0][1], cut[1][0], cut[1][1], fill="green", width=2)


def main():
    root = tk.Tk()
    root.title("Лаба 1 - Задание 2")
    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="white")
    canvas.pack()

    draw_case_a(canvas, 20)
    draw_case_b(canvas, 460)
    draw_case_c(canvas, 900)

    root.mainloop()


if __name__ == "__main__":
    main()
