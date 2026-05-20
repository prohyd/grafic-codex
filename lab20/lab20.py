import math
import tkinter as tk
from tkinter import ttk


WIDTH = 1000
HEIGHT = 650
PANEL = 270
CANVAS_W = WIDTH - PANEL
CANVAS_H = HEIGHT
DT_MS = 16


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def angle_lerp_deg(a, b, t):
    diff = (b - a + 180) % 360 - 180
    return a + diff * t


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class Bone:
    def __init__(self, name, length, parent=-1):
        self.name = name
        self.length = length
        self.parent = parent
        self.local_angle = 0.0
        self.global_angle = 0.0
        self.start = (0.0, 0.0)
        self.end = (0.0, 0.0)


class Skeleton:
    def __init__(self):
        self.root = (245.0, 355.0)
        self.bones = [
            Bone("shoulder", 105, -1),
            Bone("upper arm", 95, 0),
            Bone("forearm", 85, 1),
            Bone("hand", 52, 2),
        ]

    def set_angles(self, angles):
        for bone, angle in zip(self.bones, angles):
            bone.local_angle = angle

    def angles(self):
        return [bone.local_angle for bone in self.bones]

    def forward(self):
        for i, bone in enumerate(self.bones):
            if bone.parent == -1:
                bone.start = self.root
                bone.global_angle = bone.local_angle
            else:
                parent = self.bones[bone.parent]
                bone.start = parent.end
                bone.global_angle = parent.global_angle + bone.local_angle

            rad = math.radians(bone.global_angle)
            bone.end = (
                bone.start[0] + math.cos(rad) * bone.length,
                bone.start[1] + math.sin(rad) * bone.length,
            )

    def joints(self):
        points = [self.root]
        points.extend(bone.end for bone in self.bones)
        return points

    def solve_ccd(self, target, iterations=12):
        self.forward()
        for _ in range(iterations):
            for i in range(len(self.bones) - 1, -1, -1):
                joint = self.bones[i].start
                end = self.bones[-1].end
                to_end = math.atan2(end[1] - joint[1], end[0] - joint[0])
                to_target = math.atan2(target[1] - joint[1], target[0] - joint[0])
                delta = math.degrees(to_target - to_end)
                delta = (delta + 180) % 360 - 180
                self.bones[i].local_angle += delta
                self.bones[i].local_angle = clamp(self.bones[i].local_angle, -170, 170)
                self.forward()
            if dist(self.bones[-1].end, target) < 2:
                break


