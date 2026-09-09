from datetime import date
from sqlalchemy import String, Integer, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column("_id", Integer, primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    emailed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    response: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    followup: Mapped[date | None] = mapped_column(Date, nullable=True)