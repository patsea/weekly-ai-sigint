"""Extract full article content from URLs."""
import asyncio
import logging
from typing import Optional
import httpx
import trafilatura

logger = logging.getLogger(__name__)

# Rate limiting: delay between requests
REQUEST_DELAY_SECONDS = 1.5

async def extract_article_content(url: str, timeout: float = 30.0) -> Optional[str]:
    """
    Fetch URL and extract main article content.
    
    Args:
        url: Article URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Extracted article text, or None if extraction failed
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            
        # Extract main content using trafilatura
        content = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,  # favor recall for more content
        )
        
        if content:
            logger.info(f"Extracted {len(content)} chars from {url[:50]}...")
            return content
        else:
            logger.warning(f"No content extracted from {url[:50]}...")
            return None
            
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url[:50]}...")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url[:50]}...")
        return None
    except Exception as e:
        logger.error(f"Error extracting from {url[:50]}: {e}")
        return None


async def extract_with_rate_limit(url: str) -> Optional[str]:
    """Extract content with rate limiting delay."""
    content = await extract_article_content(url)
    await asyncio.sleep(REQUEST_DELAY_SECONDS)
    return content
