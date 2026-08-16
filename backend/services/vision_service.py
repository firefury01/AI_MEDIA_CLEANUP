import io
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def remove_background(image_bytes: bytes) -> bytes:
    """Instant Zero-Load background remover using OpenCV contour & GrabCut segmentation."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file")

    h, w = img.shape[:2]
    
    # Scale down for ultra-fast instant computation
    max_dim = 600
    scale = 1.0
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img_small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        img_small = img.copy()

    sh, sw = img_small.shape[:2]
    
    # GrabCut Initialization
    mask = np.zeros((sh, sw), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    # Target central subject bounding box
    margin_x = int(sw * 0.05)
    margin_y = int(sh * 0.05)
    rect = (margin_x, margin_y, sw - (2 * margin_x), sh - (2 * margin_y))
    
    cv2.grabCut(img_small, mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)
    
    # Generate binary mask
    bin_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
    
    # Smooth edges
    bin_mask = cv2.GaussianBlur(bin_mask, (5, 5), 0)
    
    # Resize mask back to original resolution
    if scale != 1.0:
        bin_mask = cv2.resize(bin_mask, (w, h), interpolation=cv2.INTER_LINEAR)
        
    b, g, r = cv2.split(img)
    rgba = cv2.merge([b, g, r, bin_mask])
    
    _, buffer = cv2.imencode(".png", rgba)
    return buffer.tobytes()


def upscale_and_enhance(image_bytes: bytes) -> bytes:
    """Instant 2x High-Quality Super Resolution."""
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    new_w = pil_image.width * 2
    new_h = pil_image.height * 2
    
    upscaled = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    enhancer = ImageEnhance.Contrast(sharpened)
    final_image = enhancer.enhance(1.05)
    
    buffer = io.BytesIO()
    final_image.save(buffer, format="JPEG", quality=90, optimize=True)
    return buffer.getvalue()


def clean_document_lighting(image_bytes: bytes) -> bytes:
    """Document Contrast Booster and Shadow Removal."""
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
    """Fast Bilateral Denoising."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    denoised = cv2.bilateralFilter(img, d=7, sigmaColor=50, sigmaSpace=50)
    
    _, buffer = cv2.imencode(".jpg", denoised, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buffer.tobytes()


def compress_to_target_kb(image_bytes: bytes, target_kb: int = 50) -> bytes:
    """Strict Target KB Compression."""
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    target_bytes = target_kb * 1024
    
    quality = 90
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
    
    while buffer.tell() > target_bytes and quality > 15:
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
    """Extract Ink Signature on Transparent PNG."""
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
    """Passport Photo Maker with Clean Background Composite."""
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
    """Compile Multiple Images to PDF."""
    pil_images = []
    for img_data in image_bytes_list:
        if img_data:
            pil_images.append(Image.open(io.BytesIO(img_data)).convert("RGB"))
            
    if not pil_images:
        raise ValueError("No images provided for PDF")
        
    pdf_buffer = io.BytesIO()
    pil_images[0].save(pdf_buffer, format="PDF", save_all=True, append_images=pil_images[1:])
    return pdf_buffer.getvalue()