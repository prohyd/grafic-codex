import math
import random
import struct
from dataclasses import dataclass


EPS = 1e-4
MAX_COLOR = 255


@dataclass
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x * value.x, self.y * value.y, self.z * value.z)
        return Vec3(self.x * value, self.y * value, self.z * value)

    __rmul__ = __mul__

    def __truediv__(self, value):
        return Vec3(self.x / value, self.y / value, self.z / value)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self):
        return math.sqrt(self.dot(self))

    def normalized(self):
        length = self.length()
        if length == 0:
            return self
        return self / length

    def clamp(self, low=0.0, high=1.0):
        return Vec3(
            min(max(self.x, low), high),
            min(max(self.y, low), high),
            min(max(self.z, low), high),
        )


@dataclass
class Ray:
    origin: Vec3
    direction: Vec3


@dataclass
class Material:
    color: Vec3
    reflection: float = 0.0
    transparency: float = 0.0
    refractive_index: float = 1.0
    specular: float = 0.2


@dataclass
class Hit:
    distance: float
    point: Vec3
    normal: Vec3
    material: Material


class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

    def intersect(self, ray):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4.0 * a * c

        if discriminant < 0:
            return None

        sqrt_d = math.sqrt(discriminant)
        t1 = (-b - sqrt_d) / (2.0 * a)
        t2 = (-b + sqrt_d) / (2.0 * a)
        distance = None
        if t1 > EPS:
            distance = t1
        elif t2 > EPS:
            distance = t2

        if distance is None:
            return None

        point = ray.origin + ray.direction * distance
        normal = (point - self.center).normalized()
        return Hit(distance, point, normal, self.material)


