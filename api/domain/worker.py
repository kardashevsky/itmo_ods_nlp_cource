from celery import Celery, chord, chain, group, signature

from config import (CELERY_RESULT_BACKEND, CELERY_BROKER_URL, SERVICE_AUDIO_EXTRACT_QUEUE, SERVICE_VIDEO_COMPRESS_QUEUE,
                           SERVICE_AUDIO_TRANSCRIBE_QUEUE, SERVICE_AUDIO_EMOTIONS_QUEUE, SERVICE_COMMON_REPORT_QUEUE,
                           SERVICE_AUDIO_EXTRACT, SERVICE_VIDEO_COMPRESS, SERVICE_AUDIO_TRANSCRIBE,
                           SERVICE_AUDIO_EMOTIONS, SERVICE_VIDEO_POSES, SERVICE_VIDEO_POSES_QUEUE,
                           SERVICE_COMMON_REPORT)

celery_client = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


async def define_chains(file_name, file_path):
    """Определяет и запускает обработку видео и аудио в параллели, затем собирает данные в report."""

    # Define the video pipeline: compression → pose analysis.
    video_pipeline = chain(
        signature(f"worker.{SERVICE_VIDEO_COMPRESS}", args=[file_name, file_path], queue=SERVICE_VIDEO_COMPRESS_QUEUE),
        signature(f"worker.{SERVICE_VIDEO_POSES}", queue=SERVICE_VIDEO_POSES_QUEUE)
    )

    # Define the audio pipeline: extraction → transcription → emotion analysis.
    audio_pipeline = chain(
        signature(f"worker.{SERVICE_AUDIO_EXTRACT}", args=[file_name, file_path], queue=SERVICE_AUDIO_EXTRACT_QUEUE),
        signature(f"worker.{SERVICE_AUDIO_TRANSCRIBE}", queue=SERVICE_AUDIO_TRANSCRIBE_QUEUE),
        signature(f"worker.{SERVICE_AUDIO_EMOTIONS}", queue=SERVICE_AUDIO_EMOTIONS_QUEUE)
    )

    # Run both pipelines in parallel using a group.
    processing_group = group(audio_pipeline, video_pipeline)

    # Define the final report task (the chord callback).
    report_task = signature(f"worker.{SERVICE_COMMON_REPORT}", queue=SERVICE_COMMON_REPORT_QUEUE)

    # Create a chord: once both pipelines finish, their results are passed to generate_speech_recommendations.
    workflow = chord(processing_group)(report_task)

    # Return the workflow ID to the user.
    return {
        "workflow_id": workflow.id  # This ID can later be used to query the result.
    }

