import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *

from demos.WinterDemo26.sitting_silhouette import SittingSilhouette


class Desk:

    def __init__(self, x, y, z, length=2.4, depth=0.7, height=0.76, facing=0.0,
                 laptop_count=2, bottle_count=3, with_bench=True, occupancy=0.6, size=1.0, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.length = length
        self.depth = depth
        self.height = height
        self.facing = facing
        self.size = size
        self.laptop_count = laptop_count
        self.bottle_count = bottle_count
        self.with_bench = with_bench
        self.occupancy = occupancy
        self.random_generator = random.Random(seed)

        self.top_thickness = 0.04
        self.leg_width = 0.05
        self.leg_spread = 0.26
        self.leg_inset = 0.18
        self.bench_height = 0.46
        self.bench_depth = 0.26
        self.bench_gap = 0.28

        self.laptop_width = 0.34
        self.laptop_depth = 0.24
        self.laptop_base_thickness = 0.018
        self.laptop_lid_thickness = 0.008
        self.laptop_open_angle = 108.0
        self.laptop_bezel = 0.012

        self.bottle_radius = 0.035
        self.bottle_body_height = 0.17
        self.bottle_neck_height = 0.07
        self.bottle_neck_radius = 0.013

        self.wood_color = (0.55, 0.32, 0.18)
        self.bench_color = (0.44, 0.25, 0.14)
        self.plank_line_color = (0.30, 0.17, 0.09)
        self.leg_color = (0.22, 0.20, 0.20)
        self.laptop_color = (0.16, 0.16, 0.18)
        self.screen_colors = ((0.62, 0.78, 1.0), (0.85, 0.90, 1.0), (0.55, 1.0, 0.75), (1.0, 0.85, 0.55))
        self.bottle_colors = ((1.0, 0.45, 0.08), (0.92, 0.30, 0.05), (0.85, 0.12, 0.10))
        self.cap_color = (0.85, 0.85, 0.88)
        self.sitter_colors = ((0.12, 0.10, 0.16), (0.16, 0.12, 0.10), (0.10, 0.12, 0.14))

        self.plank_count = 4
        self.screen_glow = 1.0

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.laptops = self._build_laptops()
        self.bottles = self._build_bottles()
        self.sitters = self._build_sitters()
        self.sitter_back_z = self.depth / 2.0 + self.bench_gap + self.bench_depth / 2.0 + 0.12
        self.item_order = self._build_item_order()
        self.display_list = self._compile()

    def _build_laptops(self):
        laptops = []
        if self.laptop_count <= 0:
            return laptops
        seat_width = self.length / self.laptop_count
        for index in range(self.laptop_count):
            center_x = -self.length / 2.0 + seat_width * (index + 0.5)
            center_x += self.random_generator.uniform(-0.06, 0.06)
            center_z = self.depth * 0.12 + self.random_generator.uniform(-0.03, 0.03)
            yaw = self.random_generator.uniform(-8.0, 8.0)
            screen_color = self.random_generator.choice(self.screen_colors)
            laptops.append((center_x, center_z, yaw, screen_color))
        return laptops

    def _build_bottles(self):
        bottles = []
        taken = [laptop[0] for laptop in self.laptops]
        for _ in range(self.bottle_count):
            for _attempt in range(12):
                bottle_x = self.random_generator.uniform(-self.length / 2.0 + 0.1, self.length / 2.0 - 0.1)
                if all(abs(bottle_x - laptop_x) > self.laptop_width * 0.7 for laptop_x in taken):
                    break
            bottle_z = self.random_generator.uniform(-self.depth * 0.35, -self.depth * 0.1)
            color = self.random_generator.choice(self.bottle_colors)
            taken.append(bottle_x)
            bottles.append((bottle_x, bottle_z, color))
        return bottles

    def _build_sitters(self):
        """Seat index -> sitter for about `occupancy` of the laptop seats; the rest stay empty.
        The count is rounded up or down at random so the average over many desks matches."""
        seat_count = len(self.laptops)
        occupied_count = min(seat_count, int(self.occupancy * seat_count + self.random_generator.random()))
        occupied_seats = sorted(self.random_generator.sample(range(seat_count), occupied_count))
        return {seat: SittingSilhouette(self.random_generator.choice(self.sitter_colors),
                                        phase=self.random_generator.uniform(0.0, 1.0))
                for seat in occupied_seats}

    def _build_item_order(self):
        """Placement order: first laptop, first bottle, remaining laptops, remaining bottles, sitters."""
        laptop_items = [("laptop", index) for index in range(len(self.laptops))]
        bottle_items = [("bottle", index) for index in range(len(self.bottles))]
        sitter_items = [("sitter", seat) for seat in self.sitters]
        return laptop_items[:1] + bottle_items[:1] + laptop_items[1:] + bottle_items[1:] + sitter_items

    def item_count(self):
        return len(self.item_order)

    def _box(self, min_corner, max_corner):
        x0, y0, z0 = min_corner
        x1, y1, z1 = max_corner
        faces = (
            ((0.0, 1.0, 0.0), ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))),
            ((0.0, -1.0, 0.0), ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))),
            ((0.0, 0.0, 1.0), ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))),
            ((0.0, 0.0, -1.0), ((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0))),
            ((1.0, 0.0, 0.0), ((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1))),
            ((-1.0, 0.0, 0.0), ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))),
        )
        glBegin(GL_QUADS)
        for normal, corners in faces:
            glNormal3f(*normal)
            for corner in corners:
                glVertex3f(*corner)
        glEnd()

    def _draw_slanted_leg(self, bottom, top):
        """A square post from bottom to top point, both in the local Y-Z plane at fixed X."""
        half = self.leg_width / 2.0
        leg_x, bottom_y, bottom_z = bottom
        _, top_y, top_z = top
        glPushMatrix()
        glTranslatef(leg_x, bottom_y, bottom_z)
        tilt = math.degrees(math.atan2(top_z - bottom_z, top_y - bottom_y))
        glRotatef(tilt, 1.0, 0.0, 0.0)
        post_length = math.hypot(top_z - bottom_z, top_y - bottom_y)
        self._box((-half, 0.0, -half), (half, post_length, half))
        glPopMatrix()

    def _draw_trestle(self, leg_x, top_y, spread, reach):
        """Folding A-frame legs at one end, like the beer-garden tables in the hall."""
        glColor3f(*self.leg_color)
        self._draw_slanted_leg((leg_x, 0.0, -reach), (leg_x, top_y, -spread))
        self._draw_slanted_leg((leg_x, 0.0, reach), (leg_x, top_y, spread))
        brace_y = top_y * 0.35
        brace_half = reach - (reach - spread) * 0.35
        self._box((leg_x - self.leg_width * 0.3, brace_y - 0.015, -brace_half),
                  (leg_x + self.leg_width * 0.3, brace_y + 0.015, brace_half))

    def _draw_table_top(self):
        half_length = self.length / 2.0
        half_depth = self.depth / 2.0
        top_y = self.height
        glColor3f(*self.wood_color)
        self._box((-half_length, top_y - self.top_thickness, -half_depth), (half_length, top_y, half_depth))

        glDisable(GL_LIGHTING)
        glColor3f(*self.plank_line_color)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for plank in range(1, self.plank_count):
            plank_z = -half_depth + self.depth * plank / self.plank_count
            glVertex3f(-half_length, top_y + 0.001, plank_z)
            glVertex3f(half_length, top_y + 0.001, plank_z)
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_table(self):
        self._draw_table_top()
        leg_x = self.length / 2.0 - self.leg_inset
        leg_top = self.height - self.top_thickness
        for side in (-1.0, 1.0):
            self._draw_trestle(side * leg_x, leg_top, self.depth * 0.18, self.depth * self.leg_spread / 0.6)

    def _draw_bench(self):
        half_length = self.length / 2.0
        bench_z = self.depth / 2.0 + self.bench_gap + self.bench_depth / 2.0
        glPushMatrix()
        glTranslatef(0.0, 0.0, bench_z)
        glColor3f(*self.bench_color)
        self._box((-half_length, self.bench_height - self.top_thickness, -self.bench_depth / 2.0),
                  (half_length, self.bench_height, self.bench_depth / 2.0))
        leg_x = half_length - self.leg_inset
        leg_top = self.bench_height - self.top_thickness
        for side in (-1.0, 1.0):
            self._draw_trestle(side * leg_x, leg_top, self.bench_depth * 0.2, self.bench_depth * 0.55)
        glPopMatrix()

    def _draw_laptop(self, screen_color):
        half_width = self.laptop_width / 2.0
        half_depth = self.laptop_depth / 2.0
        glColor3f(*self.laptop_color)
        self._box((-half_width, 0.0, -half_depth), (half_width, self.laptop_base_thickness, half_depth))

        glPushMatrix()
        glTranslatef(0.0, self.laptop_base_thickness, -half_depth)
        glRotatef(self.laptop_open_angle - 90.0, -1.0, 0.0, 0.0)
        glColor3f(*self.laptop_color)
        self._box((-half_width, 0.0, -self.laptop_lid_thickness), (half_width, self.laptop_depth, 0.0))

        bezel = self.laptop_bezel
        glDisable(GL_LIGHTING)
        glColor3f(screen_color[0] * self.screen_glow, screen_color[1] * self.screen_glow,
                  screen_color[2] * self.screen_glow)
        glBegin(GL_QUADS)
        glVertex3f(-half_width + bezel, bezel, 0.001)
        glVertex3f(half_width - bezel, bezel, 0.001)
        glVertex3f(half_width - bezel, self.laptop_depth - bezel, 0.001)
        glVertex3f(-half_width + bezel, self.laptop_depth - bezel, 0.001)
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_placed_laptop(self, index):
        center_x, center_z, yaw, screen_color = self.laptops[index]
        glPushMatrix()
        glTranslatef(center_x, self.height, center_z)
        glRotatef(yaw, 0.0, 1.0, 0.0)
        self._draw_laptop(screen_color)
        glPopMatrix()

    def _draw_bottle(self, color):
        glPushMatrix()
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        glColor3f(*color)
        gluCylinder(self.quadric, self.bottle_radius, self.bottle_radius, self.bottle_body_height, 12, 1)
        glTranslatef(0.0, 0.0, self.bottle_body_height)
        gluCylinder(self.quadric, self.bottle_radius, self.bottle_neck_radius, self.bottle_neck_height * 0.4, 12, 1)
        glTranslatef(0.0, 0.0, self.bottle_neck_height * 0.4)
        gluCylinder(self.quadric, self.bottle_neck_radius, self.bottle_neck_radius, self.bottle_neck_height * 0.6, 8, 1)
        glTranslatef(0.0, 0.0, self.bottle_neck_height * 0.6)
        glColor3f(*self.cap_color)
        gluDisk(self.quadric, 0.0, self.bottle_neck_radius * 1.15, 8, 1)
        glPopMatrix()

    def _draw_sitter(self, index):
        center_x = self.laptops[index][0]
        glPushMatrix()
        glTranslatef(center_x, 0.0, self.sitter_back_z)
        glRotatef(90.0, 0.0, 1.0, 0.0)
        self.sitters[index].draw()
        glPopMatrix()

    def _draw_placed_bottle(self, index):
        bottle_x, bottle_z, color = self.bottles[index]
        glPushMatrix()
        glTranslatef(bottle_x, self.height, bottle_z)
        self._draw_bottle(color)
        glPopMatrix()

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_table()
        if self.with_bench:
            self._draw_bench()
        glEndList()
        return display_list

    def update(self, delta_seconds):
        for sitter in self.sitters.values():
            sitter.update(delta_seconds)

    def draw(self, screen_glow=1.0, visible_items=None):
        """Draw the table plus the first `visible_items` items of item_order (all when None)."""
        self.screen_glow = screen_glow
        shown_items = self.item_order if visible_items is None else self.item_order[:max(0, visible_items)]
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.display_list)
        for kind, index in shown_items:
            if kind == "laptop":
                self._draw_placed_laptop(index)
            elif kind == "bottle":
                self._draw_placed_bottle(index)
            else:
                self._draw_sitter(index)
        glPopMatrix()
