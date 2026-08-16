import io
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove, new_session

# Configure ONNX Runtime to use all available CPU cores
sess_opts = ort.SessionOptions()
sess_opts.intra_op_num_threads = 4
sess_opts.inter_op_num_threads = 4

# Initialize session once globally
try:
    BG_SESSION = new_session("u2netp", session_options=sess_opts)
except Exception:
    BG_SESSION = new_session("u2netp")


def remove_background(image_bytes: bytes) -> bytes:
    """Instant background removal capped to 800px for speed."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        # Aggressive dimension cap (800px max) for ultra-fast processing
        img.thumbnail((800, 800), Image.Resampling.BILINEAR)

        # Direct processing without alpha matting loops
        output = remove(img, session=BG_SESSION, alpha_matting=False)

        out_io = io.BytesIO()
        output.save(out_io, format="PNG", optimize=False)
        return out_io.getvalue()
    except Exception as e:
        print(f"[ERROR remove-bg]: {e}")
        raise Exception(f"Background Removal Failed: {str(e)}")


def upscale_and_enhance(image_bytes: bytes, scale_factor: int = 2) -> bytes:
    """Fast Lanczos 2x super-resolution."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((1000, 1000), Image.Resampling.BILINEAR)

        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        upscaled = img.resize(new_size, Image.Resampling.BILINEAR)

        # Quick Unsharp Mask
        sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        
        out_io = io.BytesIO()
        sharpened.save(out_io, format="JPEG", quality=90)
        return out_io.getvalue()
    except Exception as e:
        print(f"[ERROR upscale]: {e}")
        raise Exception(f"Upscale Failed: {str(e)}")


def clean_document_lighting(image_bytes: bytes) -> bytes:
    """Sub-second shadow subtraction."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Downscale for instant calculation
        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Fast median background estimation
        bg = cv2.medianBlur(l, 21)
        diff = cv2.absdiff(l, bg)
        norm_l = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        res_l = clahe.apply(norm_l)

        res_lab = cv2.merge([res_l, a, b])
        result = cv2.cvtColor(res_lab, cv2.COLOR_LAB2BGR)

        _, buffer = cv2.imencode(".png", result)
        return buffer.tobytes()
    except Exception as e:
        print(f"[ERROR doc-clean]: {e}")
        raise Exception(f"Doc Enhancer Failed: {str(e)}")


def denoise_and_restore(image_bytes: bytes) -> bytes:
    """Ultra-fast edge-preserving blur (< 0.2s)."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

        denoised = cv2.bilateralFilter(img, d=5, sigmaColor=35, sigmaSpace=35)

        _, buffer = cv2.imencode(".png", denoised)
        return buffer.tobytes()
    except Exception as e:
        print(f"[ERROR denoise]: {e}")
        raise Exception(f"Denoise Failed: {str(e)}")