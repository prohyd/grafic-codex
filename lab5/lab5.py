import random
import turtle


EPS = 1e-9
SCALE = 36


def polygon_area(points):
    area = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def ensure_ccw(points):
    if polygon_area(points) < 0:
        return list(reversed(points))
    return points[:]


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def point_in_triangle(p, a, b, c):
    s1 = cross(a, b, p)
    s2 = cross(b, c, p)
    s3 = cross(c, a, p)
    has_neg = s1 < -EPS or s2 < -EPS or s3 < -EPS
    has_pos = s1 > EPS or s2 > EPS or s3 > EPS
    return not (has_neg and has_pos)


def triangulate_convex_fan(points):
    points = ensure_ccw(points)
    triangles = []
    for i in range(1, len(points) - 1):
        triangles.append([points[0], points[i], points[i + 1]])
    return triangles


def is_ear(prev_pt, curr_pt, next_pt, polygon):
    if cross(prev_pt, curr_pt, next_pt) <= EPS:
        return False

    for pt in polygon:
        if pt in (prev_pt, curr_pt, next_pt):
            continue
        if point_in_triangle(pt, prev_pt, curr_pt, next_pt):
            return False
    return True


def ear_clipping(points):
    polygon = ensure_ccw(points)
    work = polygon[:]
    triangles = []

    while len(work) > 3:
        ear_found = False
        n = len(work)
        for i in range(n):
            prev_pt = work[(i - 1) % n]
            curr_pt = work[i]
            next_pt = work[(i + 1) % n]

            if is_ear(prev_pt, curr_pt, next_pt, work):
                triangles.append([prev_pt, curr_pt, next_pt])
                del work[i]
                ear_found = True
                break

        if not ear_found:
            raise ValueError("Не удалось выполнить триангуляцию.")

    triangles.append([work[0], work[1], work[2]])
    return triangles


def merge_outer_and_hole(outer, hole):
    outer = ensure_ccw(outer)
    hole = ensure_ccw(hole)
    hole = list(reversed(hole))

    hole_index = max(range(len(hole)), key=lambda i: (hole[i][0], -hole[i][1]))
    outer_index = max(range(len(outer)), key=lambda i: (outer[i][0], -outer[i][1]))

    merged = []
    for i in range(len(outer)):
        merged.append(outer[i])
        if i == outer_index:
            bridge_hole = hole[hole_index]
            bridge_outer = outer[outer_index]
            merged.append(bridge_hole)
            for j in range(1, len(hole)):
                idx = (hole_index + j) % len(hole)
                merged.append(hole[idx])
            merged.append(bridge_hole)
            merged.append(bridge_outer)

    cleaned = []
    for pt in merged:
        if not cleaned or cleaned[-1] != pt:
            cleaned.append(pt)
    if cleaned and cleaned[0] == cleaned[-1]:
        cleaned.pop()
    return cleaned


def to_screen(point, shift_x, shift_y):
    return point[0] * SCALE + shift_x, point[1] * SCALE + shift_y


def draw_label(x, y, text):
    turtle.penup()
    turtle.goto(x, y)
    turtle.pencolor("black")
    turtle.write(text, align="center", font=("Arial", 12, "bold"))


def draw_polygon(points, shift_x, shift_y, color):
    turtle.penup()
    x0, y0 = to_screen(points[0], shift_x, shift_y)
    turtle.goto(x0, y0)
    turtle.pencolor(color)
    turtle.pensize(2)
    turtle.pendown()

    for point in points[1:]:
        turtle.goto(*to_screen(point, shift_x, shift_y))
    turtle.goto(x0, y0)

    for i, point in enumerate(points, 1):
        x, y = to_screen(point, shift_x, shift_y)
        turtle.penup()
        turtle.goto(x, y)
        turtle.dot(6, "black")
        turtle.goto(x + 8, y + 8)
        turtle.write(str(i), font=("Arial", 8, "normal"))


def draw_triangle(triangle, shift_x, shift_y, color):
    turtle.penup()
    x0, y0 = to_screen(triangle[0], shift_x, shift_y)
    turtle.goto(x0, y0)
    turtle.fillcolor(color)
    turtle.pencolor("black")
    turtle.pensize(1)
    turtle.begin_fill()
    turtle.pendown()

    for point in triangle[1:]:
        turtle.goto(*to_screen(point, shift_x, shift_y))
    turtle.goto(x0, y0)
    turtle.end_fill()


def draw_triangles(triangles, shift_x, shift_y):
    for i, triangle in enumerate(triangles, 1):
        color = (
            random.random(),
            random.random(),
            random.random(),
        )
        draw_triangle(triangle, shift_x, shift_y, color)

        cx = sum(p[0] for p in triangle) / 3
        cy = sum(p[1] for p in triangle) / 3
        sx, sy = to_screen((cx, cy), shift_x, shift_y)
        turtle.penup()
        turtle.goto(sx, sy)
        turtle.pencolor("black")
        turtle.write(str(i), align="center", font=("Arial", 8, "bold"))


def main():
    random.seed(7)

    convex_polygon = [
        (-5, -1),
        (-3, -3),
        (1, -4),
        (5, -2),
        (6, 1),
        (3, 4),
        (-1, 5),
        (-4, 3),
    ]

    monotone_polygon = [
        (-5, -3),
        (-2, -4),
        (2, -3),
        (5, -1),
        (6, 2),
        (3, 5),
        (0, 4),
        (-3, 2),
        (-4, 0),
    ]

    outer_with_hole = [
        (-6, -4),
        (6, -4),
        (6, 4),
        (-6, 4),
    ]
    hole = [
        (-1.5, -1.5),
        (1.5, -1.5),
        (1.5, 1.5),
        (-1.5, 1.5),
    ]

    fan_triangles = triangulate_convex_fan(convex_polygon)
    ear_triangles = ear_clipping(monotone_polygon)
    merged_polygon = merge_outer_and_hole(outer_with_hole, hole)
    hole_triangles = ear_clipping(merged_polygon)

    print("Лабораторная работа 5. Триангуляция полигона")
    print("Задача A: выпуклый полигон ->", len(fan_triangles), "треугольников")
    print("Задача Б: монотонный полигон ->", len(ear_triangles), "треугольников")
    print("Задача В: полигон с отверстием ->", len(hole_triangles), "треугольников")

    screen = turtle.Screen()
    screen.title("Lab 5")
    screen.setup(width=1800, height=1000)

    turtle.speed(0)
    turtle.hideturtle()
    turtle.tracer(False)

    draw_label(-620, 420, "Задача A: исходный выпуклый полигон")
    draw_polygon(convex_polygon, -620, 210, "blue")
    draw_label(-620, -40, "Задача A: триангуляция веером")
    draw_triangles(fan_triangles, -620, -270)

    draw_label(0, 420, "Задача Б: монотонный полигон")
    draw_polygon(monotone_polygon, 0, 210, "green")
    draw_label(0, -40, "Задача Б: ear clipping")
    draw_triangles(ear_triangles, 0, -270)

    draw_label(620, 420, "Задача В: полигон с отверстием")
    draw_polygon(outer_with_hole, 620, 210, "red")
    draw_polygon(hole, 620, 210, "orange")
    draw_label(620, -40, "Задача В: после преобразования")
    draw_triangles(hole_triangles, 620, -270)

    turtle.update()
    turtle.done()


if __name__ == "__main__":
    main()
