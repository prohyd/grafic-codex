import pygame
import math

pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Поворот отрезка (Брезенхем)")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Алгоритм Брезенхема
def draw_line(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= x1 < 800 and 0 <= y1 < 600:
            screen.set_at((x1, y1), WHITE)

        if x1 == x2 and y1 == y2:
            break

        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

# Поворот точки
def rotate_point(x, y, cx, cy, angle):
    rad = math.radians(angle)
    x_new = cx + (x - cx) * math.cos(rad) - (y - cy) * math.sin(rad)
    y_new = cy + (x - cx) * math.sin(rad) + (y - cy) * math.cos(rad)
    return int(x_new), int(y_new)

# Ввод
x1, y1 = map(int, input("Введите x1 y1: ").split())
x2, y2 = map(int, input("Введите x2 y2: ").split())
angle = float(input("Введите угол: "))

cx, cy = 400, 300  # центр

running = True
while running:
    screen.fill(BLACK)

    # поворот
    rx1, ry1 = rotate_point(x1, y1, cx, cy, angle)
    rx2, ry2 = rotate_point(x2, y2, cx, cy, angle)

    draw_line(rx1, ry1, rx2, ry2)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()