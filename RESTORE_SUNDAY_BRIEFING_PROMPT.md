# Restore Sunday Briefing Prompt

**Created**: 2026-01-13
**Purpose**: Restore the original comprehensive prompt that was overwritten
**Execute from**: `~/Dropbox/ALOMA/claude-code/weekly-ai-sigint/`
**Estimated Duration**: 2 minutes

---

## Prerequisites

Before executing, read best practices from:
```
~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md
```

---

## Step 1: Backup Current Prompt

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
cp prompts/sunday_briefing.md prompts/sunday_briefing.md.backup
echo "✅ Backup created"
```

---

## Step 2: Restore Original Prompt

```bash
cat > prompts/sunday_briefing.md << 'EOF'
# Sunday Briefing Pack — Synthesis Prompt

## ROLE
You are my weekly AI and enterprise tech intelligence analyst.

## GOAL
Using the content I provide, produce a complete "Sunday Briefing Pack" covering the last 7 days, so I can speak credibly about what changed and why it matters.

## TIME WINDOW
- Primary: last 7 days from today.
- Secondary: include older items only if they became newly relevant this week (example: a regulation entering into force, a delayed security disclosure, a major model now generally available).

## WORKING RULES (IMPORTANT)
- Every claim must have a link. Provide the primary source link first, then one reputable secondary analysis link if useful.
- Deduplicate stories across sources.
- Prioritise: concrete releases, benchmarks, pricing, enterprise deployments, funding, regulation changes, security incidents, chip supply, and credible research.
- Be sceptical. Flag hype, unclear claims, and marketing language.
- If sources contradict, present both sides and state what is known vs unknown.

## OUTPUT FORMAT (STRICT, MARKDOWN)

### 1) Executive Brief (10 bullets max)
The 10 most important updates this week, each with:
- One-line summary
- Why it matters (1 line)
- Primary source link
- Topic tag

### 2) Thematic Digest (sections, ordered)

#### A) Enterprise AI Transformation
5–12 items. Focus on adoption patterns, operating models, governance, ROI, implementation lessons, case studies.

#### B) Models and Labs
5–12 items. New releases, evals, capability changes, pricing, API changes, open weights, safety updates.

#### C) Chips, Cloud, and Infrastructure
5–12 items. GPU/accelerator news, datacentre scaling, inference optimisation, networking, memory, cost curves.

#### D) Startups and Funding
5–12 items. Funding rounds, notable product launches, acquisitions. Include deal size and investors if available.

#### E) Research Papers and Benchmarks
5–12 items. For each:
- Paper title
- 2–3 sentence plain-English summary
- What changed vs prior work
- Link (arXiv/official)
- "Worth reading?" score (High/Medium/Low) based on practical impact

#### F) Regulation, Policy, and Standards
3–10 items. Focus on what changes obligations, risk, procurement, or model deployment.

#### G) Security, Safety, and Reliability
3–10 items. Incidents, advisories, exploit writeups, jailbreak trends, guardrail failures, mitigations.

### 3) People Activity Digest
From tracked sources: top posts or publications this week.
10–25 items max.

---

## CONTENT TO SYNTHESIZE

{{CONTENT}}
EOF

echo "✅ Prompt restored"
```

---

## Step 3: Verify

```bash
cat prompts/sunday_briefing.md | head -30
wc -w prompts/sunday_briefing.md
```

**Expected**: ~400 words, full structured prompt

---

## Step 4: Test Pipeline

```bash
curl -s -X POST http://localhost:8000/api/scheduler/run-now | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Success:', d.get('success'))
print('Briefing ID:', d.get('steps', {}).get('synthesize', {}).get('briefing_id'))
"
```

---

## Step 5: Check Slack Output

After the pipeline runs, verify Slack receives a properly structured briefing with:
- Executive Brief section
- Thematic Digest sections (A through G)
- Proper formatting
