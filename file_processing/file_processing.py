import aiohttp
import gzip
import io
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from services.database.models.file import File

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


async def download_and_process_file(url: str, task_id: str, session: AsyncSession):
    """
       Downloads a file from the specified URL, decompresses it, parses the content to extract ACCESSION numbers,
       and updates the status of the task in the database.

       Args:
           url (str): The URL of the file to download.
           task_id (str): The ID of the task associated with the download.
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
                except (OSError, gzip.BadGzipFile) as e:
                    logger.error(f"Failed to decompress file: {e}")
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


async def update_file_status(session: AsyncSession, task_id: str, status: str, accession_list: Optional[list] = None):
    try:
        async with session.begin():

            result = await session.execute(select(File).filter_by(download_task_id=task_id))
            file_record = result.scalars().first()

            if not file_record:
                logger.warning(f"No record found for task_id: {task_id}")
                return

            file_record.status = status
            if accession_list is not None:
                file_record.accession_list = accession_list
                file_record.result_count = len(accession_list)

            await session.commit()
    except SQLAlchemyError as e:
        logger.exception("An error occurred while updating the file status")
        await session.rollback()
