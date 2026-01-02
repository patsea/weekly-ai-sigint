# Restructure claude-auto v2.5 - Fast Start with Background Checks

**Created**: January 2, 2026  
**Purpose**: Restructure claude-auto to start Claude Code immediately, run checks in background  
**Execute from**: `~/Dropbox/ALOMA/claude-code/`  
**Estimated Duration**: 20-25 minutes

---

⚠️ **IMPORTANT**: This file MUST be executed from `~/Dropbox/ALOMA/claude-code/`

---

## Prerequisites

Before executing, read best practices from:
```
~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md
```

---

## Architecture Change

### Current Sequence (v2.4) - Slow Start
```
1. Set directory
2. Run preflight checks (security scan) ← BLOCKING
3. Clear caches ← BLOCKING  
4. Check/start each service ← BLOCKING
5. Wait for services ready ← BLOCKING
6. Open webpages
7. Start Claude Code
```
**Problem**: 30-60+ seconds before Claude Code starts

### New Sequence (v2.5) - Fast Start
```
1. Set directory
2. Source best practices location
3. START CLAUDE CODE IMMEDIATELY (--dangerously-skip-permissions)
4. Background job: preflight checks, services, git status
5. Push summary to log file Claude Code can read
```
**Result**: Claude Code starts in <5 seconds

---

## Part A: Create New claude-auto v2.5

### A.1 Backup Current Version

```bash
cd ~/Dropbox/ALOMA/claude-code/claude-auto-launcher

# Backup v2.4
cp bin/claude-auto bin/claude-auto.v2.4.backup
cp lib/helpers.sh lib/helpers.sh.v2.4.backup

echo "✓ Backed up v2.4"
```

### A.2 Create New claude-auto v2.5 Script

