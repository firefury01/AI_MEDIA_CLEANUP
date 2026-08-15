
import contextlib
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool

from services.audio_service import clean_audio_stream
from services.vision_service import init_vision_model, remove_image_background

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload the lightweight, fast U2-Net model on startup
    init_vision_model("u2netp")
    yield

app = FastAPI(title="AI Media Cleanup API", lifespan=lifespan)

# Allow Cross-Origin Requests from Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "online", "version": "1.0.0"}

@app.post("/api/clean-audio")
async def clean_audio_endpoint(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty file received.")
        
        result_bytes = await run_in_threadpool(clean_audio_stream, audio_bytes)
        return Response(content=result_bytes, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@app.post("/api/remove-bg")
async def remove_bg_endpoint(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty file received.")

        result_bytes = await run_in_threadpool(remove_image_background, image_bytes)
        return Response(content=result_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background removal failed: {str(e)}")