class Lab20App:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab 20 - Skeletal Animation")
        self.root.resizable(False, False)

        self.skeleton = Skeleton()
        self.pose_a = [-35, 35, -25, 10]
        self.pose_b = [35, -70, 85, -30]
        self.target = (520, 300)
        self.time = 0.0
        self.paused = tk.BooleanVar(value=False)
        self.mode = tk.StringVar(value="animation")
        self.show_ghosts = tk.BooleanVar(value=True)
        self.speed = tk.DoubleVar(value=1.0)
        self.angle_vars = [tk.DoubleVar(value=a) for a in self.pose_a]
        self.info = tk.StringVar()

        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, bg="#f6f3ea", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.panel = ttk.Frame(root, width=PANEL, padding=12)
        self.panel.grid(row=0, column=1, sticky="nsew")
        self.panel.grid_propagate(False)

        self.build_panel()
        self.bind_events()
        self.reset_fk()
        self.tick()

    def build_panel(self):
        ttk.Label(self.panel, text="Lab 20: Skeletal Animation", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(self.panel, text="2D chain: shoulder -> upper arm -> forearm -> hand").pack(anchor="w", pady=(2, 10))

        modes = ttk.LabelFrame(self.panel, text="Mode")
        modes.pack(fill="x", pady=4)
        ttk.Radiobutton(modes, text="A: Forward kinematics", variable=self.mode, value="fk").pack(anchor="w")
        ttk.Radiobutton(modes, text="B: Pose interpolation", variable=self.mode, value="animation").pack(anchor="w")
        ttk.Radiobutton(modes, text="V: Inverse kinematics CCD", variable=self.mode, value="ik").pack(anchor="w")

        buttons = ttk.Frame(self.panel)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Reset A", command=self.reset_fk).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(buttons, text="Pose B", command=self.set_pose_b).pack(side="left", expand=True, fill="x", padx=(4, 0))

        ttk.Checkbutton(self.panel, text="Pause", variable=self.paused).pack(anchor="w")
        ttk.Checkbutton(self.panel, text="Show pose ghosts", variable=self.show_ghosts).pack(anchor="w")

        ttk.Label(self.panel, text="Animation speed").pack(anchor="w", pady=(10, 0))
        ttk.Scale(self.panel, from_=0.2, to=3.0, variable=self.speed, orient="horizontal").pack(fill="x")

        sliders = ttk.LabelFrame(self.panel, text="Local bone angles")
        sliders.pack(fill="x", pady=10)
        for i, (name, var) in enumerate(zip(["shoulder", "upper arm", "forearm", "hand"], self.angle_vars)):
            row = ttk.Frame(sliders)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=name, width=10).pack(side="left")
            label = ttk.Label(row, textvariable=var, width=5)
            label.pack(side="right")
            scale = ttk.Scale(row, from_=-170, to=170, variable=var, orient="horizontal", command=self.on_slider)
            scale.pack(side="left", fill="x", expand=True)

        ttk.Label(self.panel, text="Mouse").pack(anchor="w", pady=(8, 0))
        ttk.Label(
            self.panel,
            text="In IK mode click or drag inside the canvas. The hand tries to reach the target.",
            wraplength=PANEL - 24,
        ).pack(anchor="w")

        ttk.Separator(self.panel).pack(fill="x", pady=12)
        ttk.Label(self.panel, textvariable=self.info, wraplength=PANEL - 24).pack(anchor="w")

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.set_target)
        self.canvas.bind("<B1-Motion>", self.set_target)

    def reset_fk(self):
        self.mode.set("fk")
        for var, angle in zip(self.angle_vars, self.pose_a):
            var.set(angle)
        self.skeleton.set_angles(self.pose_a)

    def set_pose_b(self):
        self.mode.set("fk")
        for var, angle in zip(self.angle_vars, self.pose_b):
            var.set(angle)
        self.skeleton.set_angles(self.pose_b)

    def on_slider(self, _event=None):
        if self.mode.get() == "fk":
            self.skeleton.set_angles([var.get() for var in self.angle_vars])

    def set_target(self, event):
        self.target = (event.x, event.y)
        self.mode.set("ik")

    def update(self):
        if self.paused.get():
            return

        mode = self.mode.get()
        if mode == "animation":
            self.time += 0.018 * self.speed.get()
            k = (math.sin(self.time) + 1) * 0.5
            angles = [angle_lerp_deg(a, b, k) for a, b in zip(self.pose_a, self.pose_b)]
            self.skeleton.set_angles(angles)
            for var, angle in zip(self.angle_vars, angles):
                var.set(round(angle, 1))
        elif mode == "ik":
            self.skeleton.solve_ccd(self.target)
            for var, angle in zip(self.angle_vars, self.skeleton.angles()):
                var.set(round(angle, 1))
        else:
            self.skeleton.set_angles([var.get() for var in self.angle_vars])

        self.skeleton.forward()

    def draw_grid(self):
        for x in range(0, CANVAS_W, 50):
            self.canvas.create_line(x, 0, x, CANVAS_H, fill="#e3dfd3")
        for y in range(0, CANVAS_H, 50):
            self.canvas.create_line(0, y, CANVAS_W, y, fill="#e3dfd3")

    def draw_pose(self, angles, color, width=8):
        old = self.skeleton.angles()
        self.skeleton.set_angles(angles)
        self.skeleton.forward()
        points = self.skeleton.joints()
        for a, b in zip(points, points[1:]):
            self.canvas.create_line(a[0], a[1], b[0], b[1], fill=color, width=width, capstyle=tk.ROUND)
        for x, y in points:
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=color, outline="")
        self.skeleton.set_angles(old)
        self.skeleton.forward()

    def draw_skeleton(self):
        points = self.skeleton.joints()

        # Simple "skinning": a thick soft body is drawn around the bones.
        for a, b in zip(points, points[1:]):
            self.canvas.create_line(a[0], a[1], b[0], b[1], fill="#d8a57b", width=34, capstyle=tk.ROUND)
            self.canvas.create_line(a[0], a[1], b[0], b[1], fill="#553c30", width=6, capstyle=tk.ROUND)

        for i, (x, y) in enumerate(points):
            radius = 13 if i == 0 else 10
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#22313f", outline="#ffffff", width=2)
            self.canvas.create_text(x, y - 22, text=str(i), fill="#22313f", font=("Segoe UI", 9, "bold"))

        hand = points[-1]
        self.canvas.create_oval(hand[0] - 8, hand[1] - 8, hand[0] + 8, hand[1] + 8, fill="#e85d04", outline="")

    def draw_target(self):
        x, y = self.target
        self.canvas.create_line(x - 16, y, x + 16, y, fill="#c1121f", width=2)
        self.canvas.create_line(x, y - 16, x, y + 16, fill="#c1121f", width=2)
        self.canvas.create_oval(x - 8, y - 8, x + 8, y + 8, outline="#c1121f", width=2)
        self.canvas.create_text(x + 12, y - 14, text="target", fill="#c1121f", anchor="w")

    def draw_labels(self):
        self.canvas.create_text(16, 16, anchor="nw", text="Task A: FK hierarchy, Task B: pose interpolation, Task V: CCD IK", fill="#233", font=("Segoe UI", 12, "bold"))
        self.canvas.create_text(16, 42, anchor="nw", text="Parent rotation changes all child bones. IK target is controlled by mouse.", fill="#233")

        y = CANVAS_H - 100
        self.canvas.create_rectangle(12, y, 350, y + 78, fill="#fffaf0", outline="#c9bea8")
        text = (
            "Bone tree:\n"
            "0 shoulder -> 1 upper arm -> 2 forearm -> 3 hand\n"
            "Transforms are accumulated from parent to child."
        )
        self.canvas.create_text(24, y + 12, anchor="nw", text=text, fill="#44372c")

    def redraw(self):
        self.canvas.delete("all")
        self.draw_grid()
        if self.show_ghosts.get():
            self.draw_pose(self.pose_a, "#9cc9bd", 5)
            self.draw_pose(self.pose_b, "#cab8ff", 5)
        self.draw_target()
        self.draw_skeleton()
        self.draw_labels()

        end = self.skeleton.bones[-1].end
        error = dist(end, self.target)
        self.info.set(
            "Current mode: {}\nEnd effector error: {:.1f}px\nAngles: {}".format(
                self.mode.get(),
                error,
                ", ".join("{:.1f}".format(a) for a in self.skeleton.angles()),
            )
        )

    def tick(self):
        self.update()
        self.redraw()
        self.root.after(DT_MS, self.tick)


def main():
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    Lab20App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
