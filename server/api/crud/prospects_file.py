from typing import Union
from sqlalchemy.orm.session import Session
from api import schemas
from api.models import ProspectsFile


class ProspectsFileCrud:
    @classmethod
    def create_prospects_file(
        cls,
        db: Session,
        user_id: int,
        data: schemas.ProspectsFileCreate,
    ) -> ProspectsFile:
        file = ProspectsFile(**data, user_id=user_id)
        db.add(file)
        db.commit()
        db.refresh(file)
        return file

    @classmethod
    def update_file_state(cls, db: Session, file_id: int, status: str):
        db.query(ProspectsFile).filter(ProspectsFile.id == file_id).update(
            {ProspectsFile.status: status}, synchronize_session="fetch"
        )
        db.commit()

    @classmethod
    def get_file_by_id(cls, db: Session, file_id: int) -> Union[ProspectsFile, None]:
        return db.query(ProspectsFile).filter(ProspectsFile.id == file_id).one_or_none()
