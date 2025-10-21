import base64
import io
import secrets

from PIL import Image, ImageDraw, ImageFont


class ImageProcessor:

    @staticmethod
    def apply_rounded_corners(img: Image.Image, radius: int) -> Image.Image:

        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)
        img.putalpha(mask)
        return img

    @staticmethod
    def get_random_text_position(
        image_size: int,
        text_bbox: tuple[int, int, int, int],
        margin: int = 3
    ) -> tuple[int, int]:

        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        max_x = image_size - text_width - margin
        max_y = image_size - text_height - margin

        if max_x < margin:
            x = (image_size - text_width) // 2
        else:
            x = secrets.randbelow(max_x - margin + 1) + margin

        if max_y < margin:
            y = (image_size - text_height) // 2
        else:
            y = secrets.randbelow(max_y - margin + 1) + margin

        return x, y

    @staticmethod
    def render_text_with_shadow(
        draw: ImageDraw.ImageDraw,
        text: str,
        position: tuple[int, int],
        font: ImageFont.FreeTypeFont,
        text_color: str = "#000",
        shadow_color: str = "#555"
    ) -> None:

        x, y = position
        draw.text((x + 1, y + 1), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill=text_color)

    @staticmethod
    def image_to_base64(img: Image.Image) -> str:
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
