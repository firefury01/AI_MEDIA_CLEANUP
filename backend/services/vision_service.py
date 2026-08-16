import io
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

# Global lightweight fast session
fast_session = new_session("u2netp")

def remove_background(image_bytes: bytes) -> bytes:
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    orig_w, orig_h = pil_image.size
    max_side = 640
    if max(orig_w, orig_h) > max_side:
        pil_image.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
        
    output_image = remove(pil_image, session=fast_session)
    
    if (orig_w, orig_h) != output_image.size:
        output_image = output_image.resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()