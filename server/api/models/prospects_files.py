from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, DateTime, Integer, String

from api.database import Base

class ProspectsFile(Base):
    """Prospects files table"""

    __tablename__ = "prospects_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    original_file_name = Column(String, nullable=False)
    saved_file_name = Column(String, nullable=False)
    total_rows = Column(Integer, nullable=False)
    done_rows = Column(Integer, nullable=False, server_default="0")
    status = Column(String, nullable=False, server_default="created")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"{self.id} | {self.saved_file_name}"