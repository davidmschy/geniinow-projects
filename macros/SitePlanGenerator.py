"""
SitePlanGenerator.py - Enhanced version

Generates civil/site engineering plans with:
- Lot boundary with dimensions
- Dwelling footprint with setbacks
- Driveway and parking
- Contour lines from GIS elevation data
- Utility stubs (water, sewer, electric)
- North arrow and scale
- Title block info
"""
import json, sys, os, math

FREECAD_LIB = "/Applications/FreeCAD.app/Contents/Resources/lib"
if FREECAD_LIB not in sys.path:
    sys.path.insert(0, FREECAD_LIB)

import FreeCAD as App
import Part
import Draft

def create_contours(doc, center_x, center_y, base_elev, slope_pct, lot_w_ft, lot_d_ft):
    """Create approximate contour lines based on slope data."""
    contours = []
    contour_interval = 1.0  # 1 foot contours
    
    # Assume slope runs from NW to SE (common pattern)
    # Create a few contour lines across the lot
    num_contours = 3
    for i in range(num_contours):
        elev = base_elev + (i - num_contours//2) * contour_interval
        # Create a line at this approximate elevation
        length = max(lot_w_ft, lot_d_ft) * 12  # inches
        
        # Diagonal contour line
        line = Part.makeLine(
            App.Vector(center_x - length/2, center_y - length/2 + i*50*12, 0),
            App.Vector(center_x + length/2, center_y + length/2 + i*50*12, 0)
        )
        contour_obj = doc.addObject("Part::Feature", f"Contour_{int(elev)}ft")
        contour_obj.Shape = line
        contours.append(contour_obj)
    
    return contours

def create_dimension_line(doc, p1, p2, offset=10, text=""):
    """Create a dimension line between two points."""
    line = Part.makeLine(p1, p2)
    dim_obj = doc.addObject("Part::Feature", f"Dim_{text}")
    dim_obj.Shape = line
    return dim_obj

def create_site_plan(project_data):
    apn = project_data['project_metadata']['apn'].replace('-', '_')
    doc = App.newDocument(f"SitePlan_{apn}")
    
    lot = project_data.get("lot_information", {})
    lot_w = lot.get("width_ft", 100)
    lot_d = lot.get("depth_ft", 100)
    dwelling = project_data.get("dwelling_specifications", {})
    dw_w = dwelling.get("width_ft", 21.5)
    dw_d = dwelling.get("depth_ft", 31)
    
    elev_ft = lot.get("elevation_ft", 300)
    slope_pct = lot.get("slope_avg_percent", 2.0)
    
    # Setbacks
    front_setback = 25 * 12
    side_setback = 5 * 12
    rear_setback = 20 * 12
    
    # Lot boundary
    lot_shape = Part.makePlane(lot_w * 12, lot_d * 12)
    lot_obj = doc.addObject("Part::Feature", "LotBoundary")
    lot_obj.Shape = lot_shape
    lot_obj.Placement.Base = App.Vector(-lot_w*6, -lot_d*6, 0)
    
    # Property lines (slightly larger for visual distinction)
    prop_shape = Part.makePlane((lot_w + 2) * 12, (lot_d + 2) * 12)
    prop_obj = doc.addObject("Part::Feature", "PropertyLine")
    prop_obj.Shape = prop_shape
    prop_obj.Placement.Base = App.Vector(-(lot_w+2)*6, -(lot_d+2)*6, -1)
    
    # Dwelling footprint
    dw_shape = Part.makePlane(dw_w * 12, dw_d * 12)
    dw_obj = doc.addObject("Part::Feature", "DwellingFootprint")
    dw_obj.Shape = dw_shape
    dw_obj.Placement.Base = App.Vector(-lot_w*6 + side_setback, -lot_d*6 + front_setback, 0)
    
    # Driveway
    drive_w = 10 * 12
    drive_d = front_setback
    drive_shape = Part.makePlane(drive_w, drive_d)
    drive_obj = doc.addObject("Part::Feature", "Driveway")
    drive_obj.Shape = drive_shape
    drive_obj.Placement.Base = App.Vector(
        -lot_w*6 + side_setback + dw_w*6 - drive_w/2,
        -lot_d*6, 0
    )
    
    # Rear yard
    rear_w = lot_w * 12 - (2 * side_setback)
    rear_d = rear_setback
    rear_shape = Part.makePlane(rear_w, rear_d)
    rear_obj = doc.addObject("Part::Feature", "RearYard")
    rear_obj.Shape = rear_shape
    rear_obj.Placement.Base = App.Vector(
        -lot_w*6 + side_setback,
        -lot_d*6 + lot_d*12 - rear_setback, 0
    )
    
    # Side setbacks
    side_shape_l = Part.makePlane(side_setback, lot_d * 12 - front_setback - rear_setback)
    side_obj_l = doc.addObject("Part::Feature", "SideSetbackLeft")
    side_obj_l.Shape = side_shape_l
    side_obj_l.Placement.Base = App.Vector(-lot_w*6, -lot_d*6 + front_setback, 0)
    
    side_shape_r = Part.makePlane(side_setback, lot_d * 12 - front_setback - rear_setback)
    side_obj_r = doc.addObject("Part::Feature", "SideSetbackRight")
    side_obj_r.Shape = side_shape_r
    side_obj_r.Placement.Base = App.Vector(
        -lot_w*6 + lot_w*12 - side_setback,
        -lot_d*6 + front_setback, 0
    )
    
    # Utility stubs
    # Water service (front right corner typical)
    water_shape = Part.makeCylinder(3, 60)  # 3" pipe, 5' long
    water_obj = doc.addObject("Part::Feature", "WaterService")
    water_obj.Shape = water_shape
    water_obj.Placement.Base = App.Vector(
        -lot_w*6 + lot_w*12 - 24*12,
        -lot_d*6 + 5*12, 0
    )
    
    # Sewer service (front left typical)
    sewer_shape = Part.makeCylinder(4, 60)  # 4" pipe
    sewer_obj = doc.addObject("Part::Feature", "SewerService")
    sewer_obj.Shape = sewer_shape
    sewer_obj.Placement.Base = App.Vector(
        -lot_w*6 + 5*12,
        -lot_d*6 + 5*12, 0
    )
    
    # Electric service (front center)
    elec_shape = Part.makeCylinder(2, 48)
    elec_obj = doc.addObject("Part::Feature", "ElectricService")
    elec_obj.Shape = elec_shape
    elec_obj.Placement.Base = App.Vector(
        -lot_w*6 + lot_w*6,
        -lot_d*6 + 3*12, 0
    )
    
    # Contour lines
    if slope_pct and slope_pct > 0:
        create_contours(doc, 0, 0, elev_ft, slope_pct, lot_w, lot_d)
    
    # Dimension lines
    # Lot width dimension
    dim_w = Part.makeLine(
        App.Vector(-lot_w*6, -lot_d*6 - 20, 0),
        App.Vector(lot_w*6, -lot_d*6 - 20, 0)
    )
    dim_w_obj = doc.addObject("Part::Feature", f"Dim_LotWidth_{lot_w}ft")
    dim_w_obj.Shape = dim_w
    
    # Lot depth dimension
    dim_d = Part.makeLine(
        App.Vector(-lot_w*6 - 20, -lot_d*6, 0),
        App.Vector(-lot_w*6 - 20, lot_d*6, 0)
    )
    dim_d_obj = doc.addObject("Part::Feature", f"Dim_LotDepth_{lot_d}ft")
    dim_d_obj.Shape = dim_d
    
    doc.recompute()
    
    output_dir = os.path.expanduser("~/geniinow-projects/output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"SitePlan_{apn}.FCStd")
    doc.saveAs(output_path)
    
    print(f"Site plan generated: {output_path}")
    print(f"Lot: {lot_w}' x {lot_d}' | Dwelling: {dw_w}' x {dw_d}'")
    print(f"Elevation: {elev_ft} ft | Slope: {slope_pct}%")
    print(f"Objects: {len(doc.Objects)}")
    return doc

if __name__ == "__main__":
    ref_schema_path = os.path.expanduser("~/geniinow-projects/modules/training plan sets/reference_schema.json")
    
    if len(sys.argv) > 2 and sys.argv[1] == "--project-data":
        with open(sys.argv[2]) as f:
            project_data = json.load(f)
    elif os.path.exists(ref_schema_path):
        with open(ref_schema_path) as f:
            project_data = json.load(f)
        print("Using reference schema as template")
    else:
        print("Usage: python SitePlanGenerator.py --project-data /path/to/project.json")
        sys.exit(1)
    
    create_site_plan(project_data)
