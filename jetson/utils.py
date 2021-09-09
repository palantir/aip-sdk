import numpy as np

from PIL import Image


def read_png_or_tiff(image_path):
    return np.array(Image.open(image_path).convert("RGB")).astype(np.uint8)


def read_bgr888_or_rgb888(image_path, image_height, image_width):
    with open(image_path, "rb") as infile:
        data = infile.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        return arr.reshape(image_height, image_width, 3)
