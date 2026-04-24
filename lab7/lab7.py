import math
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

WIDTH = 720
HEIGHT = 450
FOV_DEG = 60.0
Z_NEAR = 0.1
Z_FAR = 100.0
FOV_FACTOR = 1.0 / math.tan(math.radians(FOV_DEG) / 2.0)


@dataclass
class Mesh:
    vertices: np.ndarray
    triangles: np.ndarray
    normals: np.ndarray


@dataclass
class Object3D:
    mesh: Mesh
    color: np.ndarray
    position: np.ndarray
    rotation_speed: np.ndarray
    scale: float = 1.0


def normalize(v):
    n = np.linalg.norm(v)
    if n < 1e-9:
        return v
    return v / n


def rotation_matrix_xyz(ax, ay, az):
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)

    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=float)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=float)
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=float)
    return rz @ ry @ rx


def make_sphere(lat_steps=10, lon_steps=16, radius=1.0):
    verts = []
    for i in range(lat_steps + 1):
        theta = math.pi * i / lat_steps
        for j in range(lon_steps):
            phi = 2 * math.pi * j / lon_steps
            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.cos(theta)
            z = radius * math.sin(theta) * math.sin(phi)
            verts.append([x, y, z])

    def idx(i, j):
        return i * lon_steps + (j % lon_steps)

    tris = []
    for i in range(lat_steps):
        for j in range(lon_steps):
            a = idx(i, j)
            b = idx(i, j + 1)
            c = idx(i + 1, j + 1)
            d = idx(i + 1, j)
            if i != 0:
                tris.append([a, b, d])
            if i != lat_steps - 1:
                tris.append([b, c, d])

    vertices = np.array(verts, dtype=float)
    normals = np.array([normalize(v) for v in vertices], dtype=float)
    return Mesh(vertices, np.array(tris, dtype=int), normals)


def make_torus(r_major=1.2, r_minor=0.45, major_steps=16, minor_steps=10):
    verts = []
    normals = []
    for i in range(major_steps):
        u = 2 * math.pi * i / major_steps
        cu, su = math.cos(u), math.sin(u)
        for j in range(minor_steps):
            v = 2 * math.pi * j / minor_steps
            cv, sv = math.cos(v), math.sin(v)
            x = (r_major + r_minor * cv) * cu
            y = r_minor * sv
            z = (r_major + r_minor * cv) * su
            verts.append([x, y, z])
            normals.append([cv * cu, sv, cv * su])

    def idx(i, j):
        return (i % major_steps) * minor_steps + (j % minor_steps)

    tris = []
    for i in range(major_steps):
        for j in range(minor_steps):
            a = idx(i, j)
            b = idx(i + 1, j)
            c = idx(i + 1, j + 1)
            d = idx(i, j + 1)
            tris.append([a, b, d])
            tris.append([b, c, d])

    return Mesh(np.array(verts, dtype=float), np.array(tris, dtype=int), np.array(normals, dtype=float))


def make_cube(size=1.4):
    s = size / 2
    vertices = np.array(
        [
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
        ],
        dtype=float,
    )
    triangles = np.array(
        [
            [0, 1, 2], [0, 2, 3],
            [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1],
            [2, 6, 7], [2, 7, 3],
            [1, 5, 6], [1, 6, 2],
            [0, 3, 7], [0, 7, 4],
        ],
        dtype=int,
    )

    normals = np.zeros_like(vertices)
    for tri in triangles:
        p0, p1, p2 = vertices[tri]
        n = normalize(np.cross(p1 - p0, p2 - p0))
        normals[tri[0]] += n
        normals[tri[1]] += n
        normals[tri[2]] += n
    normals = np.array([normalize(n) for n in normals], dtype=float)

    return Mesh(vertices, triangles, normals)


def look_at(eye, target, up):
    z = normalize(eye - target)
    x = normalize(np.cross(up, z))
    y = np.cross(z, x)
    view = np.eye(4, dtype=float)
    view[0, :3] = x
    view[1, :3] = y
    view[2, :3] = z
    view[:3, 3] = -view[:3, :3] @ eye
    return view


