import os

# ----------------------------
# VIDEO
# ----------------------------
# queue + func name
SERVICE_VIDEO_COMPRESS_QUEUE = "service_video_compress_queue"
SERVICE_VIDEO_COMPRESS = "service_video_compress"

SERVICE_VIDEO_POSES_QUEUE = "service_video_poses_queue"
SERVICE_VIDEO_POSES = "service_video_poses"

# ----------------------------
# AUDIO
# ----------------------------
SERVICE_AUDIO_EXTRACT_QUEUE = "service_audio_extract_queue"
SERVICE_AUDIO_EXTRACT = "service_audio_extract"

SERVICE_AUDIO_TRANSCRIBE_QUEUE = "service_audio_transcribe_queue"
SERVICE_AUDIO_TRANSCRIBE = "service_audio_transcribe"

SERVICE_AUDIO_EMOTIONS_QUEUE = "service_audio_emotions_queue"
SERVICE_AUDIO_EMOTIONS = "service_audio_emotions"

# ----------------------------
# COMMON
# ----------------------------
SERVICE_COMMON_REPORT_QUEUE = "service_common_report_queue"
SERVICE_COMMON_REPORT = "service_common_report"

# ----------------------------
# DATABASE & HOSTS
# ----------------------------
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASS')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')

BOT_TOKEN = os.environ.get("BOT_TOKEN")

AUDIO_HOST = os.environ.get('AUDIO_HOST', "service_audio")
AUDIO_PORT = os.environ.get('AUDIO_PORT', "8001")

AUDIO_URL = f"http://app_audio-1:{AUDIO_PORT}/"

CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "rpc://")
CELERY_BROKER_URL = (
    os.environ.get("CELERY_BROKER_URL", "pyamqp://guest:guest@localhost:5672/"),
)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", '/temp/uploads')
COMPRESSED_FOLDER = os.environ.get("COMPRESSED_FOLDER", '/temp/videos')
EXTRACTED_AUDIO = os.environ.get("EXTRACTED_AUDIO", '/temp/audios')
