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
    status = Column(String, nullable=False, server_default="created")
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)

    user = relationship("User", back_populates="prospects_files", foreign_keys=[user_id])
    prospects = relationship("Prospect", back_populates="prospects_file")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"{self.id} | {self.saved_file_name}"
