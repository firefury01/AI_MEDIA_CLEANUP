import os
import requests

HF_TOKEN = os.environ.get("HF_TOKEN", "")
API_URL = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"

def remove_background(image_bytes: bytes) -> bytes:
    if not HF_TOKEN:
        raise Exception("HF_TOKEN environment variable is not configured.")
        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error: {response.text}")
        
    return response.content