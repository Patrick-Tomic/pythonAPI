import httpx
from fastapi import HTTPException

NPM_DOWNLOADS_API = "https://api.npmjs.org/downloads/point"

VALID_PERIODS = {"last-day", "last-week", "last-month"}


async def get_download_stats(package: str, period: str = "last-week") -> dict:
    """
    Fetch download counts for an npm package from the official npm registry API.
    period: one of 'last-day', 'last-week', 'last-month' (or a custom range like
    '2024-01-01:2024-01-31' per npm's API docs).
    """
    url = f"{NPM_DOWNLOADS_API}/{period}/{package}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Package '{package}' not found on npm")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch data from npm registry")

    return response.json()