```bash
cd ~/Dropbox/ALOMA/claude-code/claude-auto-launcher

cat > bin/claude-auto << 'SCRIPT_EOF'
#!/bin/bash
# Claude Code Enhanced Launcher - FAST START Edition
# Version: 2.5
# Last Updated: January 2, 2026
#
# This script:
# 1. Sets working directory
# 2. Starts Claude Code IMMEDIATELY
# 3. Runs all checks in background
# 4. Writes status to log file for review

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(dirname "$SCRIPT_DIR")/lib"

# Source helper functions
source "$LIB_DIR/helpers.sh"

# Configuration
CCODE_DIR="${CLAUDE_CODE_DIR:-$HOME/Dropbox/ALOMA/claude-code}"
BEST_PRACTICES="$CCODE_DIR/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md"
BACKGROUND_LOG="/tmp/claude-auto-background.log"

# Fast banner
fast_banner() {
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        Claude Code Enhanced Launcher v2.5 (Fast)         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
}

# Background checks function - outputs to screen via tee
run_background_checks() {
    local log="$BACKGROUND_LOG"
    
    # Use tee to write to BOTH log file AND screen (stderr so it shows during Claude Code)
    {
        echo ""
        echo "┌──────────────────────────────────────────────────────────┐"
        echo "│  BACKGROUND CHECKS                                       │"
        echo "└──────────────────────────────────────────────────────────┘"
        
        # Quick service status (most important)
        echo ""
        echo "Services:"
        for port in 8001 5173 3001 3000; do
            case $port in
                8001) name="Backend API" ;;
                5173) name="LLM Council" ;;
                3001) name="Workflow Gen" ;;
                3000) name="Workflow Auto" ;;
            esac
            if lsof -i ":$port" -sTCP:LISTEN > /dev/null 2>&1; then
                echo "  ✓ $name (port $port)"
            else
                echo "  ✗ $name (port $port) - NOT RUNNING"
            fi
        done
        
        # Git status (brief)
        echo ""
        echo "Git:"
        cd "$CCODE_DIR"
        for repo in claude-auto-launcher llm-council weekly-ai-sigint workflow-automation vibe-coding-utilities; do
            if [ -d "$repo/.git" ]; then
                cd "$repo"
                local status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
                local unpushed=$(git log @{u}.. --oneline 2>/dev/null | wc -l | tr -d ' ')
                if [ "$status" -gt 0 ] || [ "$unpushed" -gt 0 ]; then
                    echo "  ⚠️  $repo: $status uncommitted, $unpushed unpushed"
                else
                    echo "  ✓ $repo"
                fi
                cd "$CCODE_DIR"
            fi
        done
        
        # Security scan (can be slow, show last)
        echo ""
        echo "Security scan..."
        cd "$CCODE_DIR"
        local scan_result=$(check_sensitive_data "$CCODE_DIR" 2>&1)
        if echo "$scan_result" | grep -q "SENSITIVE DATA DETECTED"; then
            echo "  ⚠️  Sensitive data warnings - review before committing"
        else
            echo "  ✓ No sensitive data in staged files"
        fi
        
        echo ""
        echo "────────────────────────────────────────────────────────────"
        
    } 2>&1 | tee -a "$log" >&2
}

# Start services function (background) - outputs to screen
start_services_background() {
    local log="$BACKGROUND_LOG"
    
    {
        echo ""
        echo "Starting services in background..."
        
        cd "$CCODE_DIR"
        
        # Backend API (port 8001)
        if ! lsof -i :8001 -sTCP:LISTEN > /dev/null 2>&1; then
            cd "$CCODE_DIR/llm-council"
            if [ -d ".venv" ]; then
                source .venv/bin/activate
                python -m backend.main > /tmp/llm-council-backend.log 2>&1 &
            else
                uv run python -m backend.main > /tmp/llm-council-backend.log 2>&1 &
            fi
            echo "  → Backend API starting..."
        fi
        
        # Frontend (port 5173)
        if ! lsof -i :5173 -sTCP:LISTEN > /dev/null 2>&1; then
            cd "$CCODE_DIR/llm-council/frontend"
            npm run dev > /tmp/llm-council-frontend.log 2>&1 &
            echo "  → LLM Council Frontend starting..."
        fi
        
        # Workflow Generator (port 3001)
        if ! lsof -i :3001 -sTCP:LISTEN > /dev/null 2>&1; then
            cd "$CCODE_DIR/vibe-coding-utilities/workflow-generator"
            PORT=3001 npm start > /tmp/workflow-generator.log 2>&1 &
            echo "  → Workflow Generator starting..."
        fi
        
        # Workflow Automation (port 3000)
        if ! lsof -i :3000 -sTCP:LISTEN > /dev/null 2>&1; then
            cd "$CCODE_DIR/workflow-automation"
            pnpm dev > /tmp/workflow-automation.log 2>&1 &
            echo "  → Workflow Automation starting..."
        fi
        
    } 2>&1 | tee -a "$log" >&2
}

main() {
    fast_banner
    
    # Change to claude-code directory
    cd "$CCODE_DIR" || {
        echo "Error: Cannot access $CCODE_DIR"
        exit 1
    }
    echo ""
    echo "✓ Directory: $(pwd)"
    echo "✓ Best Practices: $BEST_PRACTICES"
    
    # Start background checks and services (output will appear on screen)
    run_background_checks &
    start_services_background &
    
    echo ""
    echo "Starting Claude Code..."
    echo ""
    
    # Start Claude Code immediately
    claude --dangerously-skip-permissions
}

main "$@"
SCRIPT_EOF

chmod +x bin/claude-auto
echo "✓ Created claude-auto v2.5"
```

### A.3 Update helpers.sh Version

```bash
cd ~/Dropbox/ALOMA/claude-code/claude-auto-launcher

# Update version in helpers.sh
sed -i '' 's/# Version: 2.4/# Version: 2.5/' lib/helpers.sh

echo "✓ Updated helpers.sh version"
```

### A.4 Install to ~/.claude-auto/

```bash
cd ~/Dropbox/ALOMA/claude-code/claude-auto-launcher

# Copy to installed location
cp bin/claude-auto ~/.claude-auto/bin/claude-auto
cp bin/claude-auto-stop ~/.claude-auto/bin/claude-auto-stop
cp bin/claude-auto-status ~/.claude-auto/bin/claude-auto-status
cp lib/helpers.sh ~/.claude-auto/lib/helpers.sh

echo "✓ Installed to ~/.claude-auto/"
```

### A.5 Verify Installation

```bash
# Check versions
echo "=== Installed Versions ==="
grep "Version" ~/.claude-auto/bin/claude-auto | head -1
grep "Version" ~/.claude-auto/lib/helpers.sh | head -1
```

---

