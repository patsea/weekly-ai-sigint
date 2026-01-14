# Fix Content Fetcher — Full Article Extraction

**Created**: 2026-01-13
**Purpose**: Update fetcher to extract full article content instead of just RSS snippets
**Execute from**: `~/Dropbox/ALOMA/claude-code/weekly-ai-sigint/`
**Estimated Duration**: 15-20 minutes

---

## Prerequisites

Before executing, read best practices from:
```
~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md
```

⚠️ **STOP LAUNCHD SERVICE FIRST** to avoid conflicts:
```bash
launchctl unload ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist 2>/dev/null || true
echo "✅ Service stopped"
```

---

## Step 1: Check Current ContentItem Model

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
grep -A5 "content = " app/models/content.py
```

**Expected**: Should be `Text` type (unlimited). If `String(N)`, needs update.

---

## Step 2: Install trafilatura

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
source venv/bin/activate
pip install trafilatura
echo "trafilatura" >> requirements.txt
echo "✅ trafilatura installed"
```

---

## Step 3: Create Content Extractor Module

```bash
cat > app/services/content_extractor.py << 'EOF'
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
EOF

echo "✅ Content extractor module created"
```

---

## Step 4: Update Fetcher to Use Full Content Extraction

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint

# Backup current fetcher
cp app/services/fetcher.py app/services/fetcher.py.backup

# Check current structure
grep -n "async def _fetch_rss\|result\[.description.\]\|result\[.content.\]" app/services/fetcher.py
```

Now update the fetcher. Find where content items are created and add full content extraction:

```python
# Add to imports at top of fetcher.py:
from app.services.content_extractor import extract_with_rate_limit
```

```python
# In _fetch_rss function, after getting feed entries, for each item:
# Replace the RSS description with full extracted content

# Before saving ContentItem, add:
full_content = await extract_with_rate_limit(entry.link)
if full_content:
    content_text = full_content
else:
    # Fallback to RSS description if extraction fails
    content_text = entry.get("description", "") or entry.get("summary", "")
```

---

## Step 5: Apply Changes to fetcher.py

This requires manual editing. Key changes:

### 5.1 Add import at top

```python
from app.services.content_extractor import extract_with_rate_limit
```

### 5.2 In `_fetch_rss` function, update content item creation

Find where `ContentItem` is created and update to extract full content:

```python
# After getting entry URL, before creating ContentItem:
full_content = await extract_with_rate_limit(entry.link)

# Use full_content if available, otherwise fall back to description
content_text = full_content if full_content else (
    entry.get("description", "") or entry.get("summary", "")
)

# When creating ContentItem, use content_text:
content_item = ContentItem(
    source_id=source.id,
    title=entry.get("title", "Untitled"),
    url=entry.link,
    content=content_text,  # Now contains full article
    # ... rest of fields
)
```

### 5.3 In `_fetch_blog` function, same pattern

```python
full_content = await extract_with_rate_limit(url)
content_text = full_content if full_content else description
```

---

## Step 6: Clear Existing Content and Re-fetch

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
source venv/bin/activate

# Start server temporarily
uvicorn app.main:app --port 8000 > /tmp/refetch.log 2>&1 &
sleep 4

# Check current content count
echo "=== Current Content ==="
curl -s http://localhost:8000/api/content/ | python3 -c "
import sys, json
items = json.load(sys.stdin)
print(f'Total items: {len(items)}')
if items:
    print(f'Sample content length: {len(items[0].get(\"content\", \"\"))} chars')
"

# Delete all existing content to force re-fetch with full extraction
echo ""
echo "=== Clearing old content ==="
# This requires a delete endpoint or direct DB access
```

---

## Step 7: Re-fetch All Sources

```bash
echo "=== Re-fetching all sources with full content extraction ==="
echo "This may take several minutes due to rate limiting..."

curl -s -X POST http://localhost:8000/api/run/fetch | python3 -m json.tool
```

---

## Step 8: Verify Content Quality

```bash
echo "=== Checking content quality ==="
curl -s "http://localhost:8000/api/content/?limit=3" | python3 -c "
import sys, json
items = json.load(sys.stdin)
for item in items:
    title = item.get('title', 'No title')[:50]
    content = item.get('content', '')
    print(f'Title: {title}...')
    print(f'Content length: {len(content)} chars')
    print(f'Preview: {content[:200]}...')
    print('---')
"
```

**Expected**: Content should be 1000+ characters per article, not 100-200.

---

## Step 9: Test Synthesis

```bash
echo "=== Testing synthesis with full content ==="
curl -s -X POST "http://localhost:8000/api/run/synthesize?days_back=7" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Status:', d.get('status'))
print('Briefing ID:', d.get('briefing_id'))
"
```

---

## Step 10: Restart launchd Service

```bash
# Stop test server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Restart launchd
launchctl load ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
sleep 3

# Verify
curl -s http://localhost:8000/health | python3 -c "
import sys, json
print('Health:', json.load(sys.stdin).get('status'))
"
echo "✅ Service restarted with full content extraction"
```

---

## Verification Checklist

- [ ] trafilatura installed
- [ ] content_extractor.py created
- [ ] fetcher.py updated with import
- [ ] fetcher.py uses extract_with_rate_limit for each item
- [ ] Old content cleared
- [ ] Sources re-fetched
- [ ] Content items now have 1000+ chars
- [ ] Synthesis produces structured briefing
- [ ] launchd service restarted

---

## Expected Outcome

| Before | After |
|--------|-------|
| RSS snippet: 100-200 chars | Full article: 2000-10000 chars |
| Claude confused by incomplete data | Claude produces structured briefing |
| "Content appears incomplete" error | Executive Brief + Thematic Digest |
