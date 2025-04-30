import gc
import logging
import os

import librosa
import numpy as np
import soundfile as sf
import torch
from aniemore.models import HuggingFaceModel
from aniemore.recognizers.voice import VoiceRecognizer
from celery import Celery

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, \
    SERVICE_AUDIO_EMOTIONS_QUEUE, SERVICE_AUDIO_EMOTIONS

celery_worker = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_worker.conf.task_routes = {f"worker.*": {"queue": SERVICE_AUDIO_EMOTIONS_QUEUE}, }

# Set up logging
logging.basicConfig(level=logging.INFO)

torch.set_num_threads(1)

model = HuggingFaceModel.Voice.WavLM  # assuming this is your model instance
device = "cuda" if torch.cuda.is_available() else "cpu"
vr = VoiceRecognizer(model=model, device=device)


@celery_worker.task(name=f"worker.{SERVICE_AUDIO_EMOTIONS}")
def service_audio_emotions(input_info, segment_duration: float = 1.5) -> dict:
    """
    Analyzes the emotions present in an audio file and calculates their percentage.

    :param input_info: Path to the input audio file (or a dict with key "file_path").
    :param segment_duration: Duration of audio segments in seconds for emotion analysis.
    :return: A dictionary with a status and a result string containing emotion percentages.
    """
    try:
        speech_speed = "N/A"

        # If the input is a dict, extract the file path
        if isinstance(input_info, dict):
            audio_file_path = input_info.get("result").get("file_path", "")
            speech_speed = input_info.get("result").get("speech_speed", "N/A")
        else:
            audio_file_path = input_info

        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Load the audio file
        audio, sr = librosa.load(audio_file_path, sr=None)
        duration = librosa.get_duration(y=audio, sr=sr)

        # Initialize emotion counters
        emotions_count = {}
        total_segments = int(np.ceil(duration / segment_duration))

        # Process audio in segments
        for segment in range(total_segments):
            start_time = segment * segment_duration
            end_time = min((segment + 1) * segment_duration, duration)
            segment_audio = audio[int(start_time * sr):int(end_time * sr)]

            # Save segment as a temporary file
            temp_segment_path = "/temp/utils/temp_segment.wav"
            os.makedirs(os.path.dirname(temp_segment_path), exist_ok=True)
            sf.write(temp_segment_path, segment_audio, sr)

            # Recognize emotion for the segment
            emotion = vr.recognize(temp_segment_path, return_single_label=True)

            # Count emotions
            emotions_count[emotion] = emotions_count.get(emotion, 0) + 1

        # Calculate emotion percentages
        total_emotions = sum(emotions_count.values())
        emotion_percentages = {
            emotion: (count / total_emotions) * 100
            for emotion, count in emotions_count.items()
        }

        # Define the order of emotions and build a result string
        emotion_order = ["anger", "happiness", "enthusiasm", "disgust", "neutral", "fear", "sadness"]
        result = ""
        for emotion in emotion_order:
            result += f"{emotion}: {emotion_percentages.get(emotion, 0):.2f} "

        return {'status': 'SUCCESS', 'speaker_mood': result, 'speech_speed' : speech_speed}

    except Exception as ex:
        import logging
        logging.error(f"Failed processing audio emotions: {ex}")
        try:
            service_audio_emotions.retry(countdown=2)
        except Exception as retry_ex:
            logging.error(f"Max retries exceeded in service_audio_emotions: {retry_ex}")
            return {'status': 'FAIL', 'result': 'N/A', "speech_speed" : speech_speed}
    finally:
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
