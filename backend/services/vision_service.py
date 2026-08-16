import io
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Lazy session holder
_rembg_remove = None
_rembg_session = None

def get_rembg_components():
    global _rembg_remove, _rembg_session
    if _rembg_remove is None:
        # Import inside function so server starts instantly without blocking port bind
        from rembg import remove, new_session
        _rembg_remove = remove
        _rembg_session = new_session("u2netp")
    return _rembg_remove, _rembg_session


def remove_background(image_bytes: bytes) -> bytes:
    """Isolate foreground subject with transparent alpha cutout."""
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    orig_w, orig_h = pil_image.size
    max_side = 720
    if max(orig_w, orig_h) > max_side:
        pil_image.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
        
    rem_fn, session = get_rembg_components()
    output_image = rem_fn(pil_image, session=session)
    
    if (orig_w, orig_h) != output_image.size:
        output_image = output_image.resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        
    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def upscale_and_enhance(image_bytes: bytes) -> bytes:
    """2x Super-resolution via Lanczos interpolation + unsharp masking."""
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    new_w = pil_image.width * 2
    new_h = pil_image.height * 2
    
    upscaled = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=3))
    enhancer = ImageEnhance.Contrast(sharpened)
    final_image = enhancer.enhance(1.08)
    
    buffer = io.BytesIO()
    final_image.save(buffer, format="JPEG", quality=92, optimize=True)
    return buffer.getvalue()


def clean_document_lighting(image_bytes: bytes) -> bytes:
    """Even out uneven lighting/shadows and boost document legibility."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
    bg_model = cv2.medianBlur(dilated, 21)
    
    diff = 255 - cv2.absdiff(gray, bg_model)
    norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    cleaned = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8)
    
    _, buffer = cv2.imencode(".jpg", cleaned, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buffer.tobytes()


def denoise_image_fast(image_bytes: bytes) -> bytes:
    """Fast Bilateral filter to remove sensor/grain noise while preserving sharp edges."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    denoised = cv2.bilateralFilter(img, d=7, sigmaColor=50, sigmaSpace=50)
    
    _, buffer = cv2.imencode(".jpg", denoised, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return buffer.tobytes()


def compress_to_target_kb(image_bytes: bytes, target_kb: int = 50) -> bytes:
    """Iteratively compress and scale image to fit strictly under target KB limit."""
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_bytes = target_kb * 1024
    
    quality = 90
    min_quality = 15
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
    
    while buffer.tell() > target_bytes and quality > min_quality:
        quality -= 8
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
        
    while buffer.tell() > target_bytes:
        new_w = int(pil_image.width * 0.85)
        new_h = int(pil_image.height * 0.85)
        if new_w < 50 or new_h < 50:
            break
        pil_image = pil_image.resize((new_w, new_h), Image.Resampling.BILINEAR)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=max(quality, 30), optimize=True)
        
    return buffer.getvalue()


def extract_clean_signature(image_bytes: bytes) -> bytes:
    """Extract handwritten ink signature on a clean transparent PNG."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    cleaned_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    b, g, r = cv2.split(img)
    rgba = cv2.merge([b, g, r, cleaned_mask])
    
    _, buffer = cv2.imencode(".png", rgba)
    return buffer.tobytes()


def generate_passport_photo(image_bytes: bytes, bg_color: str = "white") -> bytes:
    """Crop subject to standard 3.5:4.5 passport aspect ratio with chosen background."""
    cutout_bytes = remove_background(image_bytes)
    foreground = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")
    
    bg_rgb = (255, 255, 255) if bg_color.lower() == "white" else (35, 120, 240)
    background = Image.new("RGBA", foreground.size, (*bg_rgb, 255))
    combined = Image.alpha_composite(background, foreground).convert("RGB")
    
    w, h = combined.size
    target_aspect = 3.5 / 4.5
    current_aspect = w / h
    
    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        combined = combined.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        combined = combined.crop((0, top, w, top + new_h))
        
    passport_final = combined.resize((413, 531), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    passport_final.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def convert_images_to_pdf(image_bytes_list: list[bytes]) -> bytes:
    """Compile multiple images into a clean single PDF file."""
    pil_images = []
    for img_data in image_bytes_list:
        if img_data:
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            pil_images.append(img)
            
    if not pil_images:
        raise ValueError("No valid image data provided.")
        
    pdf_buffer = io.BytesIO()
    first_img = pil_images[0]
    rest_images = pil_images[1:]
    
    first_img.save(pdf_buffer, format="PDF", save_all=True, append_images=rest_images)
    return pdf_buffer.getvalue()