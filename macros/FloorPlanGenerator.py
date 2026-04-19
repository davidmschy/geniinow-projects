"""
FloorPlanGenerator.py

Generate architectural floor plans from project data.
"""

import sys, os, json, math
sys.path.insert(0, "/Applications/FreeCAD.app/Contents/Resources/lib")

import FreeCAD as App
import Part

def create_floor_plan(project_data, output_dir):
    doc = App.newDocument(f"FloorPlan_{project_data['project_metadata']['apn']}")
    
    dwelling = project_data.get("dwelling_specifications", {})
    sip = project_data.get("sip_specifications", {})
    
    width = dwelling.get("width_ft", 20) * 12
    depth = dwelling.get("depth_ft", 32) * 12
    wall_thickness = sip.get("wall_thickness_in", 6.5)
    
    # Exterior walls as boxes
    walls = []
    w1 = Part.makeBox(width, wall_thickness, 120, App.Vector(0, 0, 0))                    # bottom
    w2 = Part.makeBox(width, wall_thickness, 120, App.Vector(0, depth-wall_thickness, 0)) # top
    w3 = Part.makeBox(wall_thickness, depth, 120, App.Vector(0, 0, 0))                    # left
    w4 = Part.makeBox(wall_thickness, depth, 120, App.Vector(width-wall_thickness, 0, 0)) # right
    walls = [w1, w2, w3, w4]
    
    # Interior walls
    int_walls = []
    module_type = dwelling.get("module_type", "single_family")
    
    if "duplex" in module_type or "two_unit" in module_type:
        dw = Part.makeBox(wall_thickness, depth - 2*wall_thickness, 120, 
                         App.Vector(width/2 - wall_thickness/2, wall_thickness, 0))
        int_walls.append(dw)
    
    if "adu" in module_type.lower():
        sep_wall = Part.makeBox(width - 2*wall_thickness, wall_thickness, 120,
                               App.Vector(wall_thickness, depth * 0.6, 0))
        int_walls.append(sep_wall)
        bath_depth = 8 * 12
        bath_wall = Part.makeBox(wall_thickness, bath_depth, 120,
                                App.Vector(width * 0.65, depth - wall_thickness - bath_depth, 0))
        int_walls.append(bath_wall)
    
    all_wall_solids = walls + int_walls
    
    # Doors (cutouts)
    door_width = 36
    door_height = 80
    doors = []
    
    # Front door
    fd = Part.makeBox(door_width, wall_thickness + 4, door_height,
                     App.Vector(width/2 - door_width/2, -2, 0))
    doors.append(fd)
    
    if int_walls:
        int_door = Part.makeBox(door_width, wall_thickness + 4, door_height,
                               App.Vector(width/2 - door_width/2, depth * 0.4, 0))
        doors.append(int_door)
    
    # Windows (cutouts)
    win_width = 36
    win_height = 48
    windows = []
    
    fw = Part.makeBox(win_width, wall_thickness + 4, win_height,
                     App.Vector(width * 0.25, -2, 36))
    windows.append(fw)
    
    rw = Part.makeBox(win_width, wall_thickness + 4, win_height,
                     App.Vector(width * 0.75, depth - wall_thickness - 2, 36))
    windows.append(rw)
    
    sw1 = Part.makeBox(wall_thickness + 4, win_width, win_height,
                      App.Vector(-2, depth * 0.3, 36))
    windows.append(sw1)
    
    sw2 = Part.makeBox(wall_thickness + 4, win_width, win_height,
                      App.Vector(width - wall_thickness - 2, depth * 0.7, 36))
    windows.append(sw2)
    
    # Cut doors and windows from walls
    wall_features = []
    for i, wall in enumerate(all_wall_solids):
        # Check intersection with each door
        for door in doors:
            if wall.BoundBox.intersect(door.BoundBox):
                wall = wall.cut(door)
        # Check intersection with each window
        for window in windows:
            if wall.BoundBox.intersect(window.BoundBox):
                wall = wall.cut(window)
        
        feat = doc.addObject("Part::Feature", f"Wall_{i}")
        feat.Shape = wall
        wall_features.append(feat)
    
    # Room markers
    if "adu" in module_type.lower():
        rooms = [
            {"name": "Living", "pos": (width * 0.5, depth * 0.3)},
            {"name": "Kitchen", "pos": (width * 0.3, depth * 0.15)},
            {"name": "Bedroom", "pos": (width * 0.5, depth * 0.75)},
            {"name": "Bath", "pos": (width * 0.82, depth * 0.85)}
        ]
    else:
        rooms = [
            {"name": "Living", "pos": (width * 0.5, depth * 0.35)},
            {"name": "Kitchen", "pos": (width * 0.25, depth * 0.15)},
            {"name": "Bedroom", "pos": (width * 0.75, depth * 0.75)},
            {"name": "Bath", "pos": (width * 0.25, depth * 0.75)}
        ]
    
    for room in rooms:
        marker = doc.addObject("Part::Sphere", f"Room_{room['name']}")
        marker.Radius = 6
        marker.Placement = App.Placement(App.Vector(room['pos'][0], room['pos'][1], 60), App.Rotation())
    
    # Dimension lines (as simple edges)
    dim_edges = []
    # Width dimension line
    dim_edges.append(Part.makeLine(App.Vector(0, -20, 0), App.Vector(width, -20, 0)))
    # Depth dimension line
    dim_edges.append(Part.makeLine(App.Vector(-20, 0, 0), App.Vector(-20, depth, 0)))
    
    dim_compound = Part.makeCompound(dim_edges)
    dim_feat = doc.addObject("Part::Feature", "Dimensions")
    dim_feat.Shape = dim_compound
    
    doc.recompute()
    
    # Save
    fcstd_path = os.path.join(output_dir, f"FloorPlan_{project_data['project_metadata']['apn']}.FCStd")
    doc.saveAs(fcstd_path)
    
    # Try DXF export
    dxf_path = os.path.join(output_dir, f"FloorPlan_{project_data['project_metadata']['apn']}.dxf")
    try:
        compound = doc.addObject("Part::Compound", "AllWalls")
        compound.Links = wall_features
        doc.recompute()
        import importDXF
        importDXF.export([compound], dxf_path)
        print(f"DXF: {dxf_path}")
    except Exception as e:
        print(f"DXF export: {e}")
        dxf_path = None
    
    doc.save()
    
    return {
        "fcstd": fcstd_path,
        "dxf": dxf_path,
        "rooms": [r["name"] for r in rooms],
        "module_type": module_type,
        "walls": len(all_wall_solids),
        "doors": len(doors),
        "windows": len(windows)
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-data", required=True)
    parser.add_argument("--output", default=os.path.expanduser("~/geniinow-projects/output"))
    args = parser.parse_args()
    
    with open(args.project_data) as f:
        data = json.load(f)
    
    os.makedirs(args.output, exist_ok=True)
    result = create_floor_plan(data, args.output)
    
    print(f"\nFloor plan generated:")
    print(f"  FCStd: {result['fcstd']}")
    print(f"  DXF: {result['dxf']}")
    print(f"  Rooms: {', '.join(result['rooms'])}")
    print(f"  Walls: {result['walls']}, Doors: {result['doors']}, Windows: {result['windows']}")

if __name__ == "__main__":
    main()
