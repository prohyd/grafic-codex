import pygame
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)

polygon = [(200, 200), (300, 200), (250, 300)]

center = (400, 300)
angle = 0

drag = False
start_mouse_angle = 0
start_angle = 0

def get_angle(cx, cy, mx, my):
    return math.degrees(math.atan2(my - cy, mx - cx))

def rotate(p, c, a):
    x, y = p
    cx, cy = c
    r = math.radians(a)
    return (
        cx + (x - cx) * math.cos(r) - (y - cy) * math.sin(r),
        cy + (x - cx) * math.sin(r) + (y - cy) * math.cos(r)
    )

running = True
while running:
    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:  # ЛКМ — новый центр
                center = e.pos

            elif e.button == 3:  # ПКМ — начать вращение
                drag = True
                start_mouse_angle = get_angle(*center, *e.pos)
                start_angle = angle

        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 3:
                drag = False

        elif e.type == pygame.MOUSEMOTION and drag:
            current = get_angle(*center, *e.pos)
            angle = start_angle + (current - start_mouse_angle)

    rotated = [rotate(p, center, angle) for p in polygon]
    pts = [(int(x), int(y)) for x, y in rotated]

    screen.fill(BLACK)

    pygame.draw.polygon(screen, WHITE, pts, 1)
    pygame.draw.circle(screen, RED, center, 5)

    pygame.display.flip()

pygame.quit()