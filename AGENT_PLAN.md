# Genii Studio - Agent Architecture Plan

## Objective
Deploy 10 AI agents (1 per team member + shared service agents), each with:
- Google Workspace access (Gmail, Calendar, Drive, Sheets)
- ERPNext access (project-specific data)
- GitHub access (repo management, PR review)
- Mattermost access (team communication)
- Local LLM access (LM Studio for cost control)

## Team Agent Mapping

| # | Agent | Role | Primary Tools | ERPNext Access | GWS Access |
|---|-------|------|---------------|----------------|------------|
| 1 | **David** | CEO/Dealmaker | All | Full admin | Full admin |
| 2 | **Amber** | Business Manager | ERPNext, GWS, Mattermost | Full | Full |
| 3 | **Robert** | Draftsman/Facility | CAD, GitHub, ERPNext | Projects | Drive/Sheets |
| 4 | **Tony** | Labor/Project Coord | ERPNext, Mattermost, Calendar | Projects | Calendar/Drive |
| 5 | **John** | Land/Broker | GWS, ERPNext, Maps | Land acq | Gmail/Calendar |
| 6 | **Mark** | Realtor/Modular | GWS, ERPNext, CRM | Sales | Gmail/Calendar |
| 7 | **Aryan** | Accountant/CFO | ERPNext, GWS Sheets | Full financial | Sheets/Drive |
| 8 | **Antonio** | QC/Facility | ERPNext, CAD, GitHub | QC/Compliance | Drive |
| 9 | **Syed** | Software Engineer | GitHub, ERPNext, API | System admin | Drive |
| 10 | **Shared** | Pipeline/Automation | CAD, GitHub, ERPNext | All projects | Service acct |

## Authentication Strategy

### Google Workspace (Pipedream/GSA - Non-expiring)
- Use Google Service Account with domain-wide delegation
- Each agent gets scoped credentials:
  - David/Amber: Full domain admin
  - Robert/Antonio: Drive + Sheets (CAD files)
  - John/Mark: Gmail + Calendar (client-facing)
  - Aryan: Sheets + Drive (financial)
  - Tony: Calendar + Drive (scheduling)
  - Syed: Drive + Admin SDK (system)

### ERPNext (API Key per agent)
- Create ERPNext User for each agent
- Generate API Key/Secret per user
- Role-based permissions:
  - Project Manager: Create/modify projects
  - Accountant: Financial doctypes only
  - Engineer: BOM, manufacturing status
  - Sales: Customer, lead, opportunity

### GitHub (Personal Access Token or App)
- Option A: GitHub App (recommended)
  - Single app, OAuth per user
  - Scoped to repos needed
- Option B: Fine-grained PAT per agent
  - `repo` scope for engineers
  - `read:org` for managers

### Mattermost (Bot Account)
- Create bot account: `@genii-bot`
- Personal Access Token with `post:all` permission
- Each agent can post to relevant channels

### LM Studio (Local)
- Running on Mac Studio at `http://127.0.0.1:1234`
- Models: `gemma-4-e4b`, `nemotron-3-nano`, `qwen2.5`
- All agents route to local LLM for:
  - Text generation (free)
  - Code review (free)
  - Cost savings vs paid APIs

## Deployment Model

### Option 1: PM2 Daemon (Recommended)
Each agent runs as a persistent Node.js/Python process managed by PM2:

```bash
# Agent config example (pm2 ecosystem)
module.exports = {
  apps: [
    { name: 'agent-david', script: 'agent.js', env: { ROLE: 'ceo' } },
    { name: 'agent-robert', script: 'agent.js', env: { ROLE: 'draftsman' } },
    { name: 'agent-aryan', script: 'agent.js', env: { ROLE: 'cfo' } },
    ...
  ]
}
```

### Option 2: Docker Container per Agent
- More isolation
- Higher resource overhead
- Better for conflicting dependencies

### Option 3: Serverless (Vercel/Modal)
- Spin up on demand
- Lower cost for intermittent use
- Cold start latency

**Recommendation:** PM2 for now (macOS native, fast, proven)

## Data Flow

```
User Request (David)
    ↓
Router Agent (determines which agent handles it)
    ↓
Specialist Agent (Robert for CAD, Aryan for finance)
    ↓
Tool Calls (ERPNext, GWS, GitHub, CAD)
    ↓
Response + Action Log
    ↓
Mattermost notification (if relevant)
    ↓
GitHub commit (if plan changes)
```

## GitHub Repository Strategy

### Per-Project Repos
- Naming: `{project-type}-{apn}-{city-slug}`
- Examples:
  - `site-plan-449-341-009-fresno`
  - `mfg-module-parkview-lot9`
  - `sales-lead-1234-elmhurst`
