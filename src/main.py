import firebase_admin
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from firebase_admin import credentials

from src.routers import account_router, gacha_router, item_router

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    account_router.router,
    tags=["Account"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    item_router.router,
    tags=["Item"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    gacha_router.router,
    tags=["Gacha"],
    responses={404: {"description": "Not found"}},
)

app.mount("/", StaticFiles(directory="./static/build", html=True), name="static")


# If url not found in backend, pass to frontend.
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return FileResponse("./static/build/index.html")


if __name__ == "__main__":
    cred = credentials.Certificate(
        "private_keys/the-aegis-forge-fe-firebase-adminsdk-fbsvc-ae3c292608.json"
    )
    firebase_admin.initialize_app(cred)
    print("Current App Name:", firebase_admin.get_app().project_id)

    uvicorn.run("src.main:app", port=5000, host="0.0.0.0", log_level="info")
