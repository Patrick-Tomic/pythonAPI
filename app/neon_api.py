import os
import httpx
from fastapi import HTTPException

NEON_API_BASE = "https://console.neon.tech/api/v2"
NEON_API_KEY = os.getenv("NEON_API_KEY")


def _headers() -> dict:
    if not NEON_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="NEON_API_KEY is not set. Add it to your .env file.",
        )
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEON_API_KEY}",
    }


async def _request(method: str, path: str, json: dict | None = None) -> dict | None:
    url = f"{NEON_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.request(method, url, headers=_headers(), json=json)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found on Neon")
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid Neon API key")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Neon API error: {response.text}")

    if response.status_code == 204 or not response.content:
        return None
    return response.json()


# ---- Databases ----

async def list_databases(project_id: str, branch_id: str) -> dict:
    return await _request("GET", f"/projects/{project_id}/branches/{branch_id}/databases")


async def get_database(project_id: str, branch_id: str, database_name: str) -> dict:
    return await _request(
        "GET", f"/projects/{project_id}/branches/{branch_id}/databases/{database_name}"
    )


async def create_database(project_id: str, branch_id: str, name: str, owner_name: str) -> dict:
    body = {"database": {"name": name, "owner_name": owner_name}}
    return await _request(
        "POST", f"/projects/{project_id}/branches/{branch_id}/databases", json=body
    )


async def update_database(
    project_id: str, branch_id: str, database_name: str, new_name: str | None = None,
    owner_name: str | None = None,
) -> dict:
    fields = {}
    if new_name:
        fields["name"] = new_name
    if owner_name:
        fields["owner_name"] = owner_name
    body = {"database": fields}
    return await _request(
        "PATCH",
        f"/projects/{project_id}/branches/{branch_id}/databases/{database_name}",
        json=body,
    )


async def delete_database(project_id: str, branch_id: str, database_name: str) -> dict | None:
    return await _request(
        "DELETE", f"/projects/{project_id}/branches/{branch_id}/databases/{database_name}"
    )


# ---- Roles ----

async def list_roles(project_id: str, branch_id: str) -> dict:
    return await _request("GET", f"/projects/{project_id}/branches/{branch_id}/roles")


async def get_role(project_id: str, branch_id: str, role_name: str) -> dict:
    return await _request(
        "GET", f"/projects/{project_id}/branches/{branch_id}/roles/{role_name}"
    )


async def create_role(project_id: str, branch_id: str, name: str, no_login: bool = False) -> dict:
    body = {"role": {"name": name, "no_login": no_login}}
    return await _request("POST", f"/projects/{project_id}/branches/{branch_id}/roles", json=body)


async def delete_role(project_id: str, branch_id: str, role_name: str) -> dict | None:
    return await _request(
        "DELETE", f"/projects/{project_id}/branches/{branch_id}/roles/{role_name}"
    )


async def reset_role_password(project_id: str, branch_id: str, role_name: str) -> dict:
    return await _request(
        "POST",
        f"/projects/{project_id}/branches/{branch_id}/roles/{role_name}/reset_password",
    )