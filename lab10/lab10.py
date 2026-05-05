from pathlib import Path

import matplotlib.tri as mtri
import numpy as np
from PIL import Image, ImageDraw


SIZE = (220, 220)
FRAMES_A = 10
FRAMES_B = 14
FRAMES_V = 14
OUTPUT_DIR = Path(__file__).resolve().parent


def to_array(image):
    return np.asarray(image, dtype=np.float32) / 255.0


def to_image(array):
    clipped = np.clip(array * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(clipped)


def bilinear_sample(image, coords):
    h, w = image.shape[:2]
    x = np.clip(coords[:, 0], 0, w - 1)
    y = np.clip(coords[:, 1], 0, h - 1)

    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)

    dx = (x - x0)[:, None]
    dy = (y - y0)[:, None]

    top = image[y0, x0] * (1.0 - dx) + image[y0, x1] * dx
    bottom = image[y1, x0] * (1.0 - dx) + image[y1, x1] * dx
    return top * (1.0 - dy) + bottom * dy


def triangle_barycentric(points, triangle):
    a, b, c = triangle
    denom = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denom) < 1e-8:
        return None

    w0 = ((b[1] - c[1]) * (points[:, 0] - c[0]) + (c[0] - b[0]) * (points[:, 1] - c[1])) / denom
    w1 = ((c[1] - a[1]) * (points[:, 0] - c[0]) + (a[0] - c[0]) * (points[:, 1] - c[1])) / denom
    w2 = 1.0 - w0 - w1
    return np.column_stack((w0, w1, w2))


def add_frame_corners(points, width, height):
    corners = np.array(
        [
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1],
        ],
        dtype=np.float32,
    )
    return np.vstack((points.astype(np.float32), corners))


def build_triangles(points):
    triangulation = mtri.Triangulation(points[:, 0], points[:, 1])
    return triangulation.triangles


def warp_image(image, src_points, dst_points, triangles, size):
    width, height = size
    result = np.zeros((height, width, 3), dtype=np.float32)

    for tri in triangles:
        src_tri = src_points[tri]
        dst_tri = dst_points[tri]
        min_x = max(int(np.floor(dst_tri[:, 0].min())), 0)
        max_x = min(int(np.ceil(dst_tri[:, 0].max())), width - 1)
        min_y = max(int(np.floor(dst_tri[:, 1].min())), 0)
        max_y = min(int(np.ceil(dst_tri[:, 1].max())), height - 1)
        if min_x > max_x or min_y > max_y:
            continue

        grid_x, grid_y = np.meshgrid(np.arange(min_x, max_x + 1), np.arange(min_y, max_y + 1))
        pixels = np.column_stack((grid_x.ravel(), grid_y.ravel())).astype(np.float32)
        bary = triangle_barycentric(pixels, dst_tri)
        if bary is None:
            continue

        mask = np.all(bary >= -1e-5, axis=1)
        if not np.any(mask):
            continue

        src_coords = bary[mask] @ src_tri
        sampled = bilinear_sample(image, src_coords)
        inside = pixels[mask].astype(int)
        result[inside[:, 1], inside[:, 0]] = sampled

    return result


def morph_frame(image_a, image_b, points_a, points_b, triangles, alpha, size):
    inter_points = (1.0 - alpha) * points_a + alpha * points_b
    warped_a = warp_image(image_a, points_a, inter_points, triangles, size)
    warped_b = warp_image(image_b, points_b, inter_points, triangles, size)
    return (1.0 - alpha) * warped_a + alpha * warped_b


def save_gif(frames, path, duration=90):
    images = [to_image(frame) for frame in frames]
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
    )


def make_loop_frames(frames):
    if len(frames) < 2:
        return frames
    return frames + frames[-2:0:-1]


