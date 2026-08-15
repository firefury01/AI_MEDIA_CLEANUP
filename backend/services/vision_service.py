import io
from PIL import Image
from rembg import remove, new_session

_session = None

def get_session(model_name: str = "u2netp", *args, **kwargs):
    global _session
    if _session is None:
        _session = new_session(model_name)
    return _session

def init_vision_model(*args, **kwargs):
    """
    Startup hook: Safely accepts any arguments (*args, **kwargs)
    and allows the server to boot instantly within 1 second.
    """
    return True

def remove_image_background(image_bytes: bytes, *args, **kwargs) -> bytes:
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    # Large images resize for fast performance
    max_dim = 1200
    if max(input_image.size) > max_dim:
        input_image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    
    session = get_session()
    output_image = remove(input_image, session=session)
    
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    return output_buffer.getvalue()

# Compatibility alias
remove_background = remove_image_background