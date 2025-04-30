import logging
import os
import subprocess

from celery import Celery
from celery.exceptions import MaxRetriesExceededError

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SERVICE_VIDEO_COMPRESS_QUEUE, \
    COMPRESSED_FOLDER, SERVICE_VIDEO_COMPRESS

celery_worker = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_worker.conf.task_routes = {f"worker.*": {"queue": SERVICE_VIDEO_COMPRESS_QUEUE}, }

# Set up logging
logging.basicConfig(level=logging.INFO)


@celery_worker.task(name=f"worker.{SERVICE_VIDEO_COMPRESS}")
def service_video_compress(video_name, input_video_path):
    """
    Compresses a video and sends the result (compressed file path) to Redis.
    """
    try:
        # Ensure output directory exists
        os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
        ext = os.path.splitext(input_video_path)[-1]
        compressed_video_path = os.path.join(COMPRESSED_FOLDER, f"{video_name}{ext}")

        # Command for compressing video
        command = ["ffmpeg", "-i", input_video_path, "-vcodec", "libx264", "-crf", "28",  # Compression quality
                   compressed_video_path]
        subprocess.run(command, check=True)

    except subprocess.CalledProcessError as ex:
        logging.error(f"Failed extracting audio: {ex}")

        try:
            service_video_compress.retry(countdown=2)
            return {'status': 'RETRYING'}

        except MaxRetriesExceededError as ex:
            logging.error(f"Max retries exceeded: {ex}")
            return {'status': 'FAIL', 'result': 'max retries achieved'}

    else:
        return {'status': 'SUCCESS', 'result': compressed_video_path}
