import logging
import os
import shutil

from domain.contracts import UserCreate, VideoCreate
from fastapi import UploadFile
from init_data_py import InitData
from sqlalchemy.orm import Session
from storage.db_query import get_or_create_user, create_video

from config import BOT_TOKEN
from config import UPLOAD_FOLDER


def validate_init_data(init_string: str) -> InitData:
    """
    Parses and validates the init_string using InitData.
    """
    try:
        init_data = InitData.parse(init_string)
        if not init_data.validate(BOT_TOKEN):
            logging.info("Init-data is not valid.")
            raise ValueError("Init-data is not valid.")
        return init_data
    except Exception as ex:
        logging.exception("Failed to validate init data.")
        raise ValueError(f"Invalid init data: {str(ex)}")


def get_or_create_user_record(db: Session, init_data: InitData):
    """
    Extracts user data from InitData and retrieves or creates the user record.
    """
    user_data = UserCreate(id=init_data.user.id, first_name=init_data.user.first_name,
        last_name=init_data.user.last_name, username=init_data.user.username, )
    return get_or_create_user(db, user_data)


def save_video_file(file: UploadFile, generated_name : str, db: Session, init_data: InitData) -> str:
    """
    Validates and saves the uploaded video file to the temp directory.
    """
    # Validate file extension
    allowed_extensions = (".mp4", ".avi", ".mov", ".mkv")
    if not file.filename.lower().endswith(allowed_extensions):
        raise ValueError("Invalid file format. Allowed formats: mp4, avi, mov, mkv.")

    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_FOLDER, f"{generated_name}{ext}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    create_video(
        db,
        VideoCreate(
            original_name=file.filename,
            generated_name=f"{generated_name}{ext}",
            file_path=file_path,  # pass file_path here
            status="in_process",
            analysis="",
            user_id=init_data.user.id
        )
    )

    return file_path