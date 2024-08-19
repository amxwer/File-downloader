from fastapi import FastAPI
from services.routers.file import router as file_router

app = FastAPI(
    title="FIle downloader",
    debug= True


)
app.include_router(file_router, prefix="/file", tags=["FileManager"])
