import math
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider


WINDOW_SIZE = 420
Z_NEAR = 0.1
Z_FAR = 1000.0
VIEW_X_LIMIT = 9.5
VIEW_Y_LIMIT = 5.5


@dataclass
class Mesh:
    vertices: np.ndarray
    edges: list[tuple[int, int]]
    faces: list[tuple[int, ...]]


def rotation_x(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array(
        [
            [1, 0, 0],
            [0, c, -s],
            [0, s, c],
        ],
        dtype=float,
    )


def rotation_y(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array(
        [
            [c, 0, s],
            [0, 1, 0],
            [-s, 0, c],
        ],
        dtype=float,
    )


def rotation_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array(
        [
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1],
        ],
        dtype=float,
    )


def transform(vertices, matrix):
    return vertices @ matrix.T


def orthographic_project(points):
    return points[:, :2], points[:, 2]


def perspective_project(points, focal_length, camera_distance):
    shifted = points.copy()
    shifted[:, 2] += camera_distance
    z = np.maximum(shifted[:, 2], Z_NEAR)
    x = focal_length * shifted[:, 0] / z
    y = focal_length * shifted[:, 1] / z
    return np.column_stack((x, y)), z


def cube_mesh(size=2.0):
    s = size / 2
    vertices = np.array(
        [
            [-s, -s, -s],
            [s, -s, -s],
            [s, s, -s],
            [-s, s, -s],
            [-s, -s, s],
            [s, -s, s],
            [s, s, s],
            [-s, s, s],
        ],
        dtype=float,
    )
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 3, 7, 4),
    ]
    return Mesh(vertices, edges, faces)


def octahedron_mesh(size=2.8):
    s = size / 2
    vertices = np.array(
        [
            [0, 0, s],
            [0, 0, -s],
            [-s, 0, 0],
            [s, 0, 0],
            [0, -s, 0],
            [0, s, 0],
        ],
        dtype=float,
    )
    edges = [
        (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 4), (4, 3), (3, 5), (5, 2),
    ]
    faces = [
        (0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
        (1, 2, 4), (1, 4, 3), (1, 3, 5), (1, 5, 2),
    ]
    return Mesh(vertices, edges, faces)


def pyramid_mesh(radius=1.6, height=2.8):
    base = []
    for i in range(4):
        angle = math.pi / 4 + i * math.pi / 2
        base.append([radius * math.cos(angle), radius * math.sin(angle), -height / 2])
    vertices = np.array(base + [[0, 0, height / 2]], dtype=float)
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4), (3, 4)]
    faces = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    return Mesh(vertices, edges, faces)


def cylinder_mesh(radius=1.1, height=2.8, segments=20):
    vertices = []
    for z in (-height / 2, height / 2):
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append([radius * math.cos(angle), radius * math.sin(angle), z])
    edges = []
    faces = []
    for i in range(segments):
        n = (i + 1) % segments
        edges.append((i, n))
        edges.append((i + segments, n + segments))
        edges.append((i, i + segments))
        faces.append((i, n, n + segments, i + segments))
    faces.append(tuple(range(segments)))
    faces.append(tuple(range(segments, 2 * segments)))
    return Mesh(np.array(vertices, dtype=float), edges, faces)


def cone_mesh(radius=1.2, height=3.0, segments=20):
    vertices = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append([radius * math.cos(angle), radius * math.sin(angle), -height / 2])
    vertices.append([0, 0, height / 2])
    apex = segments
    edges = []
    faces = [tuple(range(segments))]
    for i in range(segments):
        n = (i + 1) % segments
        edges.append((i, n))
        edges.append((i, apex))
        faces.append((i, n, apex))
    return Mesh(np.array(vertices, dtype=float), edges, faces)


def sphere_mesh(radius=1.55, lat_steps=10, lon_steps=18):
    vertices = []
    for i in range(lat_steps + 1):
        theta = math.pi * i / lat_steps
        for j in range(lon_steps):
            phi = 2 * math.pi * j / lon_steps
            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.sin(theta) * math.sin(phi)
            z = radius * math.cos(theta)
            vertices.append([x, y, z])

    def idx(i, j):
        return i * lon_steps + (j % lon_steps)

    edges = []
    faces = []
    for i in range(lat_steps):
        for j in range(lon_steps):
            a = idx(i, j)
            b = idx(i, j + 1)
            c = idx(i + 1, j + 1)
            d = idx(i + 1, j)
            edges.append((a, b))
            edges.append((a, d))
            if i != 0 and i != lat_steps - 1:
                faces.append((a, b, c, d))
            elif i == 0:
                faces.append((a, c, d))
            else:
                faces.append((a, b, d))
    return Mesh(np.array(vertices, dtype=float), list(dict.fromkeys(edges)), faces)


