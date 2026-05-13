import math
import random
import tkinter as tk
from tkinter import ttk


WIDTH = 980
HEIGHT = 620
PANEL = 250
CANVAS_W = WIDTH - PANEL
GROUND_Y = HEIGHT - 34
DT = 1 / 60


class Particle:
    def __init__(self, x, y, vx, vy, ax, ay, life, size, color1, color2=None, kind="circle", frame=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ax = ax
        self.ay = ay
        self.life = life
        self.max_life = life
        self.size = size
        self.start_size = size
        self.color1 = color1
        self.color2 = color2 or color1
        self.kind = kind
        self.frame = frame
        self.angle = random.random() * math.tau
        self.spin = random.uniform(-3.0, 3.0)

    @property
    def t(self):
        return max(0.0, min(1.0, 1.0 - self.life / self.max_life))

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        self.life -= dt


def mix_color(a, b, k):
    k = max(0.0, min(1.0, k))
    ar, ag, ab = a
    br, bg, bb = b
    return (
        int(ar + (br - ar) * k),
        int(ag + (bg - ag) * k),
        int(ab + (bb - ab) * k),
    )


def rgb(color):
    return "#{:02x}{:02x}{:02x}".format(*color)


class ParticleSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab 17 - Particle System")
        self.root.resizable(False, False)

        self.mode = tk.StringVar(value="firework")
        self.weather = tk.StringVar(value="rain")
        self.paused = tk.BooleanVar(value=False)
        self.particles = []
        self.images = []
        self.last_burst = 0.0
        self.time = 0.0
        self.wind = 0.0
        self.mouse_down = False

        self.build_ui()
        self.make_fire_sprites()
        self.bind_events()
        self.reset()
        self.tick()

    def build_ui(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=HEIGHT, bg="#080b14", highlightthickness=0)
        self.canvas.grid(row=0, column=0)

        panel = ttk.Frame(self.root, padding=12)
        panel.grid(row=0, column=1, sticky="nsew")

        ttk.Label(panel, text="Задание 17", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(panel, text="Система частиц").pack(anchor="w", pady=(0, 12))

        ttk.Label(panel, text="Эффект:").pack(anchor="w")
        modes = [
            ("A: фейерверк", "firework"),
            ("Б: дождь / снег", "weather"),
            ("В: огонь", "fire"),
        ]
        for text, value in modes:
            ttk.Radiobutton(panel, text=text, variable=self.mode, value=value, command=self.reset).pack(anchor="w")

        ttk.Separator(panel).pack(fill="x", pady=10)
        ttk.Label(panel, text="Настройки:").pack(anchor="w")

        self.amount = tk.IntVar(value=130)
        ttk.Label(panel, text="Количество частиц").pack(anchor="w", pady=(5, 0))
        ttk.Scale(panel, from_=30, to=260, variable=self.amount, orient="horizontal").pack(fill="x")

        self.gravity = tk.DoubleVar(value=150.0)
        ttk.Label(panel, text="Гравитация").pack(anchor="w", pady=(8, 0))
        ttk.Scale(panel, from_=0, to=420, variable=self.gravity, orient="horizontal").pack(fill="x")

        self.wind_var = tk.DoubleVar(value=0.0)
        ttk.Label(panel, text="Ветер").pack(anchor="w", pady=(8, 0))
        ttk.Scale(panel, from_=-120, to=120, variable=self.wind_var, orient="horizontal").pack(fill="x")

        ttk.Label(panel, text="Для задачи Б:").pack(anchor="w", pady=(12, 0))
        ttk.Radiobutton(panel, text="Дождь", variable=self.weather, value="rain", command=self.reset).pack(anchor="w")
        ttk.Radiobutton(panel, text="Снег", variable=self.weather, value="snow", command=self.reset).pack(anchor="w")

        ttk.Separator(panel).pack(fill="x", pady=10)
        ttk.Checkbutton(panel, text="Пауза", variable=self.paused).pack(anchor="w")
        ttk.Button(panel, text="Сброс", command=self.reset).pack(fill="x", pady=(8, 2))
        ttk.Button(panel, text="Взрыв по центру", command=lambda: self.spawn_firework(CANVAS_W / 2, HEIGHT / 2)).pack(
            fill="x", pady=2
        )

        ttk.Separator(panel).pack(fill="x", pady=10)
        text = (
            "Что реализовано:\n"
            "A - частицы летят из одной точки,\n"
            "    имеют случайные скорости и\n"
            "    меняют цвет за время жизни.\n"
            "Б - бесконечный дождь/снег,\n"
            "    есть простая гравитация.\n"
            "В - огонь из billboard-спрайтов,\n"
            "    кадры текстуры меняются,\n"
            "    яркие слои имитируют additive."
        )
        ttk.Label(panel, text=text, justify="left").pack(anchor="w", pady=(4, 0))

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", lambda _event: setattr(self, "mouse_down", False))

    def make_fire_sprites(self):
        self.fire_sprites = []
        palettes = [
            ("#fff7b0", "#ff9b23", "#e93913"),
            ("#ffe46b", "#ff7226", "#b71910"),
            ("#ffc54d", "#ef4d1c", "#5b1414"),
            ("#e6e6e6", "#777777", "#222222"),
        ]
        for c0, c1, c2 in palettes:
            img = tk.PhotoImage(width=28, height=28)
            cx, cy = 14, 15
            for y in range(28):
                for x in range(28):
                    d = math.hypot((x - cx) / 13, (y - cy) / 12)
                    if d > 1:
                        continue
                    if d < 0.32:
                        col = c0
                    elif d < 0.68:
                        col = c1
                    else:
                        col = c2
                    img.put(col, (x, y))
            self.fire_sprites.append(img)

    def reset(self):
        self.particles.clear()
        self.time = 0.0
        self.last_burst = 0.0
        self.canvas.delete("all")
        if self.mode.get() == "weather":
            for _ in range(self.amount.get()):
                self.spawn_weather(random.uniform(0, CANVAS_W), random.uniform(-HEIGHT, HEIGHT))
        elif self.mode.get() == "fire":
            for _ in range(self.amount.get() // 2):
                self.spawn_fire()
        else:
            self.spawn_firework(CANVAS_W / 2, HEIGHT / 2)

    def on_click(self, event):
        self.mouse_down = True
        if self.mode.get() == "firework":
            self.spawn_firework(event.x, event.y)
        elif self.mode.get() == "fire":
            for _ in range(16):
                self.spawn_fire(event.x)

    def on_drag(self, event):
        if self.mode.get() == "fire":
            for _ in range(5):
                self.spawn_fire(event.x)

    def spawn_firework(self, x, y):
        base = random.choice(
            [
                (255, 83, 73),
                (255, 210, 74),
                (87, 210, 255),
                (180, 119, 255),
                (96, 255, 154),
            ]
        )
        n = self.amount.get()
        for _ in range(n):
            angle = random.random() * math.tau
            speed = random.uniform(70, 260)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            end = mix_color(base, (20, 20, 35), random.uniform(0.65, 1.0))
            life = random.uniform(1.2, 2.6)
            size = random.uniform(2.0, 4.2)
            self.particles.append(Particle(x, y, vx, vy, 0, self.gravity.get(), life, size, base, end))

    def spawn_weather(self, x=None, y=None):
        wind = self.wind_var.get()
        if self.weather.get() == "rain":
            x = random.uniform(-40, CANVAS_W + 40) if x is None else x
            y = random.uniform(-80, -5) if y is None else y
            vx = wind + random.uniform(-20, 20)
            vy = random.uniform(360, 520)
            self.particles.append(Particle(x, y, vx, vy, 0, self.gravity.get() * 0.4, 2.8, 1.5, (130, 180, 255), kind="rain"))
        else:
            x = random.uniform(-40, CANVAS_W + 40) if x is None else x
            y = random.uniform(-80, -5) if y is None else y
            vx = wind + random.uniform(-35, 35)
            vy = random.uniform(45, 110)
            self.particles.append(
                Particle(x, y, vx, vy, 0, self.gravity.get() * 0.06, random.uniform(5, 8), random.uniform(2, 4), (245, 248, 255), kind="snow")
            )

    def spawn_fire(self, x=None):
        x = random.uniform(CANVAS_W * 0.38, CANVAS_W * 0.62) if x is None else x + random.uniform(-18, 18)
        y = GROUND_Y + random.uniform(-8, 8)
        vx = self.wind_var.get() * 0.28 + random.uniform(-28, 28)
        vy = random.uniform(-170, -70)
        life = random.uniform(0.7, 1.35)
        size = random.uniform(0.65, 1.25)
        frame = random.randrange(len(self.fire_sprites))
        self.particles.append(Particle(x, y, vx, vy, 0, -35, life, size, (255, 220, 100), (80, 80, 80), "fire", frame))

    def update_particles(self):
        mode = self.mode.get()
        target = self.amount.get()
        if mode == "weather":
            while len(self.particles) < target:
                self.spawn_weather()
        elif mode == "fire":
            for _ in range(max(2, target // 18)):
                self.spawn_fire()
        elif self.time - self.last_burst > 2.0:
            self.last_burst = self.time
            self.spawn_firework(random.uniform(90, CANVAS_W - 90), random.uniform(120, HEIGHT * 0.55))

        alive = []
        for p in self.particles:
            if mode == "weather" and p.kind == "snow":
                p.ax = math.sin(self.time * 1.7 + p.angle) * 18
            p.update(DT)
            if mode == "weather" and (p.y > HEIGHT + 50 or p.x < -90 or p.x > CANVAS_W + 90):
                self.spawn_weather()
                continue
            if mode == "fire" and p.t > 0.48:
                p.frame = min(len(self.fire_sprites) - 1, p.frame + 1)
            if p.alive and len(alive) < 900:
                alive.append(p)
        self.particles = alive

    def draw_background(self):
        mode = self.mode.get()
        if mode == "weather":
            self.canvas.create_rectangle(0, 0, CANVAS_W, HEIGHT, fill="#101622", outline="")
            self.canvas.create_rectangle(0, GROUND_Y, CANVAS_W, HEIGHT, fill="#202833", outline="")
            for x in range(0, CANVAS_W, 90):
                self.canvas.create_line(x, GROUND_Y, x + 60, HEIGHT, fill="#2d3744")
        elif mode == "fire":
            self.canvas.create_rectangle(0, 0, CANVAS_W, HEIGHT, fill="#100b08", outline="")
            self.canvas.create_rectangle(0, GROUND_Y + 5, CANVAS_W, HEIGHT, fill="#23130d", outline="")
            self.canvas.create_oval(CANVAS_W * 0.36, GROUND_Y - 28, CANVAS_W * 0.64, GROUND_Y + 32, fill="#37170a", outline="")
        else:
            self.canvas.create_rectangle(0, 0, CANVAS_W, HEIGHT, fill="#080b18", outline="")
            for _ in range(35):
                # Звезды рисуются детерминированно от текущего времени, чтобы фон не мелькал.
                pass
            random.seed(17)
            for _ in range(75):
                x = random.randint(0, CANVAS_W)
                y = random.randint(0, HEIGHT - 80)
                color = random.choice(["#2d375d", "#465481", "#7984aa"])
                self.canvas.create_rectangle(x, y, x + 1, y + 1, fill=color, outline="")
            random.seed()

    def draw_particles(self):
        for p in self.particles:
            fade = 1.0 - p.t
            if p.kind == "rain":
                length = 18 + abs(p.vy) * 0.03
                self.canvas.create_line(p.x, p.y, p.x - 6, p.y + length, fill="#79a8ff", width=2)
            elif p.kind == "snow":
                r = p.size * (0.75 + 0.3 * math.sin(self.time * 5 + p.angle))
                self.canvas.create_oval(p.x - r, p.y - r, p.x + r, p.y + r, fill="#f4f8ff", outline="")
            elif p.kind == "fire":
                scale = p.size * (1.2 - p.t * 0.55)
                img = self.fire_sprites[p.frame % len(self.fire_sprites)]
                self.canvas.create_image(p.x, p.y, image=img)
                if p.t < 0.55:
                    r = 10 * scale
                    # Яркое пятно поверх спрайта имитирует аддитивное смешивание цветов.
                    self.canvas.create_oval(p.x - r, p.y - r, p.x + r, p.y + r, outline="#ffce4b")
            else:
                color = rgb(mix_color(p.color1, p.color2, p.t))
                r = max(0.7, p.size * fade)
                self.canvas.create_oval(p.x - r, p.y - r, p.x + r, p.y + r, fill=color, outline="")
                if p.t < 0.55:
                    tail_x = p.x - p.vx * 0.035
                    tail_y = p.y - p.vy * 0.035
                    self.canvas.create_line(p.x, p.y, tail_x, tail_y, fill=color)

    def redraw(self):
        self.canvas.delete("all")
        self.draw_background()
        self.draw_particles()
        info = f"Частиц: {len(self.particles)}   t = {self.time:5.1f} c"
        self.canvas.create_text(12, 14, text=info, fill="#d7deff", anchor="w", font=("Segoe UI", 10))

    def tick(self):
        if not self.paused.get():
            self.time += DT
            self.update_particles()
            self.redraw()
        self.root.after(int(DT * 1000), self.tick)


def main():
    root = tk.Tk()
    ParticleSystemApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
