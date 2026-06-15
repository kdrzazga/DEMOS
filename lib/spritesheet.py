import arcade


def create_textures_from_sheet(sheet_path, number_of_textures):
    sheet_texture = arcade.load_texture(sheet_path)
    sheet_width = sheet_texture.width
    sheet_height = sheet_texture.height
    texture_width = sheet_width // number_of_textures
    texture_height = sheet_height
    textures = []
    for i in range(number_of_textures):
        x = i * texture_width
        y = 0
        Te
        texture = arcade.load_texture(sheet_texture, x, y, texture_width, texture_height )
        textures.append(texture)
    return textures
