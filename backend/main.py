import io
from typing import List
import cv2
import numpy as np
from PIL import Image, ImageFilter
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI(title="AI Media Cleanup Studio Backend")

# Enable CORS for all incoming frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is online and ready"}

# 1. Background Remover Endpoint
@app.post("/api/vision/remove-bg")
def remove_bg_endpoint(file: UploadFile = File(...)):
    print(f"\n[START] remove-bg: {file.filename}")
    try:
        contents = file.file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image")

        h, w = img.shape[:2]
        max_dim = 500
        scale = min(max_dim / max(h, w), 1.0)
        proc_w, proc_h = int(w * scale), int(h * scale)
        small_img = cv2.resize(img, (proc_w, proc_h), interpolation=cv2.INTER_AREA)

        mask = np.zeros((proc_h, proc_w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        rect = (int(proc_w * 0.04), int(proc_h * 0.04), int(proc_w * 0.92), int(proc_h * 0.92))

        cv2.grabCut(small_img, mask, rect, bgd_model, fgd_model, 2, cv2.GC_INIT_WITH_RECT)
        final_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")
        final_mask = cv2.resize(final_mask, (w, h), interpolation=cv2.INTER_LINEAR)
        alpha = (final_mask * 255).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (5, 5), 0)

        b, g, r = cv2.split(img)
        rgba = cv2.merge([b, g, r, alpha])

        _, buffer = cv2.imencode(".png", rgba)
        print("[FINISH] remove-bg success")
        return Response(content=buffer.tobytes(), media_type="image/png")
    except Exception as e:
        print(f"[ERROR remove-bg]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. Super-Resolution / 2x AI Upscaler Endpoint
@app.post("/api/vision/upscale")
def upscale_endpoint(file: UploadFile = File(...)):
    print(f"\n[START] upscale: {file.filename}")
    try:
        contents = file.file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        new_size = (int(img.width * 2), int(img.height * 2))
        upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
        sharpened = upscaled.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=3))

        out_io = io.BytesIO()
        sharpened.save(out_io, format="PNG")
        print("[FINISH] upscale success")
        return Response(content=out_io.getvalue(), media_type="image/png")
    except Exception as e:
        print(f"[ERROR upscale]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. Document Lighting & Shadow Enhancer Endpoint
@app.post("/api/vision/document-clean")
def doc_clean_endpoint(file: UploadFile = File(...)):
    print(f"\n[START] doc-clean: {file.filename}")
    try:
        contents = file.file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        bg = cv2.medianBlur(l, 21)
        diff = cv2.absdiff(l, bg)
        norm_l = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        res_l = clahe.apply(norm_l)

        res_lab = cv2.merge([res_l, a, b])
        result = cv2.cvtColor(res_lab, cv2.COLOR_LAB2BGR)

        _, buffer = cv2.imencode(".png", result)
        print("[FINISH] doc-clean success")
        return Response(content=buffer.tobytes(), media_type="image/png")
    except Exception as e:
        print(f"[ERROR doc-clean]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. Image Denoise Studio Endpoint
@app.post("/api/vision/denoise")
def denoise_endpoint(file: UploadFile = File(...)):
    print(f"\n[START] denoise: {file.filename}")
    try:
        contents = file.file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        denoised = cv2.bilateralFilter(img, d=7, sigmaColor=40, sigmaSpace=40)

        _, buffer = cv2.imencode(".png", denoised)
        print("[FINISH] denoise success")
        return Response(content=buffer.tobytes(), media_type="image/png")
    except Exception as e:
        print(f"[ERROR denoise]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. Image to PDF Converter Endpoint
@app.post("/api/vision/image-to-pdf")
def image_to_pdf_endpoint(files: List[UploadFile] = File(...)):
    print(f"\n[START] image-to-pdf: {len(files)} files received")
    try:
        pil_images = []
        for file in files:
            contents = file.file.read()
            img = Image.open(io.BytesIO(contents)).convert("RGB")
            pil_images.append(img)

        if not pil_images:
            raise ValueError("No valid images provided")

        pdf_bytes_io = io.BytesIO()
        first_image = pil_images[0]
        rest_images = pil_images[1:]

        first_image.save(
            pdf_bytes_io,
            format="PDF",
            save_all=True,
            append_images=rest_images,
            resolution=100.0,
        )

        print("[FINISH] image-to-pdf success")
        return Response(
            content=pdf_bytes_io.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=converted_document.pdf"}
        )
    except Exception as e:
        print(f"[ERROR image-to-pdf]: {e}")
        raise HTTPException(status_code=500, detail=str(e))