def project_points(points_cam):
    x = points_cam[:, 0]
    y = points_cam[:, 1]
    z = points_cam[:, 2]
    z_safe = np.where(np.abs(z) < 1e-6, 1e-6, z)
    ndc_x = -(x * FOV_FACTOR) / z_safe
    ndc_y = -(y * FOV_FACTOR) / z_safe
    sx = (ndc_x + 1.0) * 0.5 * (WIDTH - 1)
    sy = (1.0 - (ndc_y + 1.0) * 0.5) * (HEIGHT - 1)
    return np.column_stack((sx, sy, -z))


def normalize_rows(v):
    norms = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.clip(norms, 1e-9, None)


def phong_lighting_batch(pos, normal, view_pos, lights, base_color, ambient_color, ka, kd, ks, shininess):
    n = normalize_rows(normal)
    v = normalize_rows(view_pos - pos)
    color = np.broadcast_to(ka * ambient_color * base_color, pos.shape).copy()

    for light_pos, light_color in lights:
        l = normalize_rows(light_pos - pos)
        ndotl = np.maximum(np.sum(n * l, axis=1), 0.0)
        diffuse = kd * ndotl[:, None] * light_color * base_color

        r = normalize_rows(2 * np.sum(n * l, axis=1)[:, None] * n - l)
        spec = ks * (np.maximum(np.sum(r * v, axis=1), 0.0) ** shininess)
        specular = spec[:, None] * light_color

        color += diffuse + specular

    return np.clip(color, 0.0, 1.0)


def rasterize_triangle(frame, zbuf, pts2, pts3, norms, cols, mode, light_params):
    x0, y0, z0 = pts2[0]
    x1, y1, z1 = pts2[1]
    x2, y2, z2 = pts2[2]

    min_x = max(int(min(x0, x1, x2)), 0)
    max_x = min(int(max(x0, x1, x2)) + 1, WIDTH - 1)
    min_y = max(int(min(y0, y1, y2)), 0)
    max_y = min(int(max(y0, y1, y2)) + 1, HEIGHT - 1)

    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denom) < 1e-8:
        return

    xs = np.arange(min_x, max_x + 1, dtype=float)
    ys = np.arange(min_y, max_y + 1, dtype=float)[:, None]
    w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / denom
    w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / denom
    w2 = 1.0 - w0 - w1
    inside = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
    if not np.any(inside):
        return

    depth = w0 * z0 + w1 * z1 + w2 * z2
    z_slice = zbuf[min_y:max_y + 1, min_x:max_x + 1]
    closer = inside & (depth < z_slice)
    if not np.any(closer):
        return

    z_slice[closer] = depth[closer]
    frame_slice = frame[min_y:max_y + 1, min_x:max_x + 1]

    view_pos, lights, base_color, ambient_color, ka, kd, ks, shininess = light_params

    if mode == "gouraud":
        colors = w0[..., None] * cols[0] + w1[..., None] * cols[1] + w2[..., None] * cols[2]
        frame_slice[closer] = np.clip(colors[closer], 0.0, 1.0)
        return

    pos = w0[..., None] * pts3[0] + w1[..., None] * pts3[1] + w2[..., None] * pts3[2]
    normal = w0[..., None] * norms[0] + w1[..., None] * norms[1] + w2[..., None] * norms[2]
    shaded = phong_lighting_batch(
        pos[closer],
        normal[closer],
        view_pos,
        lights,
        base_color,
        ambient_color,
        ka,
        kd,
        ks,
        shininess,
    )
    frame_slice[closer] = shaded


