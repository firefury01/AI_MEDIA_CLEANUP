import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

# Services import
from services.vision_service import remove_background
from services.audio_service import denoise_audio

app = FastAPI(title="AI Media Cleanup")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Media Cleanup API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Vision endpoint matching frontend call exactly
@app.post("/api/vision/remove-bg")
async def vision_remove_bg(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        output_bytes = remove_background(contents)
        return Response(content=output_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Audio endpoint matching frontend call exactly
@app.post("/api/audio/clean")
async def audio_clean(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        output_bytes = denoise_audio(contents)
        return Response(content=output_bytes, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)