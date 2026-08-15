import io
from PIL import Image
from rembg import remove, new_session

# Preload session object placeholder
session_instance = None

def init_vision_model(model_name: str = "u2netp"):
    """Loads weights into memory at server startup."""
    global session_instance
    print(f"Loading {model_name} model weights into memory...")
    session_instance = new_session(model_name)
    print("Vision model loaded successfully!")

def remove_image_background(image_bytes: bytes) -> bytes:
    """
    Resizes oversized images (Lanczos) and executes neural network
    segmentation to produce a transparent RGBA PNG.
    """
    global session_instance
    if session_instance is None:
        init_vision_model("u2netp")

    input_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # Downscale if resolution exceeds 1200px (prevents compute bottlenecks)
    max_dim = 1200
    if max(input_img.size) > max_dim:
        input_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Run inference with pre-loaded session
    output_img = remove(input_img, session=session_instance)

    out_buffer = io.BytesIO()
    output_img.save(out_buffer, format="PNG", optimize=True)
    return out_buffer.getvalue()
