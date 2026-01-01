# Weekly AI Sigint — Phase 5E Instructions

> Execute Phase 5E: Prompt Editor UI

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Read best practices first
cat ~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md | head -100

# Verify Phase 5D complete
ls -la app/templates/settings.html app/routers/settings.py

# Check current prompt file location
ls -la prompts/

# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## Phase 5E Scope

### Deliverables

1. `app/templates/prompt.html` — Prompt editor page with textarea
2. `app/routers/prompt.py` — Prompt file API endpoints
3. Update `app/routers/views.py` — Prompt editor page route
4. Update `app/main.py` — Register prompt router
5. Update `app/templates/base.html` — Add Prompt link to navigation

### Features to Implement

- View current prompt template
- Edit prompt in textarea with syntax highlighting (optional)
- Save changes to prompts/sunday_briefing.md
- Reset to default prompt
- Preview rendered prompt (with sample variables)
- Character/word count display

---

## Implementation Details

### 1. `app/routers/prompt.py`

```python
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
```

### 2. `app/templates/prompt.html`

```html
{% extends "base.html" %}
{% block title %}Prompt Editor - Weekly AI Sigint{% endblock %}
{% block content %}
<div class="mb-6">
    <h1 class="text-2xl font-bold">Prompt Editor</h1>
    <p class="text-gray-600 mt-1">Edit the Claude prompt template used for briefing synthesis</p>
</div>

<!-- Status Message -->
<div id="status-message" class="hidden mb-4 p-4 rounded"></div>

<!-- Editor Section -->
<div class="bg-white rounded-lg shadow p-6 mb-6">
    <div class="flex justify-between items-center mb-4">
        <div>
            <h2 class="text-lg font-semibold">Prompt Template</h2>
            <p class="text-sm text-gray-500" id="file-path">Loading...</p>
        </div>
        <div class="flex gap-2">
            <button onclick="resetPrompt()" class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition">
                Reset to Default
            </button>
            <button onclick="savePrompt()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition">
                Save Changes
            </button>
        </div>
    </div>
    
    <!-- Textarea Editor -->
    <textarea 
        id="prompt-editor" 
        class="w-full h-96 font-mono text-sm border rounded p-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        placeholder="Loading prompt template..."
    ></textarea>
    
    <!-- Stats Bar -->
    <div class="flex justify-between mt-2 text-sm text-gray-500">
        <div>
            <span id="char-count">0</span> characters · 
            <span id="word-count">0</span> words · 
            <span id="line-count">0</span> lines
        </div>
        <div>
            <button onclick="togglePreview()" class="text-blue-500 hover:underline">
                Toggle Preview
            </button>
        </div>
    </div>
</div>

<!-- Preview Section (hidden by default) -->
<div id="preview-section" class="hidden bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-lg font-semibold mb-4">Preview (with sample data)</h2>
    <div id="preview-content" class="prose max-w-none bg-gray-50 p-4 rounded border">
        Loading preview...
    </div>
</div>

<!-- Help Section -->
<div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold mb-4">Template Variables</h2>
    <p class="text-gray-600 mb-4">Use these variables in your prompt template:</p>
    <table class="w-full text-sm">
        <thead class="bg-gray-50">
            <tr>
                <th class="text-left p-2">Variable</th>
                <th class="text-left p-2">Description</th>
            </tr>
        </thead>
        <tbody>
            <tr class="border-t">
                <td class="p-2 font-mono text-blue-600">{content_items}</td>
                <td class="p-2">The formatted content items to analyze</td>
            </tr>
            <tr class="border-t">
                <td class="p-2 font-mono text-blue-600">{week_start}</td>
                <td class="p-2">Start date of the week being analyzed</td>
            </tr>
            <tr class="border-t">
                <td class="p-2 font-mono text-blue-600">{week_end}</td>
                <td class="p-2">End date of the week being analyzed</td>
            </tr>
        </tbody>
    </table>
</div>

<script>
let originalContent = '';

async function loadPrompt() {
    try {
        const response = await fetch('/api/prompt/');
        if (!response.ok) throw new Error('Failed to load prompt');
        const data = await response.json();
        
        document.getElementById('prompt-editor').value = data.content;
        document.getElementById('file-path').textContent = data.file_path;
        originalContent = data.content;
        updateStats();
    } catch (error) {
        showStatus('Error loading prompt: ' + error.message, 'error');
    }
}

async function savePrompt() {
    const content = document.getElementById('prompt-editor').value;
    
    try {
        const response = await fetch('/api/prompt/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content }),
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to save');
        
        originalContent = content;
        showStatus('Prompt saved successfully!', 'success');
        updateStats();
    } catch (error) {
        showStatus('Error saving prompt: ' + error.message, 'error');
    }
}

async function resetPrompt() {
    if (!confirm('Reset prompt to default? Your current changes will be lost.')) return;
    
    try {
        const response = await fetch('/api/prompt/reset', { method: 'POST' });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to reset');
        
        await loadPrompt();
        showStatus('Prompt reset to default', 'success');
    } catch (error) {
        showStatus('Error resetting prompt: ' + error.message, 'error');
    }
}

async function togglePreview() {
    const section = document.getElementById('preview-section');
    const isHidden = section.classList.contains('hidden');
    
    if (isHidden) {
        try {
            const response = await fetch('/api/prompt/preview');
            const data = await response.json();
            
            // Simple markdown-ish rendering
            let html = data.preview
                .replace(/^### (.+)$/gm, '<h3 class="font-bold mt-4">$1</h3>')
                .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-4">$1</h2>')
                .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold mt-4">$1</h1>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
            
            document.getElementById('preview-content').innerHTML = html;
        } catch (error) {
            document.getElementById('preview-content').innerHTML = 'Error loading preview';
        }
    }
    
    section.classList.toggle('hidden');
}

function updateStats() {
    const content = document.getElementById('prompt-editor').value;
    document.getElementById('char-count').textContent = content.length;
    document.getElementById('word-count').textContent = content.split(/\s+/).filter(w => w).length;
    document.getElementById('line-count').textContent = content.split('\n').length;
}

function showStatus(message, type) {
    const el = document.getElementById('status-message');
    el.textContent = message;
    el.className = type === 'error' 
        ? 'mb-4 p-4 rounded bg-red-100 text-red-700'
        : 'mb-4 p-4 rounded bg-green-100 text-green-700';
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 5000);
}

// Event listeners
document.getElementById('prompt-editor').addEventListener('input', updateStats);

// Warn on unsaved changes
window.addEventListener('beforeunload', (e) => {
    const current = document.getElementById('prompt-editor').value;
    if (current !== originalContent) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// Load on page load
loadPrompt();
</script>
{% endblock %}
```

