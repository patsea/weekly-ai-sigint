"""API routes for prompt template management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/api/prompt", tags=["prompt"])

PROMPT_FILE = Path("prompts/sunday_briefing.md")
DEFAULT_PROMPT_FILE = Path("prompts/sunday_briefing.md.default")


class PromptResponse(BaseModel):
    """Current prompt content."""
    content: str
    file_path: str
    char_count: int
    word_count: int
    line_count: int


class PromptUpdate(BaseModel):
    """Prompt update request."""
    content: str


class PromptSaveResult(BaseModel):
    """Result of saving prompt."""
    success: bool
    message: str
    char_count: int
    word_count: int


@router.get("/", response_model=PromptResponse)
async def get_prompt():
    """Get current prompt template."""
    if not PROMPT_FILE.exists():
        raise HTTPException(status_code=404, detail="Prompt file not found")

    content = PROMPT_FILE.read_text()
    return PromptResponse(
        content=content,
        file_path=str(PROMPT_FILE),
        char_count=len(content),
        word_count=len(content.split()),
        line_count=len(content.splitlines()),
    )


@router.post("/", response_model=PromptSaveResult)
async def save_prompt(update: PromptUpdate):
    """Save updated prompt template."""
    if not update.content.strip():
        raise HTTPException(status_code=400, detail="Prompt content cannot be empty")

    # Backup current prompt before saving
    if PROMPT_FILE.exists():
        backup_path = PROMPT_FILE.with_suffix(".md.backup")
        backup_path.write_text(PROMPT_FILE.read_text())

    # Save new content
    PROMPT_FILE.write_text(update.content)

    return PromptSaveResult(
        success=True,
        message="Prompt saved successfully",
        char_count=len(update.content),
        word_count=len(update.content.split()),
    )


@router.post("/reset", response_model=PromptSaveResult)
async def reset_prompt():
    """Reset prompt to default template."""
    if not DEFAULT_PROMPT_FILE.exists():
        # If no default file, create one from current or use hardcoded default
        default_content = '''# Weekly AI Intelligence Briefing

You are an AI analyst preparing a weekly intelligence briefing on AI and enterprise technology developments.

## Your Task

Analyze the following content items and synthesize them into a cohesive weekly briefing.

## Content to Analyze

{content_items}

## Output Format

Create a briefing with:
1. **Executive Summary** (2-3 paragraphs)
2. **Key Developments** (bullet points with analysis)
3. **Strategic Implications** (what this means for enterprise leaders)
4. **Watch List** (emerging trends to monitor)

Be concise, insightful, and focus on actionable intelligence.
'''
        PROMPT_FILE.write_text(default_content)
        return PromptSaveResult(
            success=True,
            message="Reset to hardcoded default (no default file found)",
            char_count=len(default_content),
            word_count=len(default_content.split()),
        )

    default_content = DEFAULT_PROMPT_FILE.read_text()
    PROMPT_FILE.write_text(default_content)

    return PromptSaveResult(
        success=True,
        message="Prompt reset to default",
        char_count=len(default_content),
        word_count=len(default_content.split()),
    )


@router.get("/preview")
async def preview_prompt():
    """Preview prompt with sample variables filled in."""
    if not PROMPT_FILE.exists():
        raise HTTPException(status_code=404, detail="Prompt file not found")

    content = PROMPT_FILE.read_text()

    # Sample content for preview
    sample_content = """
### Source: Import AI Newsletter
**Date**: 2024-01-15
**Summary**: OpenAI announces GPT-5 development timeline...

### Source: Simon Willison's Blog
**Date**: 2024-01-14
**Summary**: New techniques for prompt engineering...
"""

    # Simple variable substitution for preview
    preview = content.replace("{content_items}", sample_content)
    preview = preview.replace("{week_start}", "2024-01-08")
    preview = preview.replace("{week_end}", "2024-01-14")

    return {
        "preview": preview,
        "variables_found": ["{content_items}", "{week_start}", "{week_end}"],
    }
