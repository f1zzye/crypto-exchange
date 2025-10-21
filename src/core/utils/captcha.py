from PIL import Image, ImageDraw

from .font_loader import FontLoader
from .image_processor import ImageProcessor
from .math_operations import MathOperationGenerator
from .patters import PatternDrawer


class CaptchaGenerator:

    DEFAULT_SIZE: int = 50
    FONT_SIZE_RATIO: int = 0.6
    TEXT_MARGIN: int = 3

    DEFAULT_BG_COLOR: str = "#E0E0E0"
    DEFAULT_LINE_COLOR: str = "#555555"
    TEXT_COLOR: str = "#000"
    SHADOW_COLOR: str = "#555"

    DEFAULT_ELLIPSE_WIDTH: int = 2
    DEFAULT_LINE_WIDTH: int = 1
    DEFAULT_CORNER_RADIUS: int = 12

    def __init__(
        self,
        size: int = DEFAULT_SIZE,
        corner_radius: int = DEFAULT_CORNER_RADIUS,
        bg_color: str = DEFAULT_BG_COLOR,
        line_color: str = DEFAULT_LINE_COLOR,
        ellipse_width: int = DEFAULT_ELLIPSE_WIDTH,
        line_width: int = DEFAULT_LINE_WIDTH,
    ):

        self.size = size
        self.corner_radius = corner_radius
        self.bg_color = bg_color
        self.line_color = line_color
        self.ellipse_width = ellipse_width
        self.line_width = line_width

        self.font_loader = FontLoader()
        self.math_generator = MathOperationGenerator()
        self.pattern_drawer = PatternDrawer(size, line_color)
        self.image_processor = ImageProcessor()

    def generate(self) -> dict[str, str | int]:
        num_1, num_2, operation, result = self.math_generator.generate()
        pattern_1, pattern_2 = self.pattern_drawer.get_different_patterns()

        img1_b64 = self._create_number_image(num_1, pattern_1)
        img2_b64 = self._create_number_image(num_2, pattern_2)

        return {
            "img1": f"data:image/png;base64,{img1_b64}",
            "img2": f"data:image/png;base64,{img2_b64}",
            "operation": operation,
            "result": result,
        }

    def _create_number_image(self, number: int, pattern: str) -> str:
        img = Image.new("RGBA", (self.size, self.size), self.bg_color)
        draw = ImageDraw.Draw(img)

        width = self.ellipse_width if pattern == "rings" else self.line_width
        self.pattern_drawer.draw(draw, pattern, width)

        img = self.image_processor.apply_rounded_corners(img, self.corner_radius)

        draw = ImageDraw.Draw(img)
        font = self.font_loader.load(int(self.size * self.FONT_SIZE_RATIO))
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)

        position = self.image_processor.get_random_text_position(
            self.size, bbox, self.TEXT_MARGIN
        )

        self.image_processor.render_text_with_shadow(
            draw, text, position, font, self.TEXT_COLOR, self.SHADOW_COLOR
        )

        return self.image_processor.image_to_base64(img)
