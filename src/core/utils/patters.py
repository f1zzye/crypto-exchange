import secrets
from PIL import ImageDraw


class PatternDrawer:

    AVAILABLE_PATTERNS: list[str] = ["rings", "grid", "triangles", "diamonds"]

    def __init__(self, size: int, line_color: str):
        self.size = size
        self.line_color = line_color

    def draw(self, draw: ImageDraw.ImageDraw, pattern: str, width: int = 1) -> None:

        patterns = {
            "rings": self._draw_rings,
            "grid": self._draw_grid,
            "triangles": self._draw_triangles,
            "diamonds": self._draw_diamonds,
        }

        pattern_func = patterns.get(pattern)

        pattern_func(draw, width)

    def _draw_rings(self, draw: ImageDraw.ImageDraw, width: int) -> None:
        step = 16
        ring_size = 12

        for i in range(0, self.size, step):
            for j in range(0, self.size, step):
                draw.ellipse(
                    [i, j, i + ring_size, j + ring_size],
                    outline=self.line_color,
                    width=width,
                )

    def _draw_grid(self, draw: ImageDraw.ImageDraw, width: int) -> None:
        step = 8

        for x in range(0, self.size, step):
            draw.line([(x, 0), (x, self.size)], fill=self.line_color, width=width)
        for y in range(0, self.size, step):
            draw.line([(0, y), (self.size, y)], fill=self.line_color, width=width)

    def _draw_triangles(self, draw: ImageDraw.ImageDraw, width: int) -> None:
        step = 16

        for x in range(0, self.size, step):
            for y in range(0, self.size, step):
                points = [(x + step // 2, y), (x, y + step), (x + step, y + step)]
                draw.polygon(points, outline=self.line_color, fill=None, width=width)

    def _draw_diamonds(self, draw: ImageDraw.ImageDraw, width: int) -> None:
        step = 16

        for x in range(0, self.size, step):
            for y in range(0, self.size, step):
                points = [
                    (x + step // 2, y),
                    (x, y + step // 2),
                    (x + step // 2, y + step),
                    (x + step, y + step // 2),
                ]
                draw.polygon(points, outline=self.line_color, fill=None, width=width)

    @classmethod
    def get_different_patterns(cls) -> tuple[str, str]:
        pattern_1 = secrets.choice(cls.AVAILABLE_PATTERNS)
        pattern_2 = secrets.choice(
            [p for p in cls.AVAILABLE_PATTERNS if p != pattern_1]
        )
        return pattern_1, pattern_2
