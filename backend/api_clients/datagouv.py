import httpx
from backend.config import settings

BASE_URL = settings.datagouv_base_url


async def search_datasets(keyword: str, page_size: int = 10) -> list[dict]:
    params = {"q": keyword, "page_size": page_size}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/datasets/", params=params)
        resp.raise_for_status()
        data = resp.json()
    return data.get("data", [])


async def get_dpe_dataset_url(departement: str) -> str | None:
    """
    Find the DPE dataset for a given departement from data.gouv.fr.
    Returns the download URL of the CSV resource if found.
    """
    keyword = f"DPE logements existants {departement}"
    datasets = await search_datasets(keyword, page_size=5)
    for ds in datasets:
        for resource in ds.get("resources", []):
            if resource.get("format", "").lower() == "csv":
                return resource.get("url")
    return None
