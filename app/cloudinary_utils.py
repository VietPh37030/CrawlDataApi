"""
Cloudinary Image Upload Utility
Uploads cover images to Cloudinary with automatic WebP conversion
"""
import httpx
import cloudinary
import cloudinary.uploader
from functools import lru_cache
from .config import get_settings


@lru_cache()
def init_cloudinary():
    """Initialize Cloudinary with credentials"""
    settings = get_settings()
    
    if not settings.cloudinary_cloud_name:
        print("[Cloudinary] WARNING: No cloud_name configured, image upload disabled")
        return False
    
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    print(f"[Cloudinary] Initialized for cloud: {settings.cloudinary_cloud_name}")
    return True


async def download_image(url: str) -> bytes | None:
    """Download image from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "image/*",
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.content
    except Exception as e:
        print(f"[Cloudinary] Download failed for {url}: {e}")
        return None


def upload_image_to_cloudinary(
    image_data: bytes, 
    public_id: str,
    folder: str = "covers"
) -> str | None:
    """
    Upload image to Cloudinary with WebP conversion
    
    Args:
        image_data: Raw image bytes
        public_id: Unique ID for the image (e.g., story slug)
        folder: Cloudinary folder name
        
    Returns:
        Cloudinary URL (WebP format) or None if failed
    """
    if not init_cloudinary():
        return None
    
    try:
        # Upload with automatic WebP conversion and optimization
        result = cloudinary.uploader.upload(
            image_data,
            public_id=public_id,
            folder=folder,
            format="webp",  # Convert to WebP
            transformation=[
                {"width": 300, "height": 400, "crop": "fill"},  # Resize to cover size
                {"quality": "auto:good"},  # Optimize quality
                {"fetch_format": "auto"},  # Best format for browser
            ],
            overwrite=True,
            resource_type="image"
        )
        
        webp_url = result.get("secure_url", "")
        print(f"[Cloudinary] Uploaded: {public_id} -> {webp_url}")
        return webp_url
        
    except Exception as e:
        print(f"[Cloudinary ERROR] Upload failed for {public_id}: {e}")
        return None


async def upload_cover_from_url(source_url: str, story_slug: str) -> str | None:
    """
    Download cover image from source URL and upload to Cloudinary
    
    Args:
        source_url: Original cover image URL
        story_slug: Story slug for naming
        
    Returns:
        Cloudinary WebP URL or original URL if upload fails
    """
    if not source_url:
        return None
    
    # Download image
    image_data = await download_image(source_url)
    if not image_data:
        print(f"[Cloudinary] Using original URL: {source_url}")
        return source_url
    
    # Upload to Cloudinary
    cloudinary_url = upload_image_to_cloudinary(image_data, story_slug)
    
    return cloudinary_url or source_url


async def migrate_story_cover(story: dict, db) -> str | None:
    """
    Migrate story cover from truyenfull to Cloudinary
    Updates database with new Cloudinary URL
    
    Args:
        story: Story dict with cover_url and slug
        db: Database instance
        
    Returns:
        New Cloudinary URL or None
    """
    original_url = story.get("cover_url", "")
    slug = story.get("slug", "")
    
    if not original_url or not slug:
        return None
    
    # Skip if already on Cloudinary
    if "cloudinary.com" in original_url:
        return original_url
    
    # Upload to Cloudinary
    new_url = await upload_cover_from_url(original_url, slug)
    
    if new_url and new_url != original_url:
        # Update database
        await db.update_story(story["id"], {"cover_url": new_url})
        print(f"[Cloudinary] Migrated cover: {slug}")
        return new_url
    
    return original_url
