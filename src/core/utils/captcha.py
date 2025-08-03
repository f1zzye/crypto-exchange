import random
from PIL import Image, ImageDraw, ImageFont
import io
import base64


class CaptchaGenerator:
    def __init__(self, size=50):
        self.size = size
        self.patterns = ["rings", "grid", "triangles", "diamonds"]
        self.corner_radius = 12
        self.bg_color = "#E0E0E0"
        self.line_color = "#555555"
        self.ellipse_width = 2
        self.line_width = 1

    @staticmethod
    def _rounded_rect(img, radius):
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [0, 0, img.size[0], img.size[1]], radius=radius, fill=255
        )
        img.putalpha(mask)
        return img

    def _draw_pattern(self, draw, pattern):
        if pattern == "rings":
            self._draw_rings(draw)
        elif pattern == "grid":
            self._draw_grid(draw)
        elif pattern == "triangles":
            self._draw_triangles(draw)
        elif pattern == "diamonds":
            self._draw_diamonds(draw)

    def _draw_rings(self, draw):
        for i in range(0, self.size, 16):
            for j in range(0, self.size, 16):
                draw.ellipse(
                    [i, j, i + 12, j + 12],
                    outline=self.line_color,
                    width=self.ellipse_width,
                )

    def _draw_grid(self, draw):
        step = 8
        for x in range(0, self.size, step):
            draw.line(
                [(x, 0), (x, self.size)], fill=self.line_color, width=self.line_width
            )
        for y in range(0, self.size, step):
            draw.line(
                [(0, y), (self.size, y)], fill=self.line_color, width=self.line_width
            )

    def _draw_triangles(self, draw):
        step = 16
        for x in range(0, self.size, step):
            for y in range(0, self.size, step):
                points = [(x + step // 2, y), (x, y + step), (x + step, y + step)]
                draw.polygon(
                    points, outline=self.line_color, fill=None, width=self.line_width
                )

    def _draw_diamonds(self, draw):
        step = 16
        for x in range(0, self.size, step):
            for y in range(0, self.size, step):
                points = [
                    (x + step // 2, y),
                    (x, y + step // 2),
                    (x + step // 2, y + step),
                    (x + step, y + step // 2),
                ]
                draw.polygon(
                    points, outline=self.line_color, fill=None, width=self.line_width
                )

    def _get_font(self):
        try:
            return ImageFont.truetype("arial.ttf", int(self.size * 0.6))
        except (IOError, OSError):
            return ImageFont.load_default()

    def _get_random_text_position(self, text_bbox):
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        margin = 3
        max_x = self.size - text_width - margin
        max_y = self.size - text_height - margin
        mix_x, mix_y = margin, margin

        if max_x < mix_x:
            x = (self.size - text_width) // 2
        else:
            x = random.randint(mix_x, max_x)

        if max_y < mix_y:
            y = (self.size - text_height) // 2
        else:
            y = random.randint(mix_y, max_y)

        return x, y

    def _create_number_image(self, number, pattern):
        img = Image.new("RGBA", (self.size, self.size), self.bg_color)
        draw = ImageDraw.Draw(img)

        self._draw_pattern(draw, pattern)
        img = self._rounded_rect(img, self.corner_radius)

        draw = ImageDraw.Draw(img)
        font = self._get_font()
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)

        x, y = self._get_random_text_position(bbox)

        draw.text((x + 1, y + 1), text, font=font, fill="#555")
        draw.text((x, y), text, font=font, fill="#000")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _generate_math_operation():
        operations = ["+", "-", "x"]
        operation = random.choice(operations)

        if operation == "+":
            num_1 = random.randint(1, 9)
            num_2 = random.randint(1, 9)
            result = num_1 + num_2
        elif operation == "-":
            num_1 = random.randint(2, 9)
            num_2 = random.randint(1, num_1)
            result = num_1 - num_2
        else:
            num_1 = random.randint(2, 5)
            num_2 = random.randint(2, 4)
            result = num_1 * num_2

        return num_1, num_2, operation, result

    def _get_different_patterns(self):
        pattern_1 = random.choice(self.patterns)
        pattern_2 = random.choice([p for p in self.patterns if p != pattern_1])

        return pattern_1, pattern_2

    def generate(self):
        num_1, num_2, operation, result = self._generate_math_operation()

        pattern_1, pattern_2 = self._get_different_patterns()

        img1_b64 = self._create_number_image(num_1, pattern_1)
        img2_b64 = self._create_number_image(num_2, pattern_2)

        return {
            "img1": f"data:image/png;base64,{img1_b64}",
            "img2": f"data:image/png;base64,{img2_b64}",
            "operation": operation,
            "result": result,
        }
