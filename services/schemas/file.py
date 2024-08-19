from pydantic import BaseModel
from typing import List,Optional
import datetime

class FileDownloadRequest(BaseModel):
    """
       Request model for starting a file download.

       Attributes:
           url (str): The URL of the file to download.
       """
    url:str



class FileStatusResponse(BaseModel):
    """
       Response model for checking the status of a file download task.

       Attributes:
           status (str): The current status of the file download task.
           result_count (Optional[int]): The number of results obtained from processing the file (e.g., number of ACCESSION numbers).
           accession_list (Optional[List[str]]): A list of ACCESSION numbers extracted from the file.
       """
    status: str
    result_count: Optional[int] = None
    accession_list: Optional[List[str]] = None

class FileDownloadResponse(BaseModel):
    """
    Response model for the initiation of a file download task.

    Attributes:
        id (int): The unique ID assigned to the file download task.
        status (str): The initial status of the file download task.
    """
    id: int
    status: str



class FileUpdate(BaseModel):
    """
      Update model for partial updates to a file record.

      Attributes:
          size (Optional[float]): The size of the file.
          url (Optional[str]): The URL of the file.
          status (Optional[str]): The status of the file download task.
          result_count (Optional[int]): The number of results obtained from processing the file.
          accession_list (Optional[List[str]]): A list of ACCESSION numbers extracted from the file.
          created_at (Optional[datetime.datetime]): The creation timestamp of the file record.
      """
    size: Optional[float] = None
    url: Optional[str] = None
    status: Optional[str] = None
    result_count: Optional[int] = None
    accession_list: Optional[List[str]] = None
    created_at: Optional[datetime.datetime] = None

    class config:
        orm_mode = True