def rasterize_shadow_triangle(frame, zbuf, tri2, shadow_strength):
    x0, y0, z0 = tri2[0]
    x1, y1, z1 = tri2[1]
    x2, y2, z2 = tri2[2]

    min_x = max(int(min(x0, x1, x2)), 0)
    max_x = min(int(max(x0, x1, x2)) + 1, WIDTH - 1)
    min_y = max(int(min(y0, y1, y2)), 0)
    max_y = min(int(max(y0, y1, y2)) + 1, HEIGHT - 1)
    if min_x > max_x or min_y > max_y:
        return

    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denom) < 1e-8:
        return

    xs = np.arange(min_x, max_x + 1, dtype=float)
    ys = np.arange(min_y, max_y + 1, dtype=float)[:, None]
    w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / denom
    w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / denom
    w2 = 1.0 - w0 - w1
    inside = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
    if not np.any(inside):
        return

    depth = w0 * z0 + w1 * z1 + w2 * z2
    z_slice = zbuf[min_y:max_y + 1, min_x:max_x + 1]
    closer = inside & (depth < z_slice)
    if not np.any(closer):
        return

    z_slice[closer] = depth[closer]
    frame_slice = frame[min_y:max_y + 1, min_x:max_x + 1]
    frame_slice[closer] *= shadow_strength


def shadow_matrix(plane, light):
    dot = float(np.dot(plane, light))
    return dot * np.eye(4) - np.outer(light, plane)


SPHERE = Object3D(
    mesh=make_sphere(lat_steps=9, lon_steps=14, radius=1.1),
    color=np.array([0.22, 0.52, 0.95]),
    position=np.array([0.0, 0.1, 0.0]),
    rotation_speed=np.array([0.3, 0.9, 0.1]),
)
TORUS = Object3D(
    mesh=make_torus(r_major=1.1, r_minor=0.35, major_steps=14, minor_steps=9),
    color=np.array([0.92, 0.48, 0.18]),
    position=np.array([2.3, 0.05, -0.6]),
    rotation_speed=np.array([0.6, 0.3, 0.2]),
)
CUBE = Object3D(
    mesh=make_cube(size=1.4),
    color=np.array([0.2, 0.78, 0.33]),
    position=np.array([-2.3, -0.05, -0.2]),
    rotation_speed=np.array([0.4, 0.7, 0.0]),
)

EYE = np.array([0.0, 1.2, 6.3], dtype=float)
TARGET = np.array([0.0, 0.0, 0.0], dtype=float)
UP = np.array([0.0, 1.0, 0.0], dtype=float)
VIEW_MATRIX = look_at(EYE, TARGET, UP)

STAGE_CONFIGS = {
    "A": {
        "objects": [SPHERE],
        "lights": [(np.array([2.5, 2.8, 3.0]), np.array([1.0, 1.0, 1.0]))],
        "ambient": np.array([0.0, 0.0, 0.0]),
        "mode": "gouraud",
    },
    "B": {
        "objects": [SPHERE, TORUS],
        "lights": [(np.array([2.8, 2.6, 2.2]), np.array([1.0, 1.0, 1.0]))],
        "ambient": np.array([0.23, 0.23, 0.23]),
        "mode": None,
    },
    "V": {
        "objects": [SPHERE, TORUS, CUBE],
        "lights": [
            (np.array([3.6, 3.2, 1.8]), np.array([1.0, 0.3, 0.3])),
            (np.array([-3.0, 2.6, 2.8]), np.array([0.35, 0.55, 1.0])),
        ],
        "ambient": np.array([0.18, 0.18, 0.18]),
        "mode": "phong",
    },
}


