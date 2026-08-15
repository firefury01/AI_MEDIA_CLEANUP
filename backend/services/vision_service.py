import io
from PIL import Image
from rembg import remove, new_session

_session = None

def get_session():
    global _session
    if _session is None:
        _session = new_session("u2netp")
    return _session

def init_vision_model():
    """Dummy startup hook to prevent main.py import error & keep startup instant"""
    pass

def remove_image_background(image_bytes: bytes) -> bytes:
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    # Large images resize for performance
    max_dim = 1200
    if max(input_image.size) > max_dim:
        input_image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    
    session = get_session()
    output_image = remove(input_image, session=session)
    
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    return output_buffer.getvalue()

# Alias for backwards compatibility
remove_background = remove_image_background