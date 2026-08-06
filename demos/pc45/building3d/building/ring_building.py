import math

from ..color_palette import BuildingColorPalette
from ..ground_plane import GroundPlane

from .building_floor import BuildingFloor
from .elliptical_footprint import EllipticalFootprint
from .facade_color_scheme import FacadeColorScheme
from .illumination_scheme import WindowIlluminationScheme
from .projecting_sign_panel import ProjectingSignPanel
from .staircase_shaft import StaircaseShaft


class RingBuilding:
    def __init__(self, outer_semi_width=30.0, outer_semi_depth=7.5, wall_depth=3.0,
                 wall_bulge_amount=0.08, upper_floor_count=8, upper_floor_height=2.4,
                 ground_floor_height=4.4,
                 upper_segment_count=64, ground_segment_count=32, pillar_availability=True,
                 pillar_placement_angle=0.9, palette=None, illumination_scheme=None,
                 color_scheme=None, window_protrusion=0.1, ground_window_margin_ratio=0.05,
                 ground_window_sill_ratio=0.10, upper_window_margin_ratio=0.16,
                 upper_window_sill_ratio=0.18, ground_window_rows_per_floor=1,
                 upper_window_rows_per_floor=2, signage_column_offset_from_corner=2,
                 signage_column_span=3, signage_top_floor_from_top=2,
                 signage_height_in_floors=1.5, signage_protrusion=1.0,
                 signage_rightward_shift=2.0):
        self.pillar_availability = pillar_availability
        self.palette = palette if palette is not None else BuildingColorPalette()
        illumination = illumination_scheme if illumination_scheme is not None else WindowIlluminationScheme()
        self.color_scheme = color_scheme if color_scheme is not None else FacadeColorScheme()
        self.total_height = ground_floor_height + upper_floor_count * upper_floor_height
        self.outer_footprint = EllipticalFootprint(
            outer_semi_width, outer_semi_depth, self.total_height, wall_bulge_amount)
        self.inner_footprint = self.outer_footprint.resized_by(-wall_depth)
        self.window_footprint = self.outer_footprint.resized_by(window_protrusion)
        self.upper_boundary_angles = self.outer_footprint.evenly_spaced_boundary_angles(upper_segment_count)
        self.ground_boundary_angles = self.outer_footprint.evenly_spaced_boundary_angles(ground_segment_count)
        self.floors = self.build_stacked_floors(
            upper_floor_count, upper_floor_height, ground_floor_height, illumination,
            ground_window_margin_ratio, ground_window_sill_ratio,
            upper_window_margin_ratio, upper_window_sill_ratio,
            ground_window_rows_per_floor, upper_window_rows_per_floor)
        self.roof_ring_quads = self.build_roof_ring_quads()
        self.ground_plane = GroundPlane()
        self.staircase_shaft = self.build_staircase_shaft(pillar_placement_angle, upper_floor_count)
        self.signage_panel = self.build_signage_panel(
            upper_segment_count, upper_floor_height, signage_column_offset_from_corner,
            signage_column_span, signage_top_floor_from_top, signage_height_in_floors,
            signage_protrusion, signage_rightward_shift)

    def build_stacked_floors(self, upper_floor_count, upper_floor_height, ground_floor_height,
                             illumination, ground_window_margin_ratio, ground_window_sill_ratio,
                             upper_window_margin_ratio, upper_window_sill_ratio,
                             ground_window_rows_per_floor, upper_window_rows_per_floor):
        stacked_floors = [BuildingFloor(
            0, 0.0, ground_floor_height, self.ground_boundary_angles, self.outer_footprint,
            self.inner_footprint, self.window_footprint, ground_window_margin_ratio,
            ground_window_sill_ratio, ground_window_rows_per_floor, illumination, self.color_scheme)]
        for upper_index in range(upper_floor_count):
            bottom_height = ground_floor_height + upper_index * upper_floor_height
            top_height = bottom_height + upper_floor_height
            stacked_floors.append(BuildingFloor(
                upper_index + 1, bottom_height, top_height, self.upper_boundary_angles,
                self.outer_footprint, self.inner_footprint, self.window_footprint,
                upper_window_margin_ratio, upper_window_sill_ratio, upper_window_rows_per_floor,
                illumination, self.color_scheme))
        return tuple(stacked_floors)

    def build_roof_ring_quads(self):
        constructed_quads = []
        boundary_angles = self.upper_boundary_angles
        for segment_index in range(len(boundary_angles) - 1):
            start_angle = boundary_angles[segment_index]
            end_angle = boundary_angles[segment_index + 1]
            constructed_quads.append((
                self.outer_footprint.perimeter_point(start_angle, self.total_height),
                self.outer_footprint.perimeter_point(end_angle, self.total_height),
                self.inner_footprint.perimeter_point(end_angle, self.total_height),
                self.inner_footprint.perimeter_point(start_angle, self.total_height),
            ))
        return tuple(constructed_quads)

    def build_staircase_shaft(self, placement_angle, upper_floor_count):
        anchor_point = self.outer_footprint.perimeter_point(placement_angle, 0.0)
        outward_normal = self.outer_footprint.outward_normal_at(placement_angle)
        tangent_direction = self.outer_footprint.tangent_at(placement_angle)
        return StaircaseShaft(
            anchor_point=anchor_point,
            outward_normal=outward_normal,
            tangent_direction=tangent_direction,
            tangential_width=6.0,
            radial_depth=4.5,
            total_height=self.total_height + 3.0,
            window_row_count=upper_floor_count + 2,
            palette=self.palette)

    def build_signage_panel(self, upper_segment_count, upper_floor_height,
                            column_offset_from_corner, column_span, top_floor_from_top,
                            height_in_floors, protrusion, rightward_shift):

        left_corner_boundary_index = upper_segment_count // 2
        near_boundary_index = left_corner_boundary_index - column_offset_from_corner + 1
        far_boundary_index = near_boundary_index - column_span
        start_angle = self.upper_boundary_angles[far_boundary_index]
        end_angle = self.upper_boundary_angles[near_boundary_index]
        angular_shift = self.horizontal_shift_to_angular_shift(rightward_shift, 0.5 * (start_angle + end_angle))
        start_angle += angular_shift
        end_angle += angular_shift
        top_height = self.total_height - (top_floor_from_top - 1) * upper_floor_height
        bottom_height = top_height - height_in_floors * upper_floor_height
        panel_front_footprint = self.outer_footprint.resized_by(protrusion)

        return self.assemble_signage_panel(
            panel_front_footprint, start_angle, end_angle, bottom_height, top_height)

    def horizontal_shift_to_angular_shift(self, rightward_shift, center_angle):
        horizontal_derivative = -self.outer_footprint.semi_width * math.sin(center_angle)
        if horizontal_derivative == 0.0:
            return 0.0
        return rightward_shift / horizontal_derivative

    def assemble_signage_panel(self, panel_front_footprint, start_angle, end_angle,
                               bottom_height, top_height):
        return ProjectingSignPanel(
            self.outer_footprint, panel_front_footprint, start_angle, end_angle,
            bottom_height, top_height)

    def render_using(self, renderer):
        self.ground_plane.render_using(renderer, self.palette)
        for floor in self.floors:
            floor.render_using(renderer, self.palette)
        for quad in self.roof_ring_quads:
            renderer.render_shaded_quad(quad, self.palette.roof_color)
        self.signage_panel.render_using(renderer, self.palette)
        if self.pillar_availability:
            self.staircase_shaft.render_using(renderer, self.palette)
