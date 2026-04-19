# Plan Set Generator Framework
## Goal: Generate HCD-permit-ready plan sets from text prompts or reference images

---

## Input Types
1. **Text prompt**: "20x32 2-bed 2-bath duplex, 2-story, SIP construction, Hanford CA"
2. **Reference PDF**: Existing plan set to replicate style/compliance from
3. **Reference image**: Sketch, photo, or partial drawing to base design on

## Output: Complete 11-Sheet Plan Set

| Sheet | Code | Description | Auto-Gen Method |
|-------|------|-------------|-----------------|
| A0.0 | LEGEND | Abbreviations, symbols, general notes | Template + project-specific additions |
| A1.0 | PLANS | Floor plans, roof plan, 4 elevations | FreeCAD 2D drawing from 3D model |
| E1.0 | ELECTRICAL | Electrical notes, panel schedules, lighting plan | Rule-based from room layout + CA code |
| P1.0 | PLUMBING | Plumbing notes, fixture schedule, riser diagram | Rule-based from room layout + CA code |
| A2.0 | DETAILS | Stairs, decks, guardrails, connections | Parametric detail library |
| S1.0 | MODULAR | Module separation plans, transport dims | FreeCAD from module split logic |
| S2.0 | WALLS | SIP wall panel details, sections | Parametric from wall spec |
| S3.0 | ROOF | SIP roof panel details, flashing | Parametric from roof spec |
| T24-1 | ENERGY | Title 24 CF1R compliance forms | CBECC/OpenStudio automation |
| T24-2 | HERS | HERS rating, duct test, infiltration | Rule-based from envelope spec |
| CG1.0 | CALGREEN | Mandatory measures checklist | Rule-based from scope |

---

## Architecture

```
User Input (prompt/image/PDF)
    |
    v
[Intent Parser] --> Extract: bedrooms, baths, stories, lot, jurisdiction
    |
    v
[Module Designer] --> Split into transportable modules (max 16' width)
    |
    v
[FreeCAD Modeler] --> Generate 3D parametric model (SIP + steel floor)
    |
    v
[Sheet Generator] --> Render each sheet from model + templates
    |
    v
[Compliance Engine] --> Title 24, CALGreen, HCD forms
    |
    v
[Output Assembler] --> Combined PDF with sheet index
```

---

## FreeCAD Drawing Templates

Title block must include:
- Project name, address, jurisdiction
- Designer (PreFab Innovations style or user-specified)
- Sheet number, scale, date
- Revision block
- HCD approval stamp area

---

## Parametric Detail Library

Pre-built details for:
- SIP wall section (8" panel, OSB skins, EPS core, gypsum both sides)
- SIP roof section (with fascia, flashing, standing seam option)
- SIP floor section (TJI + 6" SIP + subfloor)
- Module connection detail (butt joint, spline, fastening schedule)
- Stair section (guardrail, handrail, tread/riser dims)
- Deck detail (DEX-O-TEX or equivalent, drainage, flashing)
- Stucco system (3-coat, lath, building paper, Tyvek)
- Window/door head/jamb/sill details

---

## Compliance Automation

### Title 24 Performance Method
- Input: Envelope specs (SIP R-values, window U-factors, SHGC)
- Input: HVAC specs (RTU efficiency, duct location)
- Input: Water heating (tankless vs tank, EF rating)
- Output: CF1R-PRF-01E form
- Tool: OpenStudio + CEC measures (CBECC is Windows-only)

### CALGreen
- Checklist generation based on project scope
- Auto-fill mandatory measures references
- Output: HCD SHL 620 forms

### HCD
- Factory-built housing compliance checklist
- SHL 620 form generation
- Transport width/height verification

---

## Reference Plan Ingestion

### From PDF:
1. OCR text (done — tesseract installed)
2. Extract dimensions with regex patterns
3. Detect sheet types by content classification
4. Store in GBrain as reference template

### From Image:
1. OCR text
2. Detect walls, doors, windows with CV
3. Scale calibration from dimension strings
4. Vectorize to FreeCAD sketch

---

## Next Implementation Steps

1. **Create FreeCAD drawing templates** (A-size, title block, scale)
2. **Build parametric detail library** (SIP wall, roof, floor, connection)
3. **Create sheet generators** (floor plan, elevation, section renderers)
4. **Integrate compliance engine** (OpenStudio + forms)
5. **Build prompt parser** (extract design intent)
6. **Add reference plan ingestion** (PDF/image → structured data)
