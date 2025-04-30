import logging
from http import HTTPStatus

from fastapi import APIRouter, Header, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from domain.helpers import validate_init_data, get_or_create_user_record
from storage.db_init import get_db

auth_router = APIRouter(prefix="/user")


@auth_router.get("/")
async def get_user(init_string: str = Header(None), db: Session = Depends(get_db)):
    """
    Endpoint to retrieve or create a user based on init_data.
    """
    try:
        init_data = validate_init_data(init_string)
        is_new_user, user_record = get_or_create_user_record(db, init_data)

        response = {
            "is_new": is_new_user,
            "user": {
                "id": user_record.id,
                "first_name": user_record.first_name,
                "last_name": user_record.last_name,
                "username": user_record.username,
            }
        }
        return JSONResponse(status_code=HTTPStatus.OK, content=response)
    except ValueError as ex:
        return JSONResponse(status_code=HTTPStatus.UNAUTHORIZED, content={"error": str(ex)})
    except Exception as ex:
        logging.exception("An error occurred while processing the request.")
        return JSONResponse(status_code=HTTPStatus.BAD_REQUEST, content={"error": str(ex)})
