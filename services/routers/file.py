import random
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from services.schemas.file import FileDownloadRequest, FileDownloadResponse, FileStatusResponse
from services.database.database import get_async_session
from services.database.models.file import File
import aiohttp
import io
import gzip
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/file',
    tags=["FileManager"]
)


async def download_and_process_file(url: str, task_id: int, session: AsyncSession):
    """
       Downloads a file from the specified URL, decompresses it, parses the content to extract ACCESSION numbers,
       and updates the status of the task in the database.

       Args:
           url (str): The URL of the file to download.
           task_id (int): The ID of the task associated with the download.
           session (AsyncSession): The SQLAlchemy async session used to interact with the database.

       Returns:
           None

       This function performs the following steps:
       1. Downloads the file from the provided URL.
       2. Reads and decompresses the file content.
       3. Extracts ACCESSION numbers from the decompressed file data.
       4. Updates the status of the task in the database based on the outcome of these operations.
       """
    try:
        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(url) as response:
                if response.status != 200:
                    await update_file_status(session, task_id, "Failed to download")
                    return

                file_content = io.BytesIO(await response.read())

                try:
                    with gzip.open(file_content, 'rt') as gzip_file:
                        file_data = gzip_file.read()
                except gzip.BadGzipFile:
                    await update_file_status(session, task_id, "Failed to decompress")
                    return

                accession_list = extract_accession_numbers(file_data)
                await update_file_status(session, task_id, "Completed", accession_list)

    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        await update_file_status(session, task_id, "Failed to download")
    except Exception as e:
        logger.exception("An unexpected error occurred in download_and_process_file")
        await update_file_status(session, task_id, "Failed due to an unexpected error")


def extract_accession_numbers(file_data: str) -> list:
    """
       Extracts ACCESSION numbers from the provided file data.

       Args:
           file_data (str): The content of the file as a string.

       Returns:
           list: A list of extracted ACCESSION numbers.

       This function processes the file content line by line, searching for lines that start with "ACCESSION"
       and extracts the number following this keyword.
       """
    accession_list = []
    for line in file_data.splitlines():
        if line.startswith("ACCESSION"):
            accession_list.append(line.split()[1])
    return accession_list


async def update_file_status(session: AsyncSession, task_id: int, status: str, accession_list: Optional[list] = None):
    """
      Updates the status of a file download task in the database.

      Args:
          session (AsyncSession): The SQLAlchemy async session used to interact with the database.
          task_id (int): The ID of the task whose status needs to be updated.
          status (str): The new status of the task.
          accession_list (Optional[list], optional): A list of ACCESSION numbers extracted from the file. Defaults to None.

      Returns:
          None

      This function updates the status of the task in the database and optionally updates additional fields
      such as the ACCESSION list and result count.
      """
    try:
        async with session.begin():
            result = await session.execute(select(File).filter_by(download_task_id=task_id))
            file_record = result.scalars().first()

            if not file_record:
                return

            file_record.status = status
            if accession_list is not None:
                file_record.accession_list = accession_list
                file_record.result_count = len(accession_list)

            await session.commit()
    except SQLAlchemyError as e:
        logger.exception("An error occurred while updating the file status")
        await session.rollback()


@router.post("/start-download/", response_model=FileDownloadResponse)
async def start_download(request: FileDownloadRequest, background_tasks: BackgroundTasks,
                         session: AsyncSession = Depends(get_async_session)):
    """
       Starts a file download task and schedules it for background processing.

       Args:
           request (FileDownloadRequest): The request body containing the URL of the file to download.
           background_tasks (BackgroundTasks): A FastAPI utility for running background tasks.
           session (AsyncSession, optional): The SQLAlchemy async session used to interact with the database. Defaults to Depends(get_async_session).

       Returns:
           dict: A dictionary containing the task ID and status of the task.

       Raises:
           HTTPException: If an error occurs while starting the download, a 500 status code is returned.

       This function creates a new task record in the database, schedules the background processing of the
       file download, and returns the task ID and initial status.
       """
    async with aiohttp.ClientSession() as client_session:
        try:
            async with client_session.head(request.url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Invalid URL")

        except aiohttp.ClientError as e:
            logger.error(f"URL validation failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid URL")

    task_id = random.randint(1, 10 ** 6)

    try:
        download_task = File(download_task_id=task_id, url=request.url, status="Downloading")
        session.add(download_task)
        await session.commit()
    except SQLAlchemyError as e:
        logger.exception("An error occurred while starting the download")
        raise HTTPException(status_code=500, detail="Failed to start download")

    background_tasks.add_task(download_and_process_file, request.url, task_id, session)
    return {"id": task_id, "status": "Downloading"}


@router.get("/status/{task_id}", response_model=FileStatusResponse)
async def check_status(task_id: int, session: AsyncSession = Depends(get_async_session)):
    """
      Retrieves the status of a file download task.

      Args:
          task_id (int): The ID of the task to check.
          session (AsyncSession, optional): The SQLAlchemy async session used to interact with the database. Defaults to Depends(get_async_session).

      Returns:
          dict: A dictionary containing the status, result count, and ACCESSION list of the task.

      Raises:
          HTTPException: If the task is not found or an error occurs while retrieving the status, a 404 or 500 status code is returned respectively.

      This function queries the database for the status of the specified task and returns relevant information.
      """
    try:
        async with session.begin():
            result = await session.execute(select(File).filter_by(download_task_id=task_id))
            file_record = result.scalars().first()

            if not file_record:
                raise HTTPException(status_code=404, detail="Task not found")

            display_accessions = file_record.accession_list[:20] if file_record.accession_list else []
            display_accessions.append('...')

            return {
                "status": file_record.status,
                "result_count": file_record.result_count,
                "accession_list": display_accessions
            }
    except SQLAlchemyError as e:
        logger.exception("An error occurred while checking the status")
        raise HTTPException(status_code=500, detail="Failed to retrieve status")