### 3. Update `app/templates/base.html`

Add "Prompt" link to navigation:

```html
<!-- Find the nav section and add after Settings -->
<a href="/prompt" class="{% if request.url.path == '/prompt' %}text-blue-600 font-medium{% else %}text-gray-600 hover:text-gray-900{% endif %}">
    Prompt
</a>
```

### 4. Update `app/routers/views.py`

```python
@router.get("/prompt", response_class=HTMLResponse)
async def prompt_page(request: Request):
    """Prompt editor page."""
    return templates.TemplateResponse("prompt.html", {
        "request": request,
    })
```

### 5. Update `app/main.py`

```python
from app.routers import sources, content, manual, briefings, views, settings, prompt

# Add after other routers
app.include_router(prompt.router)
```

---

## Verification Gate

After implementation, verify:

```bash
# 1. Start server
source venv/bin/activate
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
uvicorn app.main:app --port 8000 > /tmp/phase5e-test.log 2>&1 &
sleep 3

# 2. Check health
curl -s http://localhost:8000/health

# 3. Check prompt page renders
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/prompt
# Expected: 200

# 4. Check prompt API (single line!)
curl -s http://localhost:8000/api/prompt/ | python3 -m json.tool

# 5. Test save endpoint (single line!)
curl -s -X POST http://localhost:8000/api/prompt/ -H "Content-Type: application/json" -d '{"content":"# Test Prompt\n\nThis is a test."}' | python3 -m json.tool

# 6. Test preview endpoint
curl -s http://localhost:8000/api/prompt/preview | python3 -m json.tool

# 7. Test reset endpoint
curl -s -X POST http://localhost:8000/api/prompt/reset | python3 -m json.tool

# 8. Check navigation has Prompt link
curl -s http://localhost:8000/ | grep -c "Prompt"
# Expected: >= 1

# 9. Check for errors
cat /tmp/phase5e-test.log | grep -i "error\|exception" | head -5

# 10. Stop server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

**Success criteria:**
- [ ] Prompt page renders with navigation
- [ ] GET /api/prompt/ returns current prompt with stats
- [ ] POST /api/prompt/ saves changes
- [ ] POST /api/prompt/reset restores default
- [ ] GET /api/prompt/preview shows rendered preview
- [ ] Navigation includes Prompt link
- [ ] No server errors

---

## Commit After Verification

```bash
git add -A
git commit -m "Phase 5E complete: Prompt editor UI

- Added prompt.html template with textarea editor
- Added prompt.py router with GET/POST/reset/preview endpoints
- Stats display (chars, words, lines)
- Preview with sample variable substitution
- Unsaved changes warning
- Navigation updated with Prompt link"
```

---

## Next Phase

After 5E is verified, proceed to **Phase 5F: APScheduler Integration** (final phase of Phase 5).
