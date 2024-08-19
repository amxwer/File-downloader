import datetime
import uuid

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, TIMESTAMP, Float, UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class File(Base):
    __tablename__ = 'files'
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    download_task_id = Column(Integer,nullable=False)
    size = Column(Float, nullable=True)
    url = Column(String, nullable=False)
    status = Column(String,default="Waiting for download")
    result_count = Column(Integer,default=0)
    accession_list = Column(MutableList.as_mutable(JSON),default=list)
    created_at = Column(DateTime,default=datetime.datetime.utcnow)
