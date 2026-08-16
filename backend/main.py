from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
import uvicorn

from services.vision_service import (
    remove_background,
    upscale_and_enhance,
    clean_document_lighting,
    denoise_image_fast,
    compress_to_target_kb,
    extract_clean_signature,
    generate_passport_photo,
    convert_images_to_pdf,
)

app = FastAPI(title="AI Media Cleanup Studio Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/vision/remove-bg")
async def api_remove_bg(file: UploadFile = File(...)):
    data = await file.read()
    res = remove_background(data)
    return Response(content=res, media_type="image/png")

@app.post("/api/vision/upscale")
async def api_upscale(file: UploadFile = File(...)):
    data = await file.read()
    res = upscale_and_enhance(data)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/document-clean")
async def api_doc_clean(file: UploadFile = File(...)):
    data = await file.read()
    res = clean_document_lighting(data)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/denoise")
async def api_denoise(file: UploadFile = File(...)):
    data = await file.read()
    res = denoise_image_fast(data)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/compress-kb")
async def api_compress_kb(file: UploadFile = File(...), target_kb: int = Form(50)):
    data = await file.read()
    res = compress_to_target_kb(data, target_kb)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/signature-extract")
async def api_signature_extract(file: UploadFile = File(...)):
    data = await file.read()
    res = extract_clean_signature(data)
    return Response(content=res, media_type="image/png")

@app.post("/api/vision/passport-maker")
async def api_passport_maker(file: UploadFile = File(...), bg_color: str = Form("white")):
    data = await file.read()
    res = generate_passport_photo(data, bg_color)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/image-to-pdf")
async def api_image_to_pdf(files: list[UploadFile] = File(...)):
    raw_list = [await f.read() for f in files]
    res = convert_images_to_pdf(raw_list)
    return Response(content=res, media_type="application/pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")