def torus_mesh(major_radius=2.2, minor_radius=0.7, major_steps=18, minor_steps=12):
    vertices = []
    for i in range(major_steps):
        u = 2 * math.pi * i / major_steps
        for j in range(minor_steps):
            v = 2 * math.pi * j / minor_steps
            x = (major_radius + minor_radius * math.cos(v)) * math.cos(u)
            y = (major_radius + minor_radius * math.cos(v)) * math.sin(u)
            z = minor_radius * math.sin(v)
            vertices.append([x, y, z])

    def idx(i, j):
        return (i % major_steps) * minor_steps + (j % minor_steps)

    edges = []
    faces = []
    for i in range(major_steps):
        for j in range(minor_steps):
            a = idx(i, j)
            b = idx(i + 1, j)
            c = idx(i + 1, j + 1)
            d = idx(i, j + 1)
            edges.append((a, b))
            edges.append((a, d))
            faces.append((a, b, c, d))
    return Mesh(np.array(vertices, dtype=float), list(dict.fromkeys(edges)), faces)


def triangulate_face(face):
    if len(face) == 3:
        return [face]
    triangles = []
    for i in range(1, len(face) - 1):
        triangles.append((face[0], face[i], face[i + 1]))
    return triangles


def face_visible(face_points):
    v1 = face_points[1] - face_points[0]
    v2 = face_points[2] - face_points[0]
    normal = np.cross(v1, v2)
    center = face_points.mean(axis=0)
    view_dir = center - np.array([0.0, 0.0, -8.0])
    return np.dot(normal, view_dir) < 0


def draw_wireframe(ax, mesh, projected_points, color, hidden=False, transformed_points=None):
    for edge in mesh.edges:
        p1 = projected_points[edge[0]]
        p2 = projected_points[edge[1]]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=1.2, alpha=0.9)

    if hidden and transformed_points is not None:
        for face in mesh.faces:
            face_points = transformed_points[list(face)]
            if face_visible(face_points):
                poly = projected_points[list(face)]
                ax.fill(poly[:, 0], poly[:, 1], color="white", alpha=0.08)


def clear_axis(ax, title):
    ax.clear()
    ax.set_title(title, fontsize=11)
    ax.set_xlim(-VIEW_X_LIMIT, VIEW_X_LIMIT)
    ax.set_ylim(-VIEW_Y_LIMIT, VIEW_Y_LIMIT)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)


def rasterize_triangles(points_3d, projected_2d, faces, width, height):
    z_buffer = np.full((height, width), np.inf, dtype=float)
    scale_x = width / (2 * VIEW_X_LIMIT)
    scale_y = height / (2 * VIEW_Y_LIMIT)

    def to_screen(p):
        sx = int((p[0] + VIEW_X_LIMIT) * scale_x)
        sy = int((VIEW_Y_LIMIT - p[1]) * scale_y)
        return sx, sy

    for face in faces:
        for tri in triangulate_face(face):
            ids = list(tri)
            p2 = projected_2d[ids]
            p3 = points_3d[ids]
            s = [to_screen(p) for p in p2]
            xs = [pt[0] for pt in s]
            ys = [pt[1] for pt in s]
            min_x = max(min(xs), 0)
            max_x = min(max(xs), width - 1)
            min_y = max(min(ys), 0)
            max_y = min(max(ys), height - 1)
            denom = (
                (ys[1] - ys[2]) * (xs[0] - xs[2]) +
                (xs[2] - xs[1]) * (ys[0] - ys[2])
            )
            if abs(denom) < 1e-9:
                continue

            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    w1 = ((ys[1] - ys[2]) * (x - xs[2]) + (xs[2] - xs[1]) * (y - ys[2])) / denom
                    w2 = ((ys[2] - ys[0]) * (x - xs[2]) + (xs[0] - xs[2]) * (y - ys[2])) / denom
                    w3 = 1.0 - w1 - w2
                    if w1 >= 0 and w2 >= 0 and w3 >= 0:
                        z = w1 * p3[0, 2] + w2 * p3[1, 2] + w3 * p3[2, 2]
                        if z < z_buffer[y, x]:
                            z_buffer[y, x] = z

    return z_buffer


