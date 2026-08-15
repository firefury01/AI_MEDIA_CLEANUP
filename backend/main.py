import os
import requests
import io
from PIL import Image

HF_TOKEN = os.environ.get("HF_TOKEN", "")
API_URL = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"

def remove_background(image_bytes: bytes) -> bytes:
    if not HF_TOKEN:
        raise Exception("HF_TOKEN is not set in Render environment variables.")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    # Hugging Face inference call
    response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=45)

    if response.status_code != 200:
        # Detailed error log for Render logs
        print(f"HF Error Status: {response.status_code}, Body: {response.text}")
        raise Exception(f"Hugging Face API failed ({response.status_code}): {response.text}")

    # Ensure output is a valid PNG
    try:
        result_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        out_io = io.BytesIO()
        result_img.save(out_io, format="PNG")
        return out_io.getvalue()
    except Exception as img_err:
        print(f"Image parse error: {img_err}, Response was: {response.content[:200]}")
        return response.content