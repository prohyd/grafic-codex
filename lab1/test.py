import pygame, math


def task_a():
    WIDTH, HEIGHT = 800, 600
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)

    def bresenham(x1, y1, x2, y2):
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        err = dx - dy

        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x1 += sx

            if e2 < dx:
                err += dx
                y1 += sy

        return points

    def rotate(x, y, cx, cy, angle):
        r = math.radians(angle)

        x -= cx
        y -= cy

        xr = x * math.cos(r) - y * math.sin(r)
        yr = x * math.sin(r) + y * math.cos(r)

        return int(xr + cx), int(yr + cy)

    x1 = int(input("x1: "))
    y1 = int(input("y1: "))
    x2 = int(input("x2: "))
    y2 = int(input("y2: "))

    cx = int(input("cx: "))
    cy = int(input("cy: "))
    angle = float(input("angle: "))

    rx1, ry1 = rotate(x1, y1, cx, cy, angle)
    rx2, ry2 = rotate(x2, y2, cx, cy, angle)

    running = True

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        for p in bresenham(x1, y1, x2, y2):
            screen.set_at(p, RED)

        for p in bresenham(rx1, ry1, rx2, ry2):
            screen.set_at(p, BLUE)

        pygame.display.flip()

    pygame.quit()

def task_b():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    triangle = [(300, 200), (400, 350), (200, 350)]

    center = None
    angle = 0

    def rotate(p, c, a):

        x, y = p
        cx, cy = c

        r = math.radians(a)

        x -= cx
        y -= cy

        xr = x * math.cos(r) - y * math.sin(r)
        yr = x * math.sin(r) + y * math.cos(r)

        return int(xr + cx), int(yr + cy)

    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                center = event.pos
                angle += 45

        screen.fill((255, 255, 255))

        pts = triangle

        if center:
            pts = [rotate(p, center, angle) for p in triangle]

        pygame.draw.polygon(screen, (0, 0, 255), pts, 2)

        pygame.display.flip()

    pygame.quit()

def task_c():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)

    polygon = [(400, 150), (450, 250), (550, 250), (470, 320),
               (500, 420), (400, 360), (300, 420), (330, 320),
               (250, 250), (350, 250)]

    center = (400, 300)
    angle = 0

    def rotate(p, c, a):

        x, y = p
        cx, cy = c

        r = math.radians(a)

        x -= cx
        y -= cy

        xr = x * math.cos(r) - y * math.sin(r)
        yr = x * math.sin(r) + y * math.cos(r)

        return int(xr + cx), int(yr + cy)

    running = True

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        rot = [rotate(p, center, angle) for p in polygon]

        pygame.draw.polygon(screen, BLUE, rot, 2)

        angle += 1

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()




if __name__ == '__main__':
    task_a()