def draw_visible_edges(ax, mesh, points_3d, projected_2d, z_buffer, color):
    scale_x = z_buffer.shape[1] / (2 * VIEW_X_LIMIT)
    scale_y = z_buffer.shape[0] / (2 * VIEW_Y_LIMIT)

    def to_screen(p):
        sx = int((p[0] + VIEW_X_LIMIT) * scale_x)
        sy = int((VIEW_Y_LIMIT - p[1]) * scale_y)
        return sx, sy

    for a, b in mesh.edges:
        p1_2d = projected_2d[a]
        p2_2d = projected_2d[b]
        p1_3d = points_3d[a]
        p2_3d = points_3d[b]
        visible_x = []
        visible_y = []
        for t in np.linspace(0.0, 1.0, 60):
            p2 = p1_2d * (1 - t) + p2_2d * t
            p3 = p1_3d * (1 - t) + p2_3d * t
            sx, sy = to_screen(p2)
            if 0 <= sx < z_buffer.shape[1] and 0 <= sy < z_buffer.shape[0]:
                depth = p3[2]
                if depth <= z_buffer[sy, sx] + 0.06:
                    visible_x.append(p2[0])
                    visible_y.append(p2[1])
                else:
                    if len(visible_x) > 1:
                        ax.plot(visible_x, visible_y, color=color, linewidth=1.0)
                    visible_x = []
                    visible_y = []
        if len(visible_x) > 1:
            ax.plot(visible_x, visible_y, color=color, linewidth=1.0)


def main():
    cube = cube_mesh()
    octahedron = octahedron_mesh()
    cylinder = cylinder_mesh()
    cone = cone_mesh()
    pyramid = pyramid_mesh()
    sphere = sphere_mesh()
    torus = torus_mesh()

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    plt.subplots_adjust(bottom=0.18, wspace=0.3)

    slider_ax = fig.add_axes([0.25, 0.06, 0.5, 0.03])
    focus_slider = Slider(slider_ax, "Фокус", 3.0, 12.0, valinit=7.0, valstep=0.5)

    def update(frame):
        angle = frame * 0.08

        clear_axis(axes[0], "Задача A: куб и октаэдр, ортографическая проекция")
        cube_points = transform(cube.vertices, rotation_y(angle))
        octa_points = transform(octahedron.vertices, rotation_y(-angle * 1.1))
        cube_proj, _ = orthographic_project(cube_points)
        octa_proj, _ = orthographic_project(octa_points)
        draw_wireframe(axes[0], cube, cube_proj * 1.6 - np.array([3.4, 0]), "tab:blue")
        draw_wireframe(axes[0], octahedron, octa_proj * 1.5 + np.array([3.4, 0]), "tab:red")

        clear_axis(axes[1], "Задача B: цилиндр, конус и пирамида, перспектива")
        rot_b = rotation_x(angle * 1.1) @ rotation_y(angle * 1.6)
        focal = 6.0
        camera = 8.0
        for mesh, shift, color in [
            (cylinder, np.array([-4.4, 0.0]), "tab:green"),
            (cone, np.array([0.0, 0.0]), "tab:orange"),
            (pyramid, np.array([4.4, 0.0]), "tab:purple"),
        ]:
            pts = transform(mesh.vertices, rot_b)
            proj, _ = perspective_project(pts, focal, camera)
            draw_wireframe(axes[1], mesh, proj + shift, color)

        clear_axis(axes[2], "Задача C: тор и сфера, перспектива + z-buffer")
        focal_c = focus_slider.val
        camera_c = 9.0

        torus_rot = rotation_x(angle * 1.0) @ rotation_y(angle * 1.3)
        torus_pts = transform(torus.vertices, torus_rot)
        torus_proj, _ = perspective_project(torus_pts, focal_c, camera_c)
        torus_proj_shifted = torus_proj - np.array([4.0, 0.0])
        torus_z = rasterize_triangles(
            torus_pts,
            torus_proj_shifted,
            torus.faces,
            WINDOW_SIZE,
            WINDOW_SIZE,
        )
        draw_visible_edges(axes[2], torus, torus_pts, torus_proj_shifted, torus_z, "tab:brown")

        sphere_rot = rotation_y(angle * 1.4) @ rotation_z(angle * 0.9)
        sphere_pts = transform(sphere.vertices, sphere_rot)
        sphere_proj, _ = perspective_project(sphere_pts, focal_c, camera_c)
        sphere_proj_shifted = sphere_proj + np.array([4.0, 0.0])
        sphere_z = rasterize_triangles(
            sphere_pts,
            sphere_proj_shifted,
            sphere.faces,
            WINDOW_SIZE,
            WINDOW_SIZE,
        )
        draw_visible_edges(axes[2], sphere, sphere_pts, sphere_proj_shifted, sphere_z, "tab:blue")

        axes[0].text(-4.2, -4.1, "вращение вокруг Y", fontsize=9)
        axes[1].text(-4.2, -4.1, "вращение вокруг X и Y", fontsize=9)
        axes[2].text(-4.2, -4.1, "фокус меняется ползунком", fontsize=9)

    fig.suptitle("Лабораторная работа 6. Проволочная 3D-модель", fontsize=14)
    animation = FuncAnimation(fig, update, interval=40, cache_frame_data=False)
    fig._animation = animation
    plt.show()


if __name__ == "__main__":
    main()
