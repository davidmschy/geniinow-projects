# Genii Studio - Development Roadmap

## COMPLETED ✅

### Core Infrastructure
- [x] FreeCAD 1.1.1 execution (bundled Python interpreter fix)
- [x] Address/APN lookup (Nominatim geocoding)
- [x] GIS elevation + slope analysis (OpenTopography SRTM 90m)
- [x] Site plan generator (FreeCAD with lot, setbacks, dwelling, utilities, contours)
- [x] STEP export for engineer collaboration
- [x] Integrated pipeline (Address → Geo → GIS → CAD → GitHub)
- [x] GitHub repo auto-creation with Git LFS for CAD files
- [x] Simple HTTP API server (port 8765)
- [x] System documentation (SYSTEM.md)

### Compliance & Quality
- [x] Compliance engine (HCD SHL 620, Title 24 CF1R, CALGreen Tier 1)
- [x] Civil plan ingestion (PDF → structured data)
- [x] GIS vs Civil discrepancy checker
- [x] 15 pipeline scripts operational

### Training Data Extracted
- [x] ESR-5318 (SIP structural specs, R-values)
- [x] ADU 20x32 6W 8R (53-sheet plan set, cutting panels, shop drawings)
- [x] Parkview civil Original (grading, drainage, elevations, setbacks)

## IN PROGRESS 🔄

### Collaboration
- [ ] Mattermost bot integration for plan notifications
- [ ] GitHub PR templates for engineer review
- [ ] Issue templates for plan corrections

### Data Sources
- [ ] FEMA flood zone lookup (currently 404 - need alternate endpoint)
- [ ] County parcel lookup (Fresno County GIS unresponsive)
- [ ] USGS 3DEP elevation (403 - using OpenTopography fallback)

### Plan Set Completeness
- [ ] Floor plan generator (architectural)
- [ ] Roof plan generator
- [ ] Elevation views (4 sides)
- [ ] Section views
- [ ] Electrical plan
- [ ] Plumbing plan
- [ ] Structural details
- [ ] T-24 CF1R-ENV calculation
- [ ] T-24 CF1R-PRF calculation

## BACKLOG 📋

### ERPNext Integration
- [ ] Auto-create Project from site plan generation
- [ ] Link modules to manufacturing BOMs
- [ ] Update manufacturing status from CAD output

### Manufacturing Output
- [ ] CNC cutting paths from SIP panels
- [ ] Shop drawing generation (per wall panel)
- [ ] Bill of Materials auto-generation
- [ ] Material takeoff quantities

### Advanced Features
- [ ] LM Studio integration for local LLM inference
- [ ] Vision pipeline (sketch → CAD parameters)
- [ ] EnergyPlus/OpenStudio T-24 compliance modeling
- [ ] Multi-family/duplex site plan support
- [ ] Solar PV readiness calculations
- [ ] HERS rater integration

### Team Agent Setup
- [ ] Per-employee AI agent instances
- [ ] Google Workspace integration for each agent
- [ ] ERPNext access for each agent
- [ ] GitHub accounts for each team member
- [ ] Mattermost channels per project
