import io
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rembg import remove, new_session

# Global session variable for lazy loading
BG_SESSION = None

def get_bg_session():
    """Lazily instantiate the U2NetP model only on first API call."""
    global BG_SESSION
    if BG_SESSION is None:
        sess_opts = ort.SessionOptions()
        sess_opts.intra_op_num_threads = 2
        sess_opts.inter_op_num_threads = 2
        try:
            BG_SESSION = new_session("u2netp", session_options=sess_opts)
        except Exception:
            BG_SESSION = new_session("u2netp")
    return BG_SESSION


def remove_background(image_bytes: bytes) -> bytes:
    """Instant background removal capped to 800px for speed."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img.thumbnail((800, 800), Image.Resampling.BILINEAR)

        session = get_bg_session()
        output = remove(img, session=session, alpha_matting=False)

        out_io = io.BytesIO()
        output.save(out_io, format="PNG", optimize=False)
        return out_io.getvalue()
    except Exception as e:
        print(f"[ERROR remove-bg]: {e}")
        raise Exception(f"Background Removal Failed: {str(e)}")


def upscale_image_fast(image_bytes: bytes, scale_factor: float = 2.0) -> bytes:
    """2x super-resolution with Lanczos resampling and subtle unsharp edge masking."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        max_dim = 1600
        if max(img.size) * scale_factor > max_dim:
            scale_factor = max_dim / max(img.size)

        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        upscaled = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        enhanced = upscaled.filter(
            ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2)
        )

        out_io = io.BytesIO()
        enhanced.save(out_io, format="JPEG", quality=90, optimize=True)
        return out_io.getvalue()
    except Exception as e:
        print(f"[ERROR upscale]: {e}")
        raise Exception(f"Upscaling Failed: {str(e)}")

# Alias to resolve import name mismatch in main.py
upscale_and_enhance = upscale_image_fast


def clean_document_lighting(image_bytes: bytes) -> bytes:
    """Wipes shadows, evens illumination across paper, and boosts high-contrast text."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
        bg_blur = cv2.medianBlur(dilated, 21)

        diff = 255 - cv2.absdiff(gray, bg_blur)
        norm = cv2.normalize(
            diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U
        )

        _, thresh = cv2.threshold(
            norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        success, encoded = cv2.imencode(
            ".jpg", thresh, [int(cv2.IMWRITE_JPEG_QUALITY), 92]
        )
        if not success:
            raise Exception("Failed to encode document output")
        return encoded.tobytes()
    except Exception as e:
        print(f"[ERROR doc-clean]: {e}")
        raise Exception(f"Document Cleaning Failed: {str(e)}")


def denoise_image_fast(image_bytes: bytes) -> bytes:
    """Fast bilateral filter to clear grain while preserving crisp edge boundaries."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        denoised = cv2.bilateralFilter(img, d=7, sigmaColor=50, sigmaSpace=50)

        success, encoded = cv2.imencode(
            ".jpg", denoised, [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        )
        if not success:
            raise Exception("Failed to encode denoised image")
        return encoded.tobytes()
    except Exception as e:
        print(f"[ERROR denoise]: {e}")
        raise Exception(f"Denoise Failed: {str(e)}")


def compress_to_target_kb(image_bytes: bytes, target_kb: int = 50) -> bytes:
    """Binary search loop compression targeting exact portal limits (20KB, 50KB, 100KB)."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        target_bytes = target_kb * 1024

        min_quality = 10
        max_quality = 95
        best_output = None

        for _ in range(8):
            mid_quality = (min_quality + max_quality) // 2
            out_io = io.BytesIO()
            img.save(out_io, format="JPEG", quality=mid_quality, optimize=True)
            current_bytes = out_io.getvalue()

            if len(current_bytes) <= target_bytes:
                best_output = current_bytes
                min_quality = mid_quality + 1
            else:
                max_quality = mid_quality - 1

        if best_output is None or len(best_output) > target_bytes:
            w, h = img.size
            for scale in [0.75, 0.5, 0.35]:
                resized = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
                out_io = io.BytesIO()
                resized.save(out_io, format="JPEG", quality=60, optimize=True)
                if len(out_io.getvalue()) <= target_bytes:
                    return out_io.getvalue()
            return out_io.getvalue()

        return best_output
    except Exception as e:
        print(f"[ERROR compress-kb]: {e}")
        raise Exception(f"Compression Failed: {str(e)}")


def extract_clean_signature(image_bytes: bytes) -> bytes:
    """Removes paper backgrounds to leave dark transparent ink."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 10
        )

        b, g, r = cv2.split(img)
        alpha = thresh
        rgba = cv2.merge([b, g, r, alpha])

        success, encoded = cv2.imencode(".png", rgba)
        if not success:
            raise Exception("Failed to encode transparent signature")
        return encoded.tobytes()
    except Exception as e:
        print(f"[ERROR signature-extract]: {e}")
        raise Exception(f"Signature Extraction Failed: {str(e)}")


def generate_passport_photo(image_bytes: bytes, bg_color: str = "white") -> bytes:
    """Isolates person and mounts over white/blue 3.5x4.5cm passport backdrop."""
    try:
        cutout_bytes = remove_background(image_bytes)
        cutout_img = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

        canvas_w, canvas_h = 350, 450
        fill_rgb = (255, 255, 255) if bg_color.lower() == "white" else (30, 80, 180)

        canvas = Image.new("RGB", (canvas_w, canvas_h), fill_rgb)
        cutout_img.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        offset_x = (canvas_w - cutout_img.width) // 2
        offset_y = canvas_h - cutout_img.height

        canvas.paste(cutout_img, (offset_x, offset_y), mask=cutout_img.split()[3])

        out_io = io.BytesIO()
        canvas.save(out_io, format="JPEG", quality=95)
        return out_io.getvalue()
    except Exception as e:
        print(f"[ERROR passport-maker]: {e}")
        raise Exception(f"Passport Photo Creation Failed: {str(e)}")


def convert_images_to_pdf(images_bytes_list: list[bytes]) -> bytes:
    """Compiles uploaded images into a clean single PDF file."""
    try:
        pil_images = []
        for img_b in images_bytes_list:
            im = Image.open(io.BytesIO(img_b)).convert("RGB")
            pil_images.append(im)

        if not pil_images:
            raise Exception("No valid images supplied for PDF conversion.")

        out_io = io.BytesIO()
        pil_images[0].save(
            out_io,
            format="PDF",
            save_all=True,
            append_images=pil_images[1:],
            resolution=100.0,
        )
        return out_io.getvalue()
    except Exception as e:
        print(f"[ERROR image-to-pdf]: {e}")
        raise Exception(f"PDF Compilation Failed: {str(e)}")