import gc
import logging

import torch
import whisperx
from celery import Celery
from celery.exceptions import MaxRetriesExceededError

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, \
    SERVICE_AUDIO_TRANSCRIBE, SERVICE_AUDIO_TRANSCRIBE_QUEUE

celery_worker = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_worker.conf.task_routes = {f"worker.*": {"queue": SERVICE_AUDIO_TRANSCRIBE_QUEUE}, }

# Set up logging
logging.basicConfig(level=logging.INFO)

torch.set_num_threads(1)

device = "cuda" if torch.cuda.is_available() else "cpu"

@celery_worker.task(name=f"worker.{SERVICE_AUDIO_TRANSCRIBE}", bind=True)
def transcribe_and_analyze(self, audio_path, model_size: str = "small", batch_size: int = 16,
                           compute_type: str = "int8"):
    """
    Transcribes audio, aligns text with audio, and calculates speech speed in words per minute.

    :param audio_path: Path to the audio file (or a dict with key "result") to transcribe.
    :param model_size: Size of the WhisperX model to load (e.g., "small", "medium").
    :param batch_size: Batch size for transcription.
    :param compute_type: Compute precision type for the model (e.g., "int8").
    :return: A dictionary with keys 'status' and 'result'. The result contains:
             - file_path: Path to the audio file.
             - speech_speed: Calculated words per minute.
             - transcript: Transcript text.
             - full_result: Full transcription result.
             - aligned_result: Alignment result.
    """
    try:
        # If the input is a dict, extract the file path; otherwise use the provided path.
        if isinstance(audio_path, dict):
            audio_file = audio_path.get("result")
        else:
            audio_file = audio_path

        # Load WhisperX model and transcribe audio.
        model = whisperx.load_model(model_size, device, compute_type=compute_type)
        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size)

        # Free GPU memory from the transcription model.
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
        del model

        # Load alignment model and align text with audio.
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        aligned_result = whisperx.align(
            result["segments"], model_a, metadata, audio, device, return_char_alignments=False
        )

        # Calculate speech speed in words per minute.
        total_words = sum(len(segment["words"]) for segment in aligned_result["segments"])
        first_word_start_time = aligned_result["segments"][0]["start"]
        last_word_end_time = aligned_result["segments"][-1]["end"]
        duration_minutes = (last_word_end_time - first_word_start_time) / 60
        words_per_minute = total_words / duration_minutes

        # Prepare the final result.
        analysis_result = {
            "file_path": audio_file,
            "speech_speed": round(words_per_minute, 2),
            "transcript": result["segments"][0]["text"],
            "full_result": result,
            "aligned_result": aligned_result
        }
        return {"status": "SUCCESS", "result": analysis_result}

    except Exception as e:
        import logging
        logging.error(f"Error in transcribe_and_analyze: {e}")
        try:
            self.retry(countdown=2)
        except MaxRetriesExceededError as retry_ex:
            logging.error(f"Max retries exceeded in transcribe_and_analyze: {retry_ex}")
            return {"status": "FAIL", "result": "N/A", "error": str(e)}

    finally:
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
