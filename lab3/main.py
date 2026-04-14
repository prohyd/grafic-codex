import math
import random
import turtle


# -------- Task A: regular Pythagoras tree (rectangles) --------
def draw_polygon(points):
    turtle.up()
    turtle.goto(points[0])
    turtle.down()
    for p in points[1:]:
        turtle.goto(p)
    turtle.goto(points[0])


def square_points(x, y, size, angle_deg):
    angle = math.radians(angle_deg)
    ux, uy = size * math.cos(angle), size * math.sin(angle)
    vx, vy = size * math.cos(angle + math.pi / 2), size * math.sin(angle + math.pi / 2)

    p0 = (x, y)
    p1 = (x + ux, y + uy)
    p2 = (p1[0] + vx, p1[1] + vy)
    p3 = (x + vx, y + vy)
    return p0, p1, p2, p3


def pythagoras_regular(x, y, size, angle_deg, depth):
    if depth == 0 or size < 1.5:
        return

    p0, p1, p2, p3 = square_points(x, y, size, angle_deg)
    draw_polygon([p0, p1, p2, p3])

    child_size = size * 0.5
    pythagoras_regular(p3[0], p3[1], child_size, angle_deg + 45, depth - 1)
    pythagoras_regular(p2[0], p2[1], child_size, angle_deg - 45, depth - 1)


# -------- Task B: irregular line tree --------
def branch_irregular(x, y, length, angle_deg, depth):
    if depth == 0 or length < 2.5:
        return

    a = math.radians(angle_deg)
    x2 = x + length * math.cos(a)
    y2 = y + length * math.sin(a)

    turtle.up()
    turtle.goto(x, y)
    turtle.down()
    turtle.goto(x2, y2)

    left_delta = random.uniform(20, 45)
    right_delta = random.uniform(20, 45)
    left_scale = random.uniform(0.62, 0.82)
    right_scale = random.uniform(0.62, 0.82)

    branch_irregular(x2, y2, length * left_scale, angle_deg + left_delta, depth - 1)
    branch_irregular(x2, y2, length * right_scale, angle_deg - right_delta, depth - 1)


# -------- Task C: L-system tree with leaves --------
L_SYSTEM = {
    "name": "fern",
    "axiom": "X",
    "rules": {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
    "angle": 25,
    "step": 3,
    "iter": 5,
}


def expand_lsystem(axiom, rules, iterations):
    current = axiom
    for _ in range(iterations):
        current = "".join(rules.get(ch, ch) for ch in current)
    return current


def draw_lsystem_tree(start_x, start_y, system_data):
    turtle.up()
    turtle.goto(start_x, start_y)
    turtle.setheading(90)
    turtle.down()

    sequence = expand_lsystem(system_data["axiom"], system_data["rules"], system_data["iter"])
    stack = []

    for ch in sequence:
        if ch == "F":
            turtle.forward(system_data["step"])
        elif ch == "f":
            turtle.up()
            turtle.forward(system_data["step"])
            turtle.down()
        elif ch == "+":
            turtle.left(system_data["angle"])
        elif ch == "-":
            turtle.right(system_data["angle"])
        elif ch == "[":
            stack.append((turtle.position(), turtle.heading()))
        elif ch == "]":
            turtle.color("forestgreen")
            turtle.dot(4)
            turtle.color("saddlebrown")
            pos, heading = stack.pop()
            turtle.up()
            turtle.goto(pos)
            turtle.setheading(heading)
            turtle.down()


def draw_label(x, y, text):
    turtle.up()
    turtle.goto(x, y)
    turtle.color("black")
    turtle.write(text, align="center", font=("Arial", 12, "bold"))


def main():
    screen = turtle.Screen()
    screen.title("Lab 3")
    screen.setup(width=1400, height=850)

    turtle.hideturtle()
    turtle.speed(0)
    turtle.tracer(False)

    random.seed(42)

    # Left panel: A
    turtle.pensize(1)
    turtle.color("darkblue")
    draw_label(-450, 320, "Task A: regular Pythagoras tree")
    pythagoras_regular(-520, -280, 90, 0, 7)

    # Center panel: B
    turtle.pensize(2)
    turtle.color("black")
    draw_label(0, 320, "Task B: irregular line tree")
    branch_irregular(0, -280, 95, 90, 9)

    # Right panel: V
    turtle.pensize(2)
    turtle.color("saddlebrown")
    draw_label(450, 320, "Task C: L-system + leaves")
    draw_lsystem_tree(450, -280, L_SYSTEM)

    turtle.update()
    turtle.done()


if __name__ == "__main__":
    main()
