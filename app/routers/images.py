from fastapi import APIRouter, Query
import httpx

router = APIRouter(prefix="/images", tags=["Images"])

PEXELS_API_KEY = "O9yxd2XuZSipENPj5bbhlhba6JT6bmkHq9dgxwqWaPuQJFLyFUe22Vcb"

@router.get("/search")
async def search_images(query: str = Query(..., description="Search keyword")):
    """Search images from Pexels API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 1, "orientation": "landscape"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("photos") and len(data["photos"]) > 0:
                photo = data["photos"][0]
                return {
                    "url": photo["src"]["large"],
                    "medium": photo["src"]["medium"],
                    "small": photo["src"]["small"],
                    "photographer": photo["photographer"],
                    "alt": photo.get("alt", query)
                }
        
        # Fallback
        return {"url": f"https://source.unsplash.com/800x600/?{query}"}

@router.get("/topic/{keyword}")
async def get_topic_image(keyword: str):
    """Get image for a topic by keyword - optimized for caching"""
    search_terms = f"{keyword} conversation people speaking"
    return await search_images(search_terms)
