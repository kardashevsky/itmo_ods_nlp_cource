import logging

import requests
from celery import Celery

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, \
    SERVICE_COMMON_REPORT, SERVICE_COMMON_REPORT_QUEUE, API_URL, API_KEY

celery_worker = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_worker.conf.task_routes = {f"worker.*": {"queue": SERVICE_COMMON_REPORT_QUEUE}, }

# Set up logging
logging.basicConfig(level=logging.INFO)


@celery_worker.task(name=f"worker.{SERVICE_COMMON_REPORT}", bind=True)
def service_common_report(self, results) -> dict:
    """
    Generates speech improvement recommendations based on speech speed, mood, and pose.

    Expects `results` to be a list with:
      - results[0]: audio pipeline result, containing at least "speech_speed" and optionally "speaker_mood" or "emotions"
      - results[1]: video pipeline result, containing pose statistics under the "result" key.

    Returns:
      A dictionary with keys "status" and "result", where result is the recommendations string.
    """
    try:
        # Unpack the results from the chord (order matters based on your group definition)
        audio_result, video_result = results

        # Extract speech_speed and speaker_mood from audio_result
        if isinstance(audio_result, dict):
            speech_speed = audio_result.get("speech_speed", "N/A")
            speaker_mood = audio_result.get("speaker_mood", audio_result.get("emotions", "N/A"))
        else:
            speech_speed = "N/A"
            speaker_mood = audio_result

        # Extract speaker_pose from video_result
        if isinstance(video_result, dict):
            speaker_pose = video_result.get("result", "N/A")
        else:
            speaker_pose = video_result

        combined = {
            "speech_speed": speech_speed,
            "speaker_mood": speaker_mood,
            "speaker_pose": speaker_pose,
        }

        # Construct the prompt for the ChatGPT API
        prompt = f"""
            Скорость речи: {combined['speech_speed']} слов/мин
            Настроение (злой, счастливый, в энтузиазме, в отвращении, нейтральный): {combined['speaker_mood']}
            Поза (открытая, закрытая): {combined['speaker_pose']}
        """
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Без формальностей, только суть. Данные поступают как последовательность чисел: "
                        "(1) скорость речи (слов/мин), "
                        "(2-8) % времени в настроении (злой, счастливый, в энтузиазме, в отвращении, нейтральный, страх, грусть), "
                        "(9-10) % времени в позе (открытая, закрытая). "
                        "Дай рекомендации, как улучшить спич. Группируй комментарии. "
                        "Числа не повторяй. Если предлагаешь улучшить параметр, добавь конкретные техники и практики."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 900,
        }

        # Make the request to the OpenAI API
        response = requests.post(API_URL, headers=headers, json=data)

        if response.status_code == 200:
            recommendations = response.json()["choices"][0]["message"]["content"]
            return {"status": "SUCCESS", "result": recommendations}
        else:
            error_message = f"Ошибка: {response.status_code}, {response.text}"
            raise Exception(error_message)

    except Exception as e:
        import logging
        logging.error(f"Error in generate_speech_recommendations: {e}")
        try:
            self.retry(countdown=2)
        except Exception as retry_ex:
            logging.error(f"Max retries exceeded in generate_speech_recommendations: {retry_ex}")
            return {"status": "FAIL", "result": "max retries achieved", "error": str(e)}
