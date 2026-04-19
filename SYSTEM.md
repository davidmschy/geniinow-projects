# Genii Studio - AI-Driven CAD/BIM Pipeline

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                               │
│  Address + APN  →  PDF/Sketch  →  Natural Language Prompt   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ AddressLookup│  │ GISLookup   │  │ CivilPlanIngestor   │ │
│  │ (Nominatim)  │  │ (SRTM/USGS) │  │ (PDF OCR → Schema)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              PROCESSING LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Compliance  │  │ SitePlan    │  │ Module Generator    │ │
│  │ Engine      │  │ Generator   │  │ (HCD Compliant)     │ │
│  │ (T24/HCD)   │  │ (FreeCAD)   │  │ (FreeCAD)           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  OUTPUT LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ FCStd       │  │ STEP        │  │ GitHub Repo         │ │
│  │ (Native)    │  │ (Engineers) │  │ (Collaboration)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Pipeline Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `GenerateSitePlan.py` | Full pipeline | Address/APN | FCStd + JSON + STEP |
| `FullPipeline.py` | One-command deploy | Address/APN | GitHub repo + compliance |
| `AddressLookup.py` | Geocode + metadata | Address or APN | Lat/Lon + County + Elevation |
| `GISLookup.py` | Terrain analysis | Lat/Lon | Slope + Flood + Parcel |
| `SitePlanGenerator.py` | CAD generation | Project JSON | FreeCAD document |
| `ComplianceEngine.py` | Code compliance | Project JSON | Compliance report |
| `CivilPlanIngestor.py` | PDF ingestion | Civil PDF | Structured data + discrepancies |
| `PlanSetPublisher.py` | GitHub publish | Project JSON | GitHub repo with LFS |
| `HCD_Module_Generator.py` | Module generation | Dimensions | Manufacturing files |

## Commands

### Generate a site plan from address:
```bash
python3 ~/geniinow-projects/macros/GenerateSitePlan.py \
  --address "549 N Parkview, Fresno, CA" \
  --apn "449-341-009" \
  --lot-width 100 --lot-depth 100
```

### Full pipeline (generate + compliance + GitHub):
```bash
python3 ~/geniinow-projects/macros/FullPipeline.py \
  --address "549 N Parkview, Fresno, CA" \
  --apn "449-341-009"
```

### Ingest a civil engineer's PDF:
```bash
python3 ~/geniinow-projects/macros/CivilPlanIngestor.py \
  --pdf /path/to/civil.pdf \
  --gis-data /path/to/project.json
```

### Check compliance:
```bash
python3 ~/geniinow-projects/macros/ComplianceEngine.py \
  --project-data /path/to/project.json
```

## Compliance Checks

### HCD SHL 620 (Factory-Built)
- [x] HCD insignia reference
- [x] Title 25 CCR §3070
- [x] Transport dimensions ≤ 16'
- [ ] Foundation/anchorage details (warning)
- [ ] Installation manual (warning)

### Title 24 CF1R (Energy)
- [x] Wall insulation ≥ R-21
- [x] Roof insulation ≥ R-30
- [ ] CF1R-ENV calculation (warning)
- [ ] CF1R-PRF calculation (warning)
- [ ] Solar readiness (warning)
- [ ] HERS rater (warning)

### CALGreen Tier 1
- [x] Compliance noted
- [ ] SWPPP (warning)
- [ ] Waste management plan (warning)

## Data Sources

| Source | Data | Status |
|--------|------|--------|
| Nominatim | Address → Lat/Lon | ✓ Working |
| USGS 3DEP | Elevation | ✗ 403 Forbidden |
| OpenTopography | SRTM 90m Elevation | ✓ Working |
| FEMA | Flood zones | ✗ 404 |
| Fresno County GIS | Parcels | ✗ No response |

## Training Data Catalog

| PDF | Sheets | Type | Extracted |
|-----|--------|------|-----------|
| `ESR-5318 .pdf` | 30+ | SIP Structural | ✓ Specs, R-values |
| `ADU_20X32 6W 8R.pdf` | 53 | Plan Set | ✓ Sheet index, cutting panels |
| `Parkview_civil_Original_lot1.pdf` | 1 | Civil/Site | ✓ Elevations, drainage, setbacks |
| `Parkview_needs_stamp_lot1.pdf` | 1 | Civil/Site | - Pending |
| `apServant - Clients (1).pdf` | 10 | Architectural | - Partial |

## GitHub Repos

Generated repos follow naming: `site-plan-{apn}`
Example: https://github.com/davidmschy/site-plan-449_341_009

## Next Steps

1. [ ] Add CF1R-ENV/PRF energy calculation integration
2. [ ] Add solar readiness checks
3. [ ] Integrate with ERPNext project creation
4. [ ] Build Mattermost bot for plan notifications
5. [ ] Add FEMA flood zone lookup (fix 404)
6. [ ] Add county parcel lookup (fix no response)
7. [ ] Build floor plan generator (not just site plan)
8. [ ] Build elevation/section generator
9. [ ] Integrate with EnergyPlus for T-24 compliance
10. [ ] Add LM Studio integration for local LLM inference
