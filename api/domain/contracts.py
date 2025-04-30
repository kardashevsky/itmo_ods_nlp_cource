from pydantic import BaseModel, constr
from typing import List, Optional


class UserBase(BaseModel):
    id: int
    first_name: constr(max_length=64)
    last_name: constr(max_length=64)
    username: constr(max_length=65)


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: str

    class Config:
        orm_mode = True


class VideoBase(BaseModel):
    original_name: str
    generated_name: str
    status: constr(max_length=32)
    analysis: Optional[str] = None
    file_path: str  # add this field

class VideoCreate(VideoBase):
    user_id: int


class Video(VideoBase):
    file_path: str
    user_id: str

    class Config:
        orm_mode = True


class AudioTaskBase(BaseModel):
    task_id: str
    file_path: str


class AudioTaskCreate(AudioTaskBase):
    video_id: str


class AudioTask(AudioTaskBase):
    video_id: str

    class Config:
        orm_mode = True


class CompressTaskBase(BaseModel):
    task_id: str
    file_path: str


class CompressTaskCreate(CompressTaskBase):
    video_id: str


class CompressTask(CompressTaskBase):
    video_id: str

    class Config:
        orm_mode = True


class AnalysisBase(BaseModel):
    speech_speed: Optional[str] = None
    transcript: Optional[str] = None
    emotions: Optional[str] = None
    poses: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    file_path: str


class Analysis(AnalysisBase):
    file_path: str

    class Config:
        orm_mode = True

