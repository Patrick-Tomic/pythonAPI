from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr


class ApplicationBase(BaseModel):
    role: str
    company: str
    salary: int | None = None
    email: str
    emailed: bool | None = False
    response: bool | None = False
    followup: date | None = None
    date_applied: date | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    role: str | None = None
    company: str | None = None
    salary: int | None = None
    email: str | None = None
    emailed: bool | None = None
    response: bool | None = None
    followup: date | None = None
    date_applied: date | None = None


class ApplicationOut(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---- Neon management API schemas ----

class NeonDatabaseCreate(BaseModel):
    name: str
    owner_name: str


class NeonDatabaseUpdate(BaseModel):
    name: str | None = None
    owner_name: str | None = None


class NeonRoleCreate(BaseModel):
    name: str
    no_login: bool = False