# Weekly AI Sigint — launchd Service Setup

**Created**: 2026-01-13
**Purpose**: Install persistent macOS service for reliable weekly scheduled briefings
**Execute from**: `~/Dropbox/ALOMA/claude-code/weekly-ai-sigint/`
**Estimated Duration**: 5 minutes

---

## Prerequisites

Before executing, read best practices from:
```
~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md
```

---

## Step 1: Create the plist file

```bash
cat > ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aloma.weekly-ai-sigint</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /Users/pwilliamson/Dropbox/ALOMA/claude-code/weekly-ai-sigint &amp;&amp; source venv/bin/activate &amp;&amp; exec uvicorn app.main:app --host 127.0.0.1 --port 8000</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/pwilliamson/Dropbox/ALOMA/claude-code/weekly-ai-sigint</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/tmp/weekly-ai-sigint.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/weekly-ai-sigint.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Plist created"
```

---

## Step 2: Load the service

```bash
launchctl load ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
echo "✅ Service loaded"
```

---

## Step 3: Verify service is running

```bash
# Check launchd status
launchctl list | grep sigint

# Check process
sleep 3
lsof -i :8000

# Check health endpoint
curl -s http://localhost:8000/health | python3 -m json.tool

# Check scheduler status
curl -s http://localhost:8000/api/scheduler/status | python3 -c "
import sys, json
s = json.load(sys.stdin)
print('Running:', s.get('running'))
print('Paused:', s.get('paused'))
print('Next run:', s.get('next_run'))
print('Job count:', s.get('job_count'))
"
```

**Expected**: 
- Health returns `"status": "healthy"`
- Scheduler shows `running: True` with next Sunday 8:00 AM

---

## Useful Commands

**Check status:**
```bash
launchctl list | grep sigint
```

**View logs:**
```bash
tail -50 /tmp/weekly-ai-sigint.log
```

**Stop service (for development):**
```bash
launchctl unload ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
```

**Start service:**
```bash
launchctl load ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
```

**Restart service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
launchctl load ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
```

---

## Development Workflow

When you need to actively develop weekly-ai-sigint:

```bash
# 1. Stop launchd service
launchctl unload ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist

# 2. Run manually with --reload for hot reloading
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
source venv/bin/activate
uvicorn app.main:app --reload

# 3. When done, restart launchd service
launchctl load ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
```

---

## Uninstall (if needed)

```bash
launchctl unload ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
rm ~/Library/LaunchAgents/com.aloma.weekly-ai-sigint.plist
echo "✅ Service removed"
```
