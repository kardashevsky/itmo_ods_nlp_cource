from sqlalchemy import Column, Integer, String
from storage.db_init import Base, engine


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    username = Column(String(65), nullable=False)


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # ForeignKey removed
    file_path = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    generated_name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)
    analysis = Column(String(32))


class AudioTask(Base):
    __tablename__ = "audio_tasks"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=False)  # ForeignKey removed
    task_id = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)


class CompressTask(Base):
    __tablename__ = "compress_tasks"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=False)  # ForeignKey removed
    task_id = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)


class Analysis(Base):
    __tablename__ = "analysis"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(255), nullable=False)
    speech_speed = Column(String)
    transcript = Column(String)
    emotions = Column(String)
    poses = Column(String)
    video_id = Column(Integer, nullable=False)  # ForeignKey removed


# Create tables
Base.metadata.create_all(engine)

print("✅ Tables created successfully!")
