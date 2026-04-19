# Collaborative CAD Workflow Plan

## Goal
Multiple team members + third-party engineers work on plan sets together until submit-ready.

## Architecture

### 1. Communication Hub — Mattermost (chat.geniinow.com)
- Channels per project: `#site-plan-449-341-009`
- Channels per discipline: `#civil`, `#structural`, `#architectural`, `#hcd`
- Bot integration: AI agents post plan updates, engineers comment, approvals tracked

### 2. Version Control — GitHub
- Repo per project: `davidmschy/site-plan-<apn>`
- Git LFS for `.FCStd`, `.stp`, `.dwg` files
- Branch per discipline: `civil/grading`, `structural/foundation`, `architectural/floor-plan`
- PR workflow: Engineer submits changes → review → merge → trigger CI

### 3. Project Tracking — ERPNext
- Project linked to plan set
- Tasks per sheet: `A1.0 Cover Sheet`, `Site Plan`, `T-24`, etc.
- Status workflow: Draft → In Review → Engineer Approved → Submitted
- BOM integration for material takeoffs

### 4. CAD Generation — FreeCAD + Blender
- Base site plan generated from APN/address + sketch input
- Engineers pull repo, open in FreeCAD, make edits
- Real-time: VNC/remote desktop for pair review (cad.geniinow.com)
- Output: `.stp` for manufacturing, `.pdf` for submission

### 5. Human Interface — Obsidian
- Living documentation per project
- Meeting notes, decisions, change orders
- Links to ERPNext tasks, GitHub PRs, Mattermost threads

## Input → Output Pipeline

```
User Input (APN + sketch description)
  ↓
Address Lookup → Lot dims, zoning, utilities
  ↓
Sketch Parser → Dwelling type, dims, unit mix, setbacks
  ↓
Reference Plan Matching → Similar APN patterns from training data
  ↓
Schema Generation → Structured project.json
  ↓
CAD Generation → FreeCAD site plan + sheet index
  ↓
Collaboration Loop → Engineers review in Mattermost + edit in FreeCAD
  ↓
Compliance Check → Title 24, CalGreen, HCD SHL 620
  ↓
Submit Package → PDFs, STPs, signed cover sheets
```

## Next Steps
1. [ ] Build address/APN lookup integration (county assessor APIs)
2. [ ] Build sketch-to-schema parser (text or image input)
3. [ ] Integrate Git LFS for CAD file versioning
4. [ ] Create Mattermost bot for plan notifications
5. [ ] Build compliance checklist engine
