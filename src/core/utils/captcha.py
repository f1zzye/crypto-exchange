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

    def _create_number_image(self, number, pattern):
        img = Image.new("RGBA", (self.size, self.size), self.bg_color)
        draw = ImageDraw.Draw(img)

        self._draw_pattern(draw, pattern)
        img = self._rounded_rect(img, self.corner_radius)

        draw = ImageDraw.Draw(img)
        font = self._get_font()
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)

        x = (self.size - (bbox[2] - bbox[0])) // 2
        y = (self.size - (bbox[3] - bbox[1])) // 2

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
            num1 = random.randint(1, 9)
            num2 = random.randint(1, 9)
            result = num1 + num2
        elif operation == "-":
            num1 = random.randint(2, 9)
            num2 = random.randint(1, num1)
            result = num1 - num2
        else:
            num1 = random.randint(2, 5)
            num2 = random.randint(2, 4)
            result = num1 * num2

        return num1, num2, operation, result

    def generate(self):
        num1, num2, operation, result = self._generate_math_operation()

        pattern1 = random.choice(self.patterns)
        pattern2 = random.choice(self.patterns)

        img1_b64 = self._create_number_image(num1, pattern1)
        img2_b64 = self._create_number_image(num2, pattern2)

        return {
            "img1": f"data:image/png;base64,{img1_b64}",
            "img2": f"data:image/png;base64,{img2_b64}",
            "operation": operation,
            "result": result,
        }