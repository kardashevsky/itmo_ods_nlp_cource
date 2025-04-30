import uvicorn
from fastapi import FastAPI

from routers.router_auth import auth_router
from routers.router_service import router_service
from config import HOST, PORT

app = FastAPI(title="Front API")

app.include_router(auth_router)
app.include_router(router_service)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
