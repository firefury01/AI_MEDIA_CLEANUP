import io
import soundfile as sf
import noisereduce as nr
import numpy as np

def clean_audio_stream(audio_bytes: bytes) -> bytes:
    """
    Reads incoming audio bytes in-memory, converts multichannel to mono,
    executes multi-core stationary noise reduction, and outputs WAV bytes.
    """
    data, sample_rate = sf.read(io.BytesIO(audio_bytes))

    if len(data.shape) > 1 and data.shape[1] > 1:
        data = np.mean(data, axis=1)

    cleaned = nr.reduce_noise(
        y=data,
        sr=sample_rate,
        stationary=True,
        prop_decrease=0.85,
        n_fft=1024,
        n_jobs=-1
    )

    out_buffer = io.BytesIO()
    sf.write(out_buffer, cleaned, sample_rate, format="WAV")
    return out_buffer.getvalue()