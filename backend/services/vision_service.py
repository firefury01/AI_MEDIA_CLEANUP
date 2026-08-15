import os
import io
import requests
from PIL import Image

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://router.huggingface.co/hf-inference/models/briaai/RMBG-1.4"

def remove_background(image_bytes: bytes) -> bytes:
    if not HF_TOKEN:
        raise Exception("HF_TOKEN environment variable is missing on Render.")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/octet-stream"
    }

    try:
        response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=45)
        
        if response.status_code != 200:
            legacy_url = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
            response = requests.post(legacy_url, headers=headers, data=image_bytes, timeout=45)

        if response.status_code != 200:
            raise Exception(f"AI API Error ({response.status_code}): {response.text}")

        image = Image.open(io.BytesIO(response.content)).convert("RGBA")
        out_io = io.BytesIO()
        image.save(out_io, format="PNG")
        return out_io.getvalue()

    except Exception as e:
        raise Exception(f"Vision Processing Error: {str(e)}")