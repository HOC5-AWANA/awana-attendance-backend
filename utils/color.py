COLORS = ['Red', 'Yellow', 'Green', 'Blue']

class Color:
    def __init__(self):
        self.sparks_color_index = 0
        self.tnt_color_index = 0

    def select_color_sparks(self):
        if self.sparks_color_index >= len(COLORS):
            self.sparks_color_index = 0
        selected_color = COLORS[self.sparks_color_index]
        self.sparks_color_index += 1
        return selected_color

    def select_color_tnt(self):
        if self.tnt_color_index >= len(COLORS):
            self.tnt_color_index = 0
        selected_color = COLORS[self.tnt_color_index]
        self.tnt_color_index += 1
        return selected_color
