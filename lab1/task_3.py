import pygame
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

polygon = [(400,200),(450,300),(550,300),(470,370),
           (500,480),(400,420),(300,480),(330,370),
           (250,300),(350,300)]

center = (400, 300)
angle = 0

def rotate(point, center, angle):
    x, y = point
    cx, cy = center
    rad = math.radians(angle)
    return (
        cx + (x - cx)*math.cos(rad) - (y - cy)*math.sin(rad),
        cy + (x - cx)*math.sin(rad) + (y - cy)*math.cos(rad)
    )

# функция сглаженной линии
def draw_aa_polygon(surface, color, points):
    temp = pygame.Surface((800, 600), pygame.SRCALPHA)

    # толстая полупрозрачная линия (создаёт мягкость)
    pygame.draw.polygon(temp, (*color, 50), points)

    # чёткий контур
    pygame.draw.aalines(temp, color, True, points)

    surface.blit(temp, (0, 0))

running = True
while running:
    screen.fill(BLACK)

    angle += 1

    rotated = [rotate(p, center, angle) for p in polygon]
    pts = [(int(x), int(y)) for x, y in rotated]

    draw_aa_polygon(screen, WHITE, pts)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(100)

pygame.quit()