- Contents:
  - `plans/` - CAD files (Git LFS)
  - `docs/` - Compliance docs, calculations
  - `data/` - JSON schemas, GIS data
  - `src/` - Code, scripts

### Shared Repos
- `geniinow-projects/` - Core pipeline code (this repo)
- `training-data/` - Plan sets, reference PDFs
- `compliance/` - Title 24, CALGreen templates

## Obsidian Workflow

### Vault Structure
```
~/obsidian-geniinow/
├── 00-Inbox/           # New ideas, raw notes
├── 01-Projects/        # One note per project
│   ├── 449-341-009.md
│   └── parkview-lot9.md
├── 02-People/          # Team member profiles
│   ├── David.md
│   ├── Robert.md
│   └── ...
├── 03-Processes/       # SOPs, checklists
│   ├── site-plan-generation.md
│   └── compliance-checklist.md
├── 04-Reference/       # Extracted PDF data
│   ├── ESR-5318.md
│   └── SIP-specs.md
├── 05-Daily/           # Daily standup notes
└── 99-Archive/         # Completed projects
```

### Integration
- Agent outputs auto-synced to Obsidian vault
- Daily standup generated from ERPNext + Calendar
- Project notes linked to GitHub repos
- Compliance reports saved as project notes

## Local Model Setup (LM Studio)

### Current Status
- **Host:** `http://127.0.0.1:1234`
- **Primary:** `gemma-4-e4b` (best for reasoning)
- **Fast:** `qwen2.5:1.5b` (quick tasks)
- **Embeddings:** `nomic-embed-text` (RAG)

### Cost Savings
| Task | OpenAI Cost | Local Cost | Savings |
|------|-------------|------------|---------|
| Code review | $0.03/1K tok | $0 | 100% |
| Text generation | $0.01/1K tok | $0 | 100% |
| Embedding | $0.10/1M tok | $0 | 100% |
| Complex reasoning | $0.06/1K tok | $0 | 100% |

### Routing Logic
```python
if task_complexity == "high" and local_model_capable:
    use_local()
elif task_requires_vision:
    use_openai()  # gpt-4o
else:
    use_local()  # default
```

## Claude Code / Codex / OpenCode / Kimi

### Tool Selection Matrix
| Tool | Best For | Integration |
|------|----------|-------------|
| **Claude Code** | Complex refactoring, architecture | ACP CLI agent |
| **Codex** | Quick fixes, feature impl | OpenAI CLI |
| **OpenCode** | Budget coding, fast iteration | Local agent |
| **Kimi** | Long context (2M tokens) | CLE integration |

### Usage Strategy
- **Claude Code:** Monthly subscription, used for major architectural work
- **Codex:** Pay-per-use, used for quick feature additions
- **OpenCode:** Free tier, used for routine maintenance
- **Kimi:** When you need to ingest massive codebases (2M context)

## Implementation Order

### Phase 1: Foundation (This Week)
1. [ ] Create ERPNext user accounts for all 10 agents
2. [ ] Generate API keys and store in 1Password/Keychain
3. [ ] Set up Google Service Account with domain-wide delegation
4. [ ] Create GitHub App or PATs per agent
5. [ ] Configure Mattermost bot account

### Phase 2: Agent Deployment (Next Week)
1. [ ] Deploy PM2 daemon for each agent
2. [ ] Test ERPNext connectivity per agent
3. [ ] Test GWS connectivity per agent
4. [ ] Test GitHub connectivity per agent
5. [ ] Test Mattermost posting

### Phase 3: Workflow Integration (Week 3)
1. [ ] Agent receives project request → creates ERPNext project
2. [ ] Agent generates site plan → publishes to GitHub
3. [ ] Agent notifies team → Mattermost
4. [ ] Agent schedules review → Google Calendar
5. [ ] Agent tracks status → ERPNext updates

### Phase 4: Advanced Features (Month 2)
1. [ ] Vision pipeline (sketch → CAD)
2. [ ] T-24 energy modeling (EnergyPlus)
3. [ ] CNC path generation from SIP panels
4. [ ] Multi-agent collaboration (parallel work)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Agent makes destructive change | Sandboxed execution, approval gates |
| Rate limits on APIs | Local LLM fallback, caching |
| Credential exposure | 1Password integration, rotate quarterly |
| Conflict between agents | Central router, locking mechanism |
| Cost overruns | Local LLM default, paid API quotas |

## Success Metrics

- [ ] 10 agents operational by end of week 2
- [ ] Site plan generated in < 5 minutes end-to-end
- [ ] Compliance score > 90% on all plans
- [ ] Engineer review cycle < 3 days
- [ ] Zero manual data entry (ERPNext auto-populated)