## Part B: Update Documentation

### B.1 Update CLAUDE_AUTO_LAUNCHER.md

Add to `~/Dropbox/ALOMA/claude-code/CLAUDE_AUTO_LAUNCHER.md`:

```markdown
### January 2, 2026 (v2.5)
- ✅ **Fast Start architecture** — Claude Code starts immediately (<5 seconds)
- ✅ All checks run in background (security scan, git status, service health)
- ✅ Services start in background without blocking
- ✅ Status available via `cat /tmp/claude-auto-status.log`
- ✅ Full logs via `cat /tmp/claude-auto-background.log`
- ✅ No more waiting 30-60 seconds for checks before coding
```

### B.2 Update Best Practices Version to 1.21

```bash
cd ~/Dropbox/ALOMA/claude-code

sed -i '' 's/\*\*Version\*\*: 1.20/**Version**: 1.21/' CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md
```

### B.3 Add Changelog Entry

Add to Best Practices changelog:

```markdown
| 2026-01-02 | 1.21 | Documented claude-auto v2.5 Fast Start architecture. Claude Code now starts immediately, all checks run in background. |
```

---

## Part C: Test New Architecture

### C.1 Stop Current Services

```bash
claude-auto-stop
```

### C.2 Test Fast Start

```bash
cd ~/Dropbox/ALOMA/claude-code

# Time the new claude-auto
time claude-auto

# (Claude Code should start within 5 seconds)
# Background checks will continue running
```

### C.3 Background Output

```bash
# Background check results will appear on your screen
# while Claude Code is running (via stderr)
# No need to cat a log file!
```

---

## Part D: Verification

### D.1 Verify Fast Start

```bash
# Claude Code should start in <5 seconds
# Background checks should appear on screen within 10-20 seconds
# Services should be available shortly after

# Check services are running:
claude-auto-status
```

### D.2 Verify Logs (if needed)

```bash
# Background log is still saved for debugging
cat /tmp/claude-auto-background.log
```

### D.3 Verify Services

```bash
claude-auto-status
```

---

## Completion Checklist

- [ ] Part A.1: Backed up v2.4
- [ ] Part A.2: Created claude-auto v2.5
- [ ] Part A.3-A.4: Updated helpers, installed to ~/.claude-auto/
- [ ] Part A.5: Verified versions
- [ ] Part B: Updated documentation
- [ ] Part C: Tested fast start
- [ ] Part D: All verifications pass

---

## Rollback (if needed)

```bash
cd ~/Dropbox/ALOMA/claude-code/claude-auto-launcher

# Restore v2.4
cp bin/claude-auto.v2.4.backup bin/claude-auto
cp lib/helpers.sh.v2.4.backup lib/helpers.sh
cp bin/claude-auto ~/.claude-auto/bin/claude-auto
cp lib/helpers.sh ~/.claude-auto/lib/helpers.sh

echo "✓ Rolled back to v2.4"
```

---

## Expected Behavior After Update

```
$ claude-auto
╔══════════════════════════════════════════════════════════╗
║        Claude Code Enhanced Launcher v2.5 (Fast)         ║
╚══════════════════════════════════════════════════════════╝

✓ Directory: /Users/pwilliamson/Dropbox/ALOMA/claude-code
✓ Best Practices: .../CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md

Starting Claude Code...

 * ▐▛███▜▌ *   Claude Code v2.0.76
* ▝▜█████▛▘ *  ...

[Background output appears on screen while using Claude Code:]

┌──────────────────────────────────────────────────────────┐
│  BACKGROUND CHECKS                                       │
└──────────────────────────────────────────────────────────┘

Services:
  ✓ Backend API (port 8001)
  ✓ LLM Council (port 5173)
  ✓ Workflow Gen (port 3001)
  ✓ Workflow Auto (port 3000)

Git:
  ✓ claude-auto-launcher
  ⚠️  llm-council: 2 uncommitted, 0 unpushed
  ✓ weekly-ai-sigint
  ✓ workflow-automation
  ✓ vibe-coding-utilities

Security scan...
  ✓ No sensitive data in staged files

────────────────────────────────────────────────────────────
```

**Time to Claude Code**: <5 seconds
**Background checks**: Appear on screen as they complete (10-20 seconds)

---

**End of Instructions**
