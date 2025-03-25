from PIL import Image, ImageDraw, ImageFont

def create_text_overlay(text, font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size=50):
    """
    Creates a text overlay image using PIL.

    Args:
        text (str): The text to overlay on the image.
        font_path (str): Path to the font file.
        font_size (int): Size of the text.

    Returns:
        str: Path to the saved image containing the text overlay.
    """
    try:
        # Load font
        font = ImageFont.truetype(font_path, font_size)

        # Create an empty image with white background
        image = Image.new("RGBA", (1920, 1080), (255, 255, 255, 0))  # Adjust size if needed
        draw = ImageDraw.Draw(image)

        # Get text size using textbbox (bounding box)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position the text in the center
        x = (image.width - text_width) / 2
        y = (image.height - text_height) / 2

        # Draw text
        draw.text((x, y), text, font=font, fill="white")

        # Save the image with text overlay
        text_overlay_path = "text_overlay.png"
        image.save(text_overlay_path)
        print(f"Text overlay saved at {text_overlay_path}")

        return text_overlay_path
    except Exception as e:
        print(f"Error creating text overlay: {e}")
        return None

# Example usage of the create_text_overlay function
if __name__ == "__main__":
    prompt = "A futuristic cityscape with flying cars"
    create_text_overlay(f"Exploring: {prompt}")
