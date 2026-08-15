import io
import soundfile as sf
import noisereduce as nr
import numpy as np

def denoise_audio(audio_bytes: bytes) -> bytes:
    data, rate = sf.read(io.BytesIO(audio_bytes))
    
    # Convert stereo to mono if needed for faster processing
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    
    # Fast stationary noise reduction
    reduced_noise = nr.reduce_noise(
        y=data, 
        sr=rate, 
        stationary=True, 
        prop_decrease=0.85,
        n_fft=1024,
        hop_length=512
    )
    
    out_io = io.BytesIO()
    sf.write(out_io, reduced_noise, rate, format='WAV', subtype='PCM_16')
    return out_io.getvalue()