class Plane:
    def __init__(self, point, normal, material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material

    def intersect(self, ray):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < EPS:
            return None

        distance = (self.point - ray.origin).dot(self.normal) / denom
        if distance <= EPS:
            return None

        point = ray.origin + ray.direction * distance
        return Hit(distance, point, self.normal, self.material)


class Scene:
    def __init__(self, objects, background, light_dir, light_color, ambient=0.12, soft_samples=1):
        self.objects = objects
        self.background = background
        self.light_dir = light_dir.normalized()
        self.light_color = light_color
        self.ambient = ambient
        self.soft_samples = soft_samples


def reflect(direction, normal):
    return direction - normal * 2.0 * direction.dot(normal)


def refract(direction, normal, n1, n2):
    cos_i = max(-1.0, min(1.0, direction.dot(normal)))
    eta = n1 / n2
    n = normal

    if cos_i < 0:
        cos_i = -cos_i
    else:
        n = -normal
        eta = n2 / n1

    k = 1.0 - eta * eta * (1.0 - cos_i * cos_i)
    if k < 0:
        return None
    return (direction * eta + n * (eta * cos_i - math.sqrt(k))).normalized()


def find_nearest(ray, objects):
    nearest = None
    for obj in objects:
        hit = obj.intersect(ray)
        if hit and (nearest is None or hit.distance < nearest.distance):
            nearest = hit
    return nearest


def make_light_samples(light_dir, count):
    if count <= 1:
        return [light_dir.normalized()]

    rnd = random.Random(13)
    main = light_dir.normalized()
    helper = Vec3(0, 1, 0) if abs(main.y) < 0.95 else Vec3(1, 0, 0)
    right = main.cross(helper).normalized()
    up = right.cross(main).normalized()

    samples = []
    for _ in range(count):
        radius = 0.11 * math.sqrt(rnd.random())
        angle = 2.0 * math.pi * rnd.random()
        offset = right * (math.cos(angle) * radius) + up * (math.sin(angle) * radius)
        samples.append((main + offset).normalized())
    return samples


def shadow_factor(point, normal, scene):
    visible = 0
    samples = make_light_samples(scene.light_dir, scene.soft_samples)

    for light_direction in samples:
        origin = point + normal * EPS
        shadow_ray = Ray(origin, light_direction)
        if find_nearest(shadow_ray, scene.objects) is None:
            visible += 1

    return visible / len(samples)


def shade(hit, ray, scene, use_shadows):
    normal = hit.normal
    view_dir = -ray.direction
    light_visibility = shadow_factor(hit.point, normal, scene) if use_shadows else 1.0
    ndotl = max(0.0, normal.dot(scene.light_dir))

    diffuse = hit.material.color * ndotl * light_visibility
    half_dir = (scene.light_dir + view_dir).normalized()
    spec_power = max(0.0, normal.dot(half_dir)) ** 60
    specular = scene.light_color * spec_power * hit.material.specular * light_visibility
    ambient = hit.material.color * scene.ambient
    return ambient + diffuse * scene.light_color + specular


def trace(ray, scene, depth, options):
    hit = find_nearest(ray, scene.objects)
    if hit is None:
        t = 0.5 * (ray.direction.y + 1.0)
        return scene.background * (1.0 - t) + Vec3(0.55, 0.72, 0.95) * t

    local_color = shade(hit, ray, scene, options["shadows"])
    color = local_color

    if depth > 0 and options["reflection"] and hit.material.reflection > 0:
        reflection_dir = reflect(ray.direction, hit.normal).normalized()
        reflection_ray = Ray(hit.point + hit.normal * EPS, reflection_dir)
        reflected = trace(reflection_ray, scene, depth - 1, options)
        color = color * (1.0 - hit.material.reflection) + reflected * hit.material.reflection

    if depth > 0 and options["refraction"] and hit.material.transparency > 0:
        refraction_dir = refract(ray.direction, hit.normal, 1.0, hit.material.refractive_index)
        if refraction_dir is not None:
            offset_normal = -hit.normal if ray.direction.dot(hit.normal) > 0 else hit.normal
            refraction_ray = Ray(hit.point - offset_normal * EPS, refraction_dir)
            refracted = trace(refraction_ray, scene, depth - 1, options)
            color = color * (1.0 - hit.material.transparency) + refracted * hit.material.transparency

    return color


def create_camera_ray(x, y, width, height):
    fov = math.radians(65)
    aspect = width / height
    px = (2.0 * ((x + 0.5) / width) - 1.0) * math.tan(fov / 2.0) * aspect
    py = (1.0 - 2.0 * ((y + 0.5) / height)) * math.tan(fov / 2.0)
    origin = Vec3(0, 0.5, -5)
    direction = Vec3(px, py, 1.0).normalized()
    return Ray(origin, direction)


def render(scene, filename, width=420, height=300, max_depth=3, options=None):
    if options is None:
        options = {"shadows": True, "reflection": True, "refraction": True}

    pixels = []
    for y in range(height):
        for x in range(width):
            ray = create_camera_ray(x, y, width, height)
            color = trace(ray, scene, max_depth, options).clamp()
            pixels.append(color)

    with open(filename, "w", encoding="ascii") as file:
        file.write(f"P3\n{width} {height}\n{MAX_COLOR}\n")
        for color in pixels:
            r = int(color.x * MAX_COLOR)
            g = int(color.y * MAX_COLOR)
            b = int(color.z * MAX_COLOR)
            file.write(f"{r} {g} {b}\n")

    save_bmp(filename.replace(".ppm", ".bmp"), pixels, width, height)


def save_bmp(filename, pixels, width, height):
    row_padding = (4 - (width * 3) % 4) % 4
    row_size = width * 3 + row_padding
    pixel_data_size = row_size * height
    file_size = 14 + 40 + pixel_data_size

    with open(filename, "wb") as file:
        file.write(b"BM")
        file.write(struct.pack("<IHHI", file_size, 0, 0, 54))
        file.write(struct.pack("<IIIHHIIIIII", 40, width, height, 1, 24, 0, pixel_data_size, 2835, 2835, 0, 0))

        for y in range(height - 1, -1, -1):
            start = y * width
            for color in pixels[start:start + width]:
                r = int(color.x * MAX_COLOR)
                g = int(color.y * MAX_COLOR)
                b = int(color.z * MAX_COLOR)
                file.write(struct.pack("BBB", b, g, r))
            file.write(b"\x00" * row_padding)


def base_spheres(extra_materials=False):
    red = Material(Vec3(0.85, 0.13, 0.12), specular=0.25)
    green = Material(Vec3(0.12, 0.65, 0.24), specular=0.2)
    blue = Material(Vec3(0.15, 0.28, 0.9), specular=0.35)
    mirror = Material(Vec3(0.92, 0.92, 0.9), reflection=0.75, specular=0.9)
    glass = Material(Vec3(0.75, 0.9, 1.0), reflection=0.12, transparency=0.78, refractive_index=1.5, specular=0.8)

    objects = [
        Sphere(Vec3(-1.55, 0.15, 2.4), 0.75, red),
        Sphere(Vec3(0.15, -0.1, 2.0), 0.5, green),
        Sphere(Vec3(1.35, 0.2, 2.9), 0.8, blue),
    ]

    if extra_materials:
        objects.append(Sphere(Vec3(-0.15, 1.05, 3.35), 0.55, mirror))
        objects.append(Sphere(Vec3(0.85, -0.05, 1.35), 0.42, glass))

    return objects


def task_a_scene():
    return Scene(
        objects=base_spheres(),
        background=Vec3(0.06, 0.07, 0.09),
        light_dir=Vec3(-0.45, 0.8, -0.4),
        light_color=Vec3(1.0, 0.95, 0.85),
        ambient=0.17,
        soft_samples=1,
    )


def task_b_scene():
    floor = Plane(Vec3(0, -0.85, 0), Vec3(0, 1, 0), Material(Vec3(0.72, 0.72, 0.68), reflection=0.18, specular=0.15))
    objects = base_spheres(extra_materials=True) + [floor]
    return Scene(
        objects=objects,
        background=Vec3(0.05, 0.07, 0.1),
        light_dir=Vec3(-0.5, 0.78, -0.38),
        light_color=Vec3(1.0, 0.96, 0.88),
        ambient=0.12,
        soft_samples=1,
    )


def task_c_scene():
    floor = Plane(Vec3(0, -0.85, 0), Vec3(0, 1, 0), Material(Vec3(0.65, 0.68, 0.7), reflection=0.12, specular=0.2))
    objects = base_spheres(extra_materials=True) + [floor]
    return Scene(
        objects=objects,
        background=Vec3(0.04, 0.055, 0.08),
        light_dir=Vec3(-0.35, 0.88, -0.32),
        light_color=Vec3(0.96, 0.97, 1.0),
        ambient=0.08,
        soft_samples=18,
    )


def main():
    render(
        task_a_scene(),
        "task_A.ppm",
        options={"shadows": True, "reflection": False, "refraction": False},
        max_depth=0,
    )
    render(
        task_b_scene(),
        "task_B.ppm",
        options={"shadows": True, "reflection": True, "refraction": False},
        max_depth=1,
    )
    render(
        task_c_scene(),
        "task_C.ppm",
        options={"shadows": True, "reflection": True, "refraction": True},
        max_depth=4,
    )
    print("Done: task_A/task_B/task_C in PPM and BMP formats")


if __name__ == "__main__":
    main()
