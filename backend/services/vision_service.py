import io
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
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


# =========================================================
# NEW TOOLS ADDED BELOW
# =========================================================

def compress_to_target_kb(image_bytes: bytes, target_kb: int = 50) -> bytes:
    """Smart Binary Search Compression to hit target KB limit."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        target_bytes = target_kb * 1024
        low, high = 5, 95
        best_output = None

        # Binary search for optimal JPEG quality
        for _ in range(8):
            mid_quality = (low + high) // 2
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=mid_quality, optimize=True)
            size = buffer.tell()

            if size <= target_bytes:
                best_output = buffer.getvalue()
                low = mid_quality + 1
            else:
                high = mid_quality - 1

        # Fallback resize if image dimensions are too large for target KB
        if not best_output or len(best_output) > target_bytes:
            w, h = img.size
            img = img.resize((int(w * 0.7), int(h * 0.7)), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75, optimize=True)
            best_output = buffer.getvalue()

        return best_output
    except Exception as e:
        print(f"[ERROR compress]: {e}")
        raise Exception(f"Compression Failed: {str(e)}")


def extract_signature(image_bytes: bytes) -> bytes:
    """Remove paper background & shadows to get clean transparent signatures."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Adaptive thresholding to isolate ink lines from shadowed paper
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
        )

        # Create smooth alpha channel
        alpha = thresh
        b, g, r = cv2.split(img)
        
        # Ink darkening: make ink clean dark blue/black
        b = np.clip(b.astype(np.int32) - 40, 0, 255).astype(np.uint8)
        g = np.clip(g.astype(np.int32) - 40, 0, 255).astype(np.uint8)
        r = np.clip(r.astype(np.int32) - 40, 0, 255).astype(np.uint8)

        rgba = cv2.merge([b, g, r, alpha])
        _, encoded = cv2.imencode(".png", rgba)
        return encoded.tobytes()
    except Exception as e:
        print(f"[ERROR signature]: {e}")
        raise Exception(f"Signature Extraction Failed: {str(e)}")


def make_passport_photo(image_bytes: bytes, bg_color: str = "white") -> bytes:
    """Crop to 3.5x4.5cm ratio with clean White / Blue background."""
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        h, w, _ = img.shape

        # Passport aspect ratio 3.5 : 4.5 (approx 7:9)
        target_aspect = 7 / 9
        current_aspect = w / h

        if current_aspect > target_aspect:
            # Crop width
            new_w = int(h * target_aspect)
            start_x = (w - new_w) // 2
            cropped = img[:, start_x:start_x + new_w]
        else:
            # Crop height
            new_h = int(w / target_aspect)
            start_y = max(0, (h - new_h) // 4)  # Focus upper half for portrait
            cropped = img[start_y:start_y + new_h, :]

        # Standard passport resolution (413 x 531 px @ 300 DPI)
        resized = cv2.resize(cropped, (413, 531), interpolation=cv2.INTER_LANCZOS4)

        # Background color mapping
        if bg_color.lower() == "blue":
            bg_val = (235, 175, 50) # Light passport blue in BGR
        else:
            bg_val = (255, 255, 255) # Pure white

        # Simple GrabCut mask for portrait segment
        mask = np.zeros(resized.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        rect = (10, 10, resized.shape[1] - 20, resized.shape[0] - 20)
        
        cv2.grabCut(resized, mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        
        foreground = resized * mask2[:, :, np.newaxis]
        background = np.full(resized.shape, bg_val, dtype=np.uint8) * (1 - mask2[:, :, np.newaxis])
        final_passport = cv2.add(foreground, background)

        _, encoded = cv2.imencode(".jpg", final_passport, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        return encoded.tobytes()
    except Exception as e:
        print(f"[ERROR passport]: {e}")
        raise Exception(f"Passport Photo Creation Failed: {str(e)}")