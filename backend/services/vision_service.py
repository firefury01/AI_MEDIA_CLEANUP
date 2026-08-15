import io
from PIL import Image
from rembg import remove, new_session

# Global lightweight session (Startup par load hoga, request par nahi)
session = new_session("u2netp")

def remove_background(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    # Downscale for instant processing on low CPU
    image.thumbnail((800, 800), Image.Resampling.BILINEAR)
    
    output = remove(image, session=session)
    
    out_io = io.BytesIO()
    output.save(out_io, format="PNG", optimize=True)
    return out_io.getvalue()