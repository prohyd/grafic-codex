import math
import random

import matplotlib.pyplot as plt


N = 13


def polygon_edges(points):
    for i in range(len(points)):
        yield points[i], points[(i + 1) % len(points)]


def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(a, b, c, d):
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def is_simple_polygon(points):
    edges = list(polygon_edges(points))
    m = len(edges)
    for i in range(m):
        a1, a2 = edges[i]
        for j in range(i + 1, m):
            b1, b2 = edges[j]
            if (j == (i + 1) % m) or (i == (j + 1) % m):
                continue
            if i == 0 and j == m - 1:
                continue
            if segments_intersect(a1, a2, b1, b2):
                return False
    return True


def generate_convex_polygon(n):
    cx = random.uniform(-2, 2)
    cy = random.uniform(-2, 2)
    a = random.uniform(8, 14)
    b = random.uniform(8, 14)
    angles = sorted(random.uniform(0, 2 * math.pi) for _ in range(n))
    points = []
    for angle in angles:
        x = cx + a * math.cos(angle)
        y = cy + b * math.sin(angle)
        points.append((round(x, 3), round(y, 3)))
    return points


def generate_star_polygon(n):
    cx, cy = 0.0, 0.0
    r_outer = 12.0
    r_inner = 5.5
    step = 2 * math.pi / n
    points = []
    for i in range(n):
        angle = i * step
        radius = r_outer if i % 2 == 0 else r_inner
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((round(x, 3), round(y, 3)))
    return points


def generate_self_intersecting_polygon(n):
    cx, cy = 0.0, 0.0
    step = 2 * math.pi / n
    points = []
    for i in range(n):
        angle = i * step
        radius = 3 + i * 1.1
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))

    if n >= 8:
        points[2], points[7] = points[7], points[2]
        points[4], points[9] = points[9], points[4]

    return [(round(x, 3), round(y, 3)) for x, y in points]


def print_polygon(name, points):
    print(f"\n{name}")
    for i, (x, y) in enumerate(points, 1):
        print(f"{i:02d}: ({x:7.3f}, {y:7.3f})")
    print("Simple polygon:", "YES" if is_simple_polygon(points) else "NO")


def draw_polygon(ax, points, title, color):
    xs = [p[0] for p in points] + [points[0][0]]
    ys = [p[1] for p in points] + [points[0][1]]

    ax.plot(xs, ys, color=color, linewidth=1.7)
    ax.scatter(xs[:-1], ys[:-1], color=color, s=24)

    for i, (x, y) in enumerate(points, 1):
        ax.text(x + 0.2, y + 0.2, str(i), fontsize=8)

    simple_text = "Simple: YES" if is_simple_polygon(points) else "Simple: NO"
    ax.set_title(f"{title}\n{simple_text}")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)


def main():
    random.seed()

    poly_a = generate_convex_polygon(N)
    poly_b = generate_star_polygon(N)
    poly_c = generate_self_intersecting_polygon(N)

    print("Lab 4. Polygon generation")
    print(f"Vertex count N = {N}")
    print_polygon("Task A: Convex polygon", poly_a)
    print_polygon("Task B: Star polygon", poly_b)
    print_polygon("Task C: Self-intersecting polygon", poly_c)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    draw_polygon(axes[0], poly_a, "Task A: Convex", "tab:blue")
    draw_polygon(axes[1], poly_b, "Task B: Star", "tab:green")
    draw_polygon(axes[2], poly_c, "Task C: Self-intersecting", "tab:red")

    fig.suptitle(f"Lab 4 - Polygon Generation (N={N})")
    plt.tight_layout()
    plt.savefig("lab4_result.png", dpi=160)
    plt.show()


if __name__ == "__main__":
    main()
