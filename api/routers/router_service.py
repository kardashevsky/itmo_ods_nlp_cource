import logging
import uuid
from http import HTTPStatus

from celery.result import AsyncResult
from domain.helpers import validate_init_data, get_or_create_user_record, save_video_file
from domain.worker import celery_client, define_chains
from fastapi import APIRouter, Header, UploadFile, File, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from storage.db_init import get_db

router_service = APIRouter(prefix="/service")


# ----------------------------
# Group task
# ----------------------------
@router_service.post("/upload")
async def upload_video(init_string: str = Header(None), file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Endpoint to upload a video file.
    """
    try:
        init_data = validate_init_data(init_string)
        get_or_create_user_record(db, init_data)

        # Generate a random filename
        random_filename = f"{uuid.uuid4().hex}"
        file_path = save_video_file(file, generated_name=random_filename, db=db, init_data=init_data)

        pipeline_info = await define_chains(random_filename, file_path)
        pipeline_info.update({"message": "File uploaded successfully"})

        return JSONResponse(status_code=HTTPStatus.OK, content=pipeline_info)
    except ValueError as ex:
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST, content={"error": str(ex)})
    except Exception as ex:
        logging.exception("An error occurred while processing the request.")
        return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content={"error": str(ex)})


@router_service.get("/check_task/{workflow_id}")
async def get_group_task_result(workflow_id: str):
    """
    Check the status of a Celery chord (final aggregated task).
    """
    task_result = AsyncResult(workflow_id, app=celery_client)
    if task_result:
        if task_result.ready():
            return {"workflow_id": workflow_id, "status": task_result.status, "result": task_result.result}
        else:
            return {"workflow_id": workflow_id, "status": task_result.status, "result": "Not ready"}
    else:
        return {"error": "Invalid workflow ID or task does not exist."}


# ----------------------------
# NOT YET IMPLEMENTED - SINGLE TASK
# ----------------------------
