from pydantic import BaseModel
from datetime import datetime


class ProspectsFile(BaseModel):
    id: int
    original_file_name: str
    saved_file_name: str
    total_rows: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class ProspectFileImportResponse(BaseModel):
    result: str
    file_id: int


class ProspectsFileCreate(BaseModel):
    original_file_name: str
    saved_file_name: str
    total_rows: int


class ProspectFileProgressResponse(BaseModel):
    total: int
    done: int