def make_shape_image(shape, size=SIZE):
    image = Image.new("RGB", size, (248, 248, 248))
    draw = ImageDraw.Draw(image)
    if shape == "circle":
        draw.ellipse((45, 45, 175, 175), fill=(50, 120, 240))
    elif shape == "square":
        draw.rectangle((45, 45, 175, 175), fill=(240, 100, 70))
    elif shape == "triangle":
        draw.polygon([(110, 35), (30, 180), (190, 180)], fill=(75, 170, 110))
    elif shape == "star":
        draw.polygon(
            [(110, 25), (132, 78), (190, 84), (145, 123), (158, 185), (110, 152), (62, 185), (75, 123), (30, 84), (88, 78)],
            fill=(225, 180, 50),
        )
    return image


def task_a_points():
    center = np.array([110.0, 110.0], dtype=np.float32)
    radius = 65.0
    angles = np.deg2rad(np.arange(0, 360, 45))
    circle = np.column_stack((center[0] + radius * np.cos(angles), center[1] + radius * np.sin(angles)))
    square = np.array(
        [
            [175, 110],
            [175, 175],
            [110, 175],
            [45, 175],
            [45, 110],
            [45, 45],
            [110, 45],
            [175, 45],
        ],
        dtype=np.float32,
    )
    extra = np.array([[110, 110]], dtype=np.float32)
    return np.vstack((circle, extra)), np.vstack((square, extra))


def make_face_image(variant, size=SIZE):
    image = Image.new("RGB", size, (250, 247, 238))
    draw = ImageDraw.Draw(image)

    if variant == 1:
        face_box = (45, 28, 176, 195)
        hair = [(42, 88), (58, 26), (110, 8), (168, 24), (178, 88), (160, 50), (62, 44)]
        left_eye = (73, 80, 98, 98)
        right_eye = (122, 78, 150, 97)
        mouth = [(82, 147), (101, 160), (123, 162), (144, 150)]
        nose = [(110, 100), (104, 130), (118, 130)]
        brow_shift = -3
    else:
        face_box = (38, 34, 184, 196)
        hair = [(34, 96), (48, 36), (92, 14), (152, 18), (186, 74), (175, 106), (143, 58), (70, 54)]
        left_eye = (67, 88, 95, 108)
        right_eye = (126, 90, 156, 111)
        mouth = [(74, 144), (98, 171), (126, 169), (154, 141)]
        nose = [(111, 103), (98, 133), (119, 136)]
        brow_shift = 4

    draw.polygon(hair, fill=(90, 55, 38))
    draw.ellipse(face_box, fill=(245, 210, 180), outline=(160, 110, 85), width=2)
    draw.ellipse(left_eye, fill="white")
    draw.ellipse(right_eye, fill="white")
    draw.ellipse((left_eye[0] + 9, left_eye[1] + 6, left_eye[0] + 16, left_eye[1] + 14), fill=(40, 60, 80))
    draw.ellipse((right_eye[0] + 9, right_eye[1] + 6, right_eye[0] + 16, right_eye[1] + 14), fill=(40, 60, 80))
    draw.line((left_eye[0], left_eye[1] + brow_shift, left_eye[2], left_eye[1] - 4 + brow_shift), fill=(70, 35, 25), width=3)
    draw.line((right_eye[0], right_eye[1] - 4 + brow_shift, right_eye[2], right_eye[1] + brow_shift), fill=(70, 35, 25), width=3)
    draw.line(nose, fill=(160, 105, 85), width=3)
    draw.line(mouth, fill=(180, 65, 85), width=4)
    return image


def task_b_points():
    points_1 = np.array(
        [
            [110, 22],
            [56, 62],
            [164, 62],
            [70, 90],
            [136, 88],
            [110, 106],
            [103, 130],
            [80, 149],
            [142, 151],
            [110, 188],
        ],
        dtype=np.float32,
    )
    points_2 = np.array(
        [
            [110, 28],
            [48, 70],
            [174, 68],
            [67, 98],
            [142, 100],
            [110, 108],
            [99, 135],
            [76, 148],
            [152, 145],
            [112, 190],
        ],
        dtype=np.float32,
    )
    return points_1, points_2


def mask_from_image(image):
    arr = np.asarray(image, dtype=np.uint8)
    return np.any(arr < 240, axis=2)


