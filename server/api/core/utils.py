from fastapi import Depends
from pydantic import ValidationError
from api import schemas
from csv import reader
from sqlalchemy.orm.session import Session

from api.crud import ProspectCrud, ProspectsFileCrud
from api.dependencies.db import get_db
from api.dependencies.auth import get_current_user
from .constants import MAX_PROSPECTS_SIZE


def write_prospects(
    file_id: int,
    file: str,
    email_index: int,
    first_name_index: int,
    last_name_index: int,
    force: bool,
    has_headers: bool,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
                if len(prospects_to_be_processed) >= MAX_PROSPECTS_SIZE:
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
