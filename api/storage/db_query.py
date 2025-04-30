from typing import Optional, List

from domain.contracts import UserCreate, VideoCreate, AudioTaskCreate, CompressTaskCreate, AnalysisCreate
from sqlalchemy.orm import Session
from storage.db_models import User, Video, AudioTask, CompressTask, Analysis


# CRUD Operations for User

def get_or_create_user(db: Session, user_data: UserCreate) -> tuple[bool, User]:
    """
    Get an existing user or create a new one.
    Returns a tuple: (is_new_user, User object)
    """
    user = db.query(User).filter(User.id == user_data.id).first()
    if not user:
        user = User(**user_data.dict())
        db.add(user)
        db.commit()
        db.refresh(user)
        return True, user  # User was newly created
    return False, user  # User already existed


# CRUD Operations for Video

def create_video(db: Session, video_data: VideoCreate) -> Video:
    """
    Create a new video entry in the database.
    """
    video = Video(**video_data.dict())
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def get_video_by_name(db: Session, original_name: str) -> Optional[Video]:
    """
    Retrieve a video from the database by its original name.
    """
    return db.query(Video).filter(Video.original_name == original_name).first()


def get_videos_by_user(db: Session, user_id: str) -> List[Video]:
    """
    Retrieve all videos uploaded by a specific user.
    """
    return db.query(Video).filter(Video.user_id == user_id).all()


# CRUD Operations for AudioTask

def create_audio_task(db: Session, audio_task_data: AudioTaskCreate) -> AudioTask:
    """
    Create a new audio task entry in the database.
    """
    audio_task = AudioTask(**audio_task_data.dict())
    db.add(audio_task)
    db.commit()
    db.refresh(audio_task)
    return audio_task


# CRUD Operations for CompressTask

def create_compress_task(db: Session, compress_task_data: CompressTaskCreate) -> CompressTask:
    """
    Create a new compression task entry in the database.
    """
    compress_task = CompressTask(**compress_task_data.dict())
    db.add(compress_task)
    db.commit()
    db.refresh(compress_task)
    return compress_task


# CRUD Operations for Analysis

def save_analysis(db: Session, analysis_data: AnalysisCreate) -> Analysis:
    """
    Save analysis data to the database.
    """
    analysis = Analysis(**analysis_data.dict())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_statistics(db: Session, file_path: str) -> Optional[Analysis]:
    """
    Retrieve analysis data based on file path.
    """
    return db.query(Analysis).filter(Analysis.file_path == file_path).first()


# Update functions

def update_file_status(db: Session, task_id: str, result: str, file_type: str) -> bool:
    """
    Update the file path for a completed task in the database.

    :param task_id: ID of the task to update.
    :param result: The resulting file path after processing.
    :param file_type: Type of file ("audio" or "video").

    :return: True if successful; False otherwise.
    """
    if file_type == "audio":
        audio_task = db.query(AudioTask).filter(AudioTask.task_id == task_id).first()
        if audio_task:
            audio_task.file_path = result
            db.commit()
            return True
    elif file_type == "video":
        compress_task = db.query(CompressTask).filter(CompressTask.task_id == task_id).first()
        if compress_task:
            compress_task.file_path = result
            db.commit()
            return True
    return False
