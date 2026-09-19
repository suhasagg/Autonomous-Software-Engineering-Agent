from datetime import datetime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,Text,DateTime,JSON
from .database import Base
class CodingTask(Base):
    __tablename__="coding_tasks"
    id:Mapped[str]=mapped_column(String(80),primary_key=True)
    repository:Mapped[str]=mapped_column(String(200))
    issue:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(40),default="CREATED")
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class AuditEvent(Base):
    __tablename__="coding_audit"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    task_id:Mapped[str]=mapped_column(String(80),index=True)
    event:Mapped[str]=mapped_column(String(80))
    payload:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
