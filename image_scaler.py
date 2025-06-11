import argparse
from PIL import Image


def scale_image(input_path: str, output_path: str, scale: float = None,
                width: int = None, height: int = None) -> None:
    """Scale an image and save to output path.

    Either provide a scaling factor or target width/height.
    """
    img = Image.open(input_path)
    if scale:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
    else:
        if width is None and height is None:
            raise ValueError("Provide scale or width/height")
        if width is None:
            new_width = int(img.width * (height / img.height))
            new_height = height
        elif height is None:
            new_height = int(img.height * (width / img.width))
            new_width = width
        else:
            new_width = width
            new_height = height
    resized = img.resize((new_width, new_height), Image.LANCZOS)
    resized.save(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scale an image")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument("--scale", type=float, help="Scale factor (e.g. 0.5)")
    parser.add_argument("--width", type=int, help="Target width")
    parser.add_argument("--height", type=int, help="Target height")
    args = parser.parse_args()
    scale_image(args.input, args.output, args.scale, args.width, args.height)
