import logging
import os
import subprocess

from celery import Celery
from celery.exceptions import MaxRetriesExceededError

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, EXTRACTED_AUDIO, \
    SERVICE_AUDIO_EXTRACT, SERVICE_AUDIO_EXTRACT_QUEUE

celery_worker = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_worker.conf.task_routes = {f"worker.*": {"queue": SERVICE_AUDIO_EXTRACT_QUEUE}, }

# Set up logging
logging.basicConfig(level=logging.INFO)


@celery_worker.task(name=f"worker.{SERVICE_AUDIO_EXTRACT}")
def service_audio_extract(video_name: str, input_file: str) -> dict[str, str]:
    try:
        # Create output directory if it doesn't exist.
        base_name = os.path.basename(input_file).split('.')[0]
        audio_path = os.path.join(EXTRACTED_AUDIO, f"{base_name}.wav")

        # command
        ffmpeg_command = ["ffmpeg", "-i", input_file,
                          "-ac", "1", "-ar", "16000",
                          "-vn", audio_path]

        subprocess.run(ffmpeg_command, check=True)

    except subprocess.CalledProcessError as ex:
        logging.error(f"Failed extracting audio: {ex}")

        try:
            service_audio_extract.retry(countdown=2)
            return {'status': 'RETRYING'}

        except MaxRetriesExceededError as ex:
            logging.error(f"Max retries exceeded: {ex}")
            return {'status': 'FAIL', 'result': 'max retries achieved'}

    else:
        return {'status': 'SUCCESS', 'result': audio_path}
