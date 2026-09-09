from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud, schemas, npm, neon_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Your tables (e.g. 'applications') already exist in Neon, so we don't
    # run create_all here. If you add new models later, manage schema changes
    # with a migration tool like Alembic rather than auto-creating.
    yield


app = FastAPI(title="Neon CRUD Starter", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/npm/downloads/{package_name:path}")
async def npm_downloads(package_name: str, period: str = "last-week"):
    """
    Get download counts for an npm package.
    period: 'last-day', 'last-week', 'last-month', or a custom range
    like '2024-01-01:2024-01-31'.
    """
    return await npm.get_download_stats(package_name, period)


@app.post("/applications", response_model=schemas.ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(body: schemas.ApplicationCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_application(db, body)


@app.get("/applications", response_model=list[schemas.ApplicationOut])
async def list_applications(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_applications(db, skip=skip, limit=limit)


@app.get("/applications/{application_id}", response_model=schemas.ApplicationOut)
async def read_application(application_id: int, db: AsyncSession = Depends(get_db)):
    db_app = await crud.get_application(db, application_id)
    if db_app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_app


@app.patch("/applications/{application_id}", response_model=schemas.ApplicationOut)
async def update_application(
    application_id: int, body: schemas.ApplicationUpdate, db: AsyncSession = Depends(get_db)
):
    db_app = await crud.update_application(db, application_id, body)
    if db_app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_app


@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_application(db, application_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Application not found")


# ---- Neon management API: Databases ----
# These call Neon's control-plane API (console.neon.tech/api/v2), not your
# app's own Postgres connection. Requires NEON_API_KEY in .env.

@app.get("/neon/projects/{project_id}/branches/{branch_id}/databases")
async def list_neon_databases(project_id: str, branch_id: str):
    return await neon_api.list_databases(project_id, branch_id)


@app.get("/neon/projects/{project_id}/branches/{branch_id}/databases/{database_name}")
async def get_neon_database(project_id: str, branch_id: str, database_name: str):
    return await neon_api.get_database(project_id, branch_id, database_name)


@app.post(
    "/neon/projects/{project_id}/branches/{branch_id}/databases",
    status_code=status.HTTP_201_CREATED,
)
async def create_neon_database(project_id: str, branch_id: str, body: schemas.NeonDatabaseCreate):
    return await neon_api.create_database(project_id, branch_id, body.name, body.owner_name)


@app.patch("/neon/projects/{project_id}/branches/{branch_id}/databases/{database_name}")
async def update_neon_database(
    project_id: str, branch_id: str, database_name: str, body: schemas.NeonDatabaseUpdate
):
    return await neon_api.update_database(
        project_id, branch_id, database_name, new_name=body.name, owner_name=body.owner_name
    )


@app.delete(
    "/neon/projects/{project_id}/branches/{branch_id}/databases/{database_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_neon_database(project_id: str, branch_id: str, database_name: str):
    await neon_api.delete_database(project_id, branch_id, database_name)


# ---- Neon management API: Roles ----
# Roles are Postgres roles; Neon's API supports create/read/delete and
# password reset, but no general "update" (Postgres roles aren't freely
# renameable via this API).

@app.get("/neon/projects/{project_id}/branches/{branch_id}/roles")
async def list_neon_roles(project_id: str, branch_id: str):
    return await neon_api.list_roles(project_id, branch_id)


@app.get("/neon/projects/{project_id}/branches/{branch_id}/roles/{role_name}")
async def get_neon_role(project_id: str, branch_id: str, role_name: str):
    return await neon_api.get_role(project_id, branch_id, role_name)


@app.post(
    "/neon/projects/{project_id}/branches/{branch_id}/roles",
    status_code=status.HTTP_201_CREATED,
)
async def create_neon_role(project_id: str, branch_id: str, body: schemas.NeonRoleCreate):
    return await neon_api.create_role(project_id, branch_id, body.name, body.no_login)


@app.delete(
    "/neon/projects/{project_id}/branches/{branch_id}/roles/{role_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_neon_role(project_id: str, branch_id: str, role_name: str):
    await neon_api.delete_role(project_id, branch_id, role_name)


@app.post("/neon/projects/{project_id}/branches/{branch_id}/roles/{role_name}/reset-password")
async def reset_neon_role_password(project_id: str, branch_id: str, role_name: str):
    return await neon_api.reset_role_password(project_id, branch_id, role_name)