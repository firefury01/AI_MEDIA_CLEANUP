import io
from typing import List
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from services.vision_service import (
    remove_background,
    upscale_and_enhance,
    clean_document_lighting,
    denoise_and_restore,
    compress_to_target_kb,
    extract_signature,
    make_passport_photo,
)

app = FastAPI(title="AI Media Cleanup Studio API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check Endpoints (For Render) ---

@app.get("/")
@app.head("/")
def root():
    return {"status": "healthy", "service": "AI Vision Studio Backend"}


@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "ok"}


# --- Vision Tool Endpoints ---

@app.post("/api/vision/remove-bg")
async def api_remove_bg(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = remove_background(content)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/upscale")
async def api_upscale(file: UploadFile = File(...), scale: int = Form(2)):
    try:
        content = await file.read()
        result = upscale_and_enhance(content, scale_factor=scale)
        return Response(content=result, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/document-clean")
async def api_document_clean(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = clean_document_lighting(content)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/denoise")
async def api_denoise(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = denoise_and_restore(content)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/image-to-pdf")
async def api_image_to_pdf(files: List[UploadFile] = File(...)):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        pil_images = []
        for upload_file in files:
            data = await upload_file.read()
            img = Image.open(io.BytesIO(data))
            if img.mode != "RGB":
                img = img.convert("RGB")
            pil_images.append(img)

        pdf_bytes_io = io.BytesIO()
        first_image = pil_images[0]
        rest_images = pil_images[1:] if len(pil_images) > 1 else []

        first_image.save(
            pdf_bytes_io,
            format="PDF",
            save_all=True,
            append_images=rest_images,
            resolution=100.0,
        )

        return Response(content=pdf_bytes_io.getvalue(), media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- New Added Tools ---

@app.post("/api/vision/compress-kb")
async def api_compress_kb(file: UploadFile = File(...), target_kb: int = Form(50)):
    try:
        content = await file.read()
        result = compress_to_target_kb(content, target_kb=target_kb)
        return Response(content=result, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/signature-extract")
async def api_signature_extract(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = extract_signature(content)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/passport-maker")
async def api_passport_maker(file: UploadFile = File(...), bg_color: str = Form("white")):
    try:
        content = await file.read()
        result = make_passport_photo(content, bg_color=bg_color)
        return Response(content=result, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))