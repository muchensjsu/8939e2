from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    UploadFile,
    File,
    BackgroundTasks,
    Form,
)
from pydantic import ValidationError
from api import schemas
import aiofiles
from typing import Optional
from csv import reader
from sqlalchemy.orm.session import Session
import uuid

from api.crud import ProspectCrud, ProspectsFileCrud
from api.dependencies.db import get_db
from api.dependencies.auth import get_current_user

router = APIRouter(prefix="/api", tags=["prospect_files"])


@router.post(
    "/prospect_files/import", response_model=schemas.ProspectFileImportResponse
)
async def upload_prospects_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    email_index: int = Form(...),
    first_name_index: Optional[int] = Form(-1),
    last_name_index: Optional[int] = Form(-1),
    force: Optional[bool] = Form(False),
    has_headers: Optional[bool] = Form(True),
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload the file and save it on server"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )

    new_filename = str(uuid.uuid4()) + ".csv"
    async with aiofiles.open(new_filename, "wb") as out_file:
        content = await file.read(1024)
        while content:
            await out_file.write(content)
            content = await file.read(1024)

    total_rows = 0
    with open(new_filename, "r") as read_obj:
        csv_reader = reader(read_obj)
        if has_headers:
            next(csv_reader)
        for _ in csv_reader:
            total_rows += 1

    if total_rows == 0:
        raise HTTPException(
            status_code=400, detail="No data found in the uploaded file"
        )

    # create file object and save it to database.
    file_in_db = ProspectsFileCrud.create_prospects_file(
        db,
        current_user.id,
        {
            "original_file_name": file.filename,
            "saved_file_name": new_filename,
            "total_rows": total_rows,
        },
    )
    background_tasks.add_task(
        write_prospects,
        file_in_db.id,
        new_filename,
        email_index,
        first_name_index,
        last_name_index,
        force,
        has_headers,
        current_user,
        db,
    )
    return {
        "result": "File upload success. Waiting to be processed.",
        "file_id": file_in_db.id,
    }


def write_prospects(
    file_id: int,
    file: str,
    email_index,
    first_name_index,
    last_name_index,
    force,
    has_headers,
    current_user,
    db,
):
    """Extract prospects from file and insert into database"""
    user_id = current_user.id
    ProspectsFileCrud.update_file_state(db, file_id, "processing")
    try:
        with open(file, "r") as read_obj:
            csv_reader = reader(read_obj)
            if has_headers:
                next(csv_reader)
            prospects_to_be_processed = {}
            # Iterate over each row
            for row in csv_reader:
                f_name = "" if first_name_index == -1 else row[first_name_index]
                l_name = "" if last_name_index == -1 else row[last_name_index]
                prospect = schemas.ProspectCreate(
                    email=row[email_index].lower(),
                    first_name=f_name,
                    last_name=l_name,
                    file_id=file_id,
                )
                prospects_to_be_processed[prospect.email] = prospect
                if len(prospects_to_be_processed) >= 1000:
                    ProspectCrud.add_prospects_by_emails(
                        db, user_id, prospects_to_be_processed, force
                    )
                    prospects_to_be_processed = {}

            if len(prospects_to_be_processed) > 0:
                ProspectCrud.add_prospects_by_emails(
                    db, user_id, prospects_to_be_processed, force
                )

    except ValidationError:
        ProspectsFileCrud.update_file_state(db, file_id, "failed")
    else:
        ProspectsFileCrud.update_file_state(db, file_id, "finished")


@router.get(
    "/prospects_files/{id}/progress",
    response_model=schemas.ProspectFileProgressResponse,
)
def get_file_progress(
    id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """Check the progress of file"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )

    file = ProspectsFileCrud.get_file_by_id(db, id)
    if not file:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"File with id {id} does not exist",
        )
    if file.user_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=f"You do not have access to this file",
        )
    done = ProspectCrud.get_file_prospects_done(db, id)
    return {"total": file.total_rows, "done": done}
