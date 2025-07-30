import random
from PIL import Image, ImageDraw, ImageFont
import io
import base64


class CaptchaGenerator:
    def __init__(self, size: int = 50):
        self.size = size
        self.patterns = ["rings", "grid", "triangles", "diamonds"]
        self.bg_color = "#E0E0E0"
        self.corner_radius = 12

    @staticmethod
    def _rounded_rect(img, radius) -> Image:
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)
        img.putalpha(mask)
        return img

    def _draw_pattern(self, draw, pattern) -> None:
        if pattern == "rings":
            for i in range(0, self.size, 16):
                for j in range(0, self.size, 16):
                    draw.ellipse([i, j, i+12, j+12], outline="#CCCCCC", width=2)
        elif pattern == "grid":
            step = 8
            for x in range(0, self.size, step):
                draw.line([(x, 0), (x, self.size)], fill="#CCCCCC", width=1)
            for y in range(0, self.size, step):
                draw.line([(0, y), (self.size, y)], fill="#CCCCCC", width=1)

        elif pattern == "triangles":
            step = 16
            for x in range(0, self.size, step):
                for y in range(0, self.size, step):
                    points = [(x + step // 2, y), (x, y + step), (x + step, y + step)]
                    draw.polygon(points, outline="#CCCCCC", fill=None)
        elif pattern == "diamonds":
            step = 16
            for x in range(0, self.size, step):
                for y in range(0, self.size, step):
                    points = [
                        (x + step // 2, y),
                        (x, y + step // 2),
                        (x + step // 2, y + step),
                        (x + step, y + step // 2)
                    ]
                    draw.polygon(points, outline="#CCCCCC", fill=None)

    def _create_number_image(self, number: int, pattern: str):
        img = Image.new("RGBA", (self.size, self.size), self.bg_color)
        draw = ImageDraw.Draw(img)

        self._draw_pattern(draw, pattern)
        img = self._rounded_rect(img, self.corner_radius)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", int(self.size * 0.6))
        except IOError:
            font = ImageFont.load_default()

        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (self.size - (bbox[2] - bbox[0])) // 2
        y = (self.size - (bbox[3] - bbox[1])) // 2

        draw.text((x + 1, y + 1), text, font=font, fill="#555")
        draw.text((x, y), text, font=font, fill="#000")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def generate(self):
        num1 = random.randint(1, 9)
        num2 = random.randint(1, 9)
        operations = ["+", "-", "*"]
        operation = random.choice(operations)

        if operation == "-" and num1 < num2:
            num1, num2 = num2, num1
        elif operation == "*":
            num1 = random.randint(2, 5)
            num2 = random.randint(2, 4)

        if operation == "+":
            result = num1 + num2
        elif operation == "-":
            result = num1 - num2
        else:
            result = num1 * num2

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