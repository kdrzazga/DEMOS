from .ibm_logo_relief import IbmLogoRelief


class ProjectingSignPanel:
    def __init__(self, wall_footprint, front_footprint, start_angle, end_angle,
                 bottom_height, top_height, bar_protrusion=0.35):
        self.plate_front_face, self.plate_rim_faces = self.build_plate_faces(
            wall_footprint, front_footprint, start_angle, end_angle, bottom_height, top_height)
        self.logo_relief = IbmLogoRelief(
            front_footprint, front_footprint.resized_by(bar_protrusion),
            start_angle, end_angle, bottom_height, top_height)

    def build_plate_faces(self, wall_footprint, front_footprint, start_angle, end_angle,
                          bottom_height, top_height):
        wall_bottom_start = wall_footprint.perimeter_point(start_angle, bottom_height)
        wall_bottom_end = wall_footprint.perimeter_point(end_angle, bottom_height)
        wall_top_start = wall_footprint.perimeter_point(start_angle, top_height)
        wall_top_end = wall_footprint.perimeter_point(end_angle, top_height)
        front_bottom_start = front_footprint.perimeter_point(start_angle, bottom_height)
        front_bottom_end = front_footprint.perimeter_point(end_angle, bottom_height)
        front_top_start = front_footprint.perimeter_point(start_angle, top_height)
        front_top_end = front_footprint.perimeter_point(end_angle, top_height)

        raised_front_face = (front_bottom_start, front_bottom_end, front_top_end, front_top_start)
        bottom_rim_face = (wall_bottom_start, wall_bottom_end, front_bottom_end, front_bottom_start)
        top_rim_face = (front_top_start, front_top_end, wall_top_end, wall_top_start)
        start_rim_face = (wall_bottom_start, front_bottom_start, front_top_start, wall_top_start)
        end_rim_face = (front_bottom_end, wall_bottom_end, wall_top_end, front_top_end)
        return raised_front_face, (bottom_rim_face, top_rim_face, start_rim_face, end_rim_face)

    def render_using(self, renderer, palette):
        renderer.render_shaded_quad(self.plate_front_face, palette.sign_background_color)
        for rim_face in self.plate_rim_faces:
            renderer.render_shaded_quad(rim_face, palette.sign_panel_color)
        self.logo_relief.render_using(renderer, palette.sign_bar_color)
