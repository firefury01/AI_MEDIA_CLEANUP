import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
import services.vision_service as vs

app = FastAPI(title="AI Media Cleanup API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}

@app.post("/api/vision/remove-bg")
async def api_remove_bg(file: UploadFile = File(...)):
    data = await file.read()
    res = await run_in_threadpool(vs.remove_background, data)
    return Response(content=res, media_type="image/png")

@app.post("/api/vision/upscale")
async def api_upscale(file: UploadFile = File(...)):
    data = await file.read()
    res = await run_in_threadpool(vs.upscale_and_enhance, data)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/document-clean")
async def api_doc_clean(file: UploadFile = File(...)):
    data = await file.read()
    res = await run_in_threadpool(vs.clean_document_lighting, data)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/denoise")
async def api_denoise(file: UploadFile = File(...)):
    data = await file.read()
    res = await run_in_threadpool(vs.denoise_image_fast, data)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/compress-kb")
async def api_compress_kb(file: UploadFile = File(...), target_kb: int = Form(50)):
    data = await file.read()
    res = await run_in_threadpool(vs.compress_to_target_kb, data, target_kb)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/signature-extract")
async def api_signature_extract(file: UploadFile = File(...)):
    data = await file.read()
    res = await run_in_threadpool(vs.extract_clean_signature, data)
    return Response(content=res, media_type="image/png")

@app.post("/api/vision/passport-maker")
async def api_passport_maker(file: UploadFile = File(...), bg_color: str = Form("white")):
    data = await file.read()
    res = await run_in_threadpool(vs.generate_passport_photo, data, bg_color)
    return Response(content=res, media_type="image/jpeg")

@app.post("/api/vision/image-to-pdf")
async def api_image_to_pdf(files: list[UploadFile] = File(...)):
    raw_list = [await f.read() for f in files]
    res = await run_in_threadpool(vs.convert_images_to_pdf, raw_list)
    return Response(content=res, media_type="application/pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)