from typing import List, Set, Union
from sqlalchemy.orm.session import Session
from api import schemas
from api.models import Prospect
from api.core.constants import DEFAULT_PAGE_SIZE, DEFAULT_PAGE, MIN_PAGE, MAX_PAGE_SIZE


class ProspectCrud:
    @classmethod
    def get_users_prospects(
        cls,
        db: Session,
        user_id: int,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Union[List[Prospect], None]:
        """Get user's prospects"""
        if page < MIN_PAGE:
            page = MIN_PAGE
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        return (
            db.query(Prospect)
            .filter(Prospect.user_id == user_id)
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

    @classmethod
    def add_prospects_by_emails(
        cls, db: Session, user_id: int, data: dict, force: bool
    ):
        rows_need_update = (
            db.query(Prospect)
            .filter(Prospect.email.in_(data))
            .filter(Prospect.user_id == user_id)
        )
        if force:
            for row in rows_need_update:
                row.first_name = data[row.email].first_name
                row.last_name = data[row.email].last_name
                row.file_id = data[row.email].file_id
        for row in rows_need_update:
            del data[row.email]
        inserts = [
            Prospect(
                email=data[k].email,
                first_name=data[k].first_name,
                last_name=data[k].last_name,
                file_id=data[k].file_id,
                user_id=user_id,
            )
            for k in data
        ]
        db.add_all(inserts)
        db.commit()

    @classmethod
    def get_user_prospects_total(cls, db: Session, user_id: int) -> int:
        return db.query(Prospect).filter(Prospect.user_id == user_id).count()

    @classmethod
    def get_file_prospects_done(cls, db: Session, file_id: int) -> int:
        return db.query(Prospect).filter(Prospect.file_id == file_id).count()

    @classmethod
    def create_prospect(
        cls, db: Session, user_id: int, data: schemas.ProspectCreate
    ) -> Prospect:
        """Create a prospect"""
        prospect = Prospect(
            email=data.email.lower(),
            first_name=data.first_name,
            last_name=data.last_name,
            file_id=data.file_id,
            user_id=user_id,
        )
        db.add(prospect)
        db.commit()
        db.refresh(prospect)
        return prospect

    @classmethod
    def validate_prospect_ids(
        cls, db: Session, user_id: int, unvalidated_prospect_ids: Set[int]
    ) -> Set[int]:
        res = (
            db.query(Prospect.id)
            .filter(
                Prospect.user_id == user_id, Prospect.id.in_(unvalidated_prospect_ids)
            )
            .all()
        )
        return {row.id for row in res}
