import os

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASS')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')

BOT_TOKEN = os.environ.get("BOT_TOKEN")

AUDIO_HOST = os.environ.get('AUDIO_HOST', "service_audio")
AUDIO_PORT = os.environ.get('AUDIO_PORT', "8001")

AUDIO_URL = f"http://app_audio-1:{AUDIO_PORT}/"

BROKER_URI = 'redis://redis:6379'

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", '/temp/uploads')
COMPRESSED_FOLDER = os.environ.get("COMPRESSED_FOLDER", '/temp/_videos')
EXTRACTED_AUDIO = os.environ.get("EXTRACTED_AUDIO", '/temp/_audios')