def extract_ordered_contour(mask):
    padded = np.pad(mask, 1, constant_values=False)
    neighbors = (
        padded[1:-1, :-2] &
        padded[1:-1, 2:] &
        padded[:-2, 1:-1] &
        padded[2:, 1:-1]
    )
    boundary = mask & ~neighbors
    ys, xs = np.where(boundary)
    points = np.column_stack((xs, ys)).astype(np.float32)
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    order = np.argsort(angles)
    return points[order]


def sample_contour_points(contour, count):
    loop = np.vstack((contour, contour[0]))
    seg = np.linalg.norm(np.diff(loop, axis=0), axis=1)
    dist = np.concatenate(([0.0], np.cumsum(seg)))
    targets = np.linspace(0.0, dist[-1], count, endpoint=False)
    sampled = []

    for target in targets:
        idx = np.searchsorted(dist, target, side="right") - 1
        idx = min(idx, len(seg) - 1)
        length = seg[idx]
        t = 0.0 if length < 1e-8 else (target - dist[idx]) / length
        sampled.append(loop[idx] * (1.0 - t) + loop[idx + 1] * t)

    return np.array(sampled, dtype=np.float32)


def build_contact_sheet(frames, columns=5):
    pil_frames = [to_image(frame) for frame in frames]
    width, height = pil_frames[0].size
    rows = (len(pil_frames) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * width, rows * height), (255, 255, 255))

    for idx, frame in enumerate(pil_frames):
        x = (idx % columns) * width
        y = (idx // columns) * height
        canvas.paste(frame, (x, y))

    return canvas


def run_task_a():
    image_a = to_array(make_shape_image("circle"))
    image_b = to_array(make_shape_image("square"))
    pts_a, pts_b = task_a_points()
    pts_a = add_frame_corners(pts_a, *SIZE)
    pts_b = add_frame_corners(pts_b, *SIZE)
    triangles = build_triangles(pts_a)

    frames = [morph_frame(image_a, image_b, pts_a, pts_b, triangles, alpha, SIZE) for alpha in np.linspace(0.0, 1.0, FRAMES_A)]
    build_contact_sheet(frames).save(OUTPUT_DIR / "task_a_grid.png")
    save_gif(make_loop_frames(frames), OUTPUT_DIR / "task_a_shapes.gif")
    return frames


def run_task_b():
    image_a = to_array(make_face_image(1))
    image_b = to_array(make_face_image(2))
    pts_a, pts_b = task_b_points()
    pts_a = add_frame_corners(pts_a, *SIZE)
    pts_b = add_frame_corners(pts_b, *SIZE)
    triangles = build_triangles(pts_a)

    frames = [morph_frame(image_a, image_b, pts_a, pts_b, triangles, alpha, SIZE) for alpha in np.linspace(0.0, 1.0, FRAMES_B)]
    save_gif(make_loop_frames(frames), OUTPUT_DIR / "task_b_faces.gif")
    return frames


def run_task_v():
    image_a_pil = make_shape_image("triangle")
    image_b_pil = make_shape_image("star")
    image_a = to_array(image_a_pil)
    image_b = to_array(image_b_pil)

    contour_a = extract_ordered_contour(mask_from_image(image_a_pil))
    contour_b = extract_ordered_contour(mask_from_image(image_b_pil))
    pts_a = sample_contour_points(contour_a, 24)
    pts_b = sample_contour_points(contour_b, 24)
    pts_a = add_frame_corners(np.vstack((pts_a, [[110, 110]])), *SIZE)
    pts_b = add_frame_corners(np.vstack((pts_b, [[110, 110]])), *SIZE)
    triangles = build_triangles(pts_a)

    frames = [morph_frame(image_a, image_b, pts_a, pts_b, triangles, alpha, SIZE) for alpha in np.linspace(0.0, 1.0, FRAMES_V)]
    save_gif(make_loop_frames(frames), OUTPUT_DIR / "task_v_auto_contour.gif")
    return frames


def main():
    run_task_a()
    run_task_b()
    run_task_v()
    print("Lab 10 complete.")
    print("Saved files:")
    print(" - task_a_grid.png")
    print(" - task_a_shapes.gif")
    print(" - task_b_faces.gif")
    print(" - task_v_auto_contour.gif")


if __name__ == "__main__":
    main()