def render_scene(stage, shading_mode, t):
    frame = np.full((HEIGHT, WIDTH, 3), 0.93, dtype=float)
    zbuf = np.full((HEIGHT, WIDTH), np.inf, dtype=float)

    config = STAGE_CONFIGS["V" if stage not in STAGE_CONFIGS else stage]
    objects = config["objects"]
    lights = config["lights"]
    ambient = config["ambient"]
    mode = shading_mode if config["mode"] is None else config["mode"]

    if stage == "V":
        plane = np.array([0.0, 1.0, 0.0, 1.45])
        light_h = np.array([lights[0][0][0], lights[0][0][1], lights[0][0][2], 1.0])
        sm = shadow_matrix(plane, light_h)

        for obj in objects:
            rot = rotation_matrix_xyz(*(obj.rotation_speed * t))
            world = (obj.mesh.vertices * obj.scale) @ rot.T + obj.position
            w_h = np.column_stack((world, np.ones(len(world))))
            sh = (sm @ w_h.T).T
            sh = sh[:, :3] / np.clip(sh[:, 3:4], 1e-8, None)

            sh_cam = (VIEW_MATRIX @ np.column_stack((sh, np.ones(len(sh)))).T).T[:, :3]
            proj = project_points(sh_cam)
            for tri in obj.mesh.triangles:
                rasterize_shadow_triangle(frame, zbuf, proj[tri], shadow_strength=0.42)

    for obj in objects:
        rot = rotation_matrix_xyz(*(obj.rotation_speed * t))
        world_pos = (obj.mesh.vertices * obj.scale) @ rot.T + obj.position
        world_normals = obj.mesh.normals @ rot.T

        cam_pos = (VIEW_MATRIX @ np.column_stack((world_pos, np.ones(len(world_pos)))).T).T[:, :3]
        screen = project_points(cam_pos)

        if np.all(cam_pos[:, 2] > -Z_NEAR):
            continue

        ka, kd, ks, shininess = 0.35, 0.9, 0.7, 28
        light_params = (EYE, lights, obj.color, ambient, ka, kd, ks, shininess)

        if mode == "gouraud":
            vcolors = phong_lighting_batch(world_pos, world_normals, EYE, lights, obj.color, ambient, ka, kd, ks, shininess)
        else:
            vcolors = None

        for tri in obj.mesh.triangles:
            w0, w1, w2 = world_pos[tri]
            face_n = np.cross(w1 - w0, w2 - w0)
            if np.dot(face_n, EYE - (w0 + w1 + w2) / 3.0) <= 0:
                continue

            tri2 = screen[tri]
            tri3 = world_pos[tri]
            trin = world_normals[tri]
            tric = vcolors[tri] if vcolors is not None else np.zeros((3, 3))

            rasterize_triangle(frame, zbuf, tri2, tri3, trin, tric, mode, light_params)

    return frame


def main():
    state = {
        "stage": "A",
        "mode": "gouraud",
        "paused": False,
        "t": 0.0,
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_axis_off()

    image = ax.imshow(np.zeros((HEIGHT, WIDTH, 3), dtype=float), interpolation="nearest")

    info_text = ax.text(
        0.01,
        0.98,
        "",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        bbox={"facecolor": "white", "alpha": 0.8, "pad": 4},
    )

    def info_line():
        if state["stage"] == "A":
            return "Task A: one low-poly sphere, one point light, Gouraud only"
        if state["stage"] == "B":
            return f"Task B: sphere+torus, ambient, real-time mode switch (M): {state['mode']}"
        return "Task V: multi-object scene, 2 colored lights, Phong specular + shadow matrix"

    def on_key(event):
        if event.key == "1":
            state["stage"] = "A"
        elif event.key == "2":
            state["stage"] = "B"
        elif event.key == "3":
            state["stage"] = "V"
        elif event.key and event.key.lower() == "m" and state["stage"] == "B":
            state["mode"] = "phong" if state["mode"] == "gouraud" else "gouraud"
        elif event.key == " ":
            state["paused"] = not state["paused"]

    fig.canvas.mpl_connect("key_press_event", on_key)

    def update(_):
        if not state["paused"]:
            state["t"] += 0.045
        frame = render_scene(state["stage"], state["mode"], state["t"])
        image.set_data(frame)
        info_text.set_text(
            "Lab 7 - Shading\n"
            f"{info_line()}\n"
            "Controls: 1=A, 2=B, 3=V, M=switch in B, Space=pause"
        )
        return [image, info_text]

    anim = FuncAnimation(fig, update, interval=34, blit=True, cache_frame_data=False)
    fig._anim = anim
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
