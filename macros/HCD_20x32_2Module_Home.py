"""
HCD 20x32 2-Bed 2-Bath Home - 2 Module Configuration
Total: 20' x 32' = 640 sq ft
Split: Two 10' x 32' modules (transport compliant)
Joined on-site along 32' dimension
"""
import FreeCAD as App
import Part
import os

class HCDModule:
    """HCD-compliant modular unit with room layouts"""
    
    def __init__(self, name, width, length, height=10.5, position=(0,0,0)):
        self.name = name
        self.width = width      # ft
        self.length = length    # ft
        self.height = height    # ft
        self.position = position
        self.doc = App.newDocument(name)
        self.walls = []
        self.rooms = []
        
    def create_steel_floor(self, gauge=14, joist_spacing=16):
        """14-gauge C-channel steel subfloor frame"""
        # Main frame perimeter
        frame = self.doc.addObject('Part::Box', 'SteelFrame')
        frame.Length = self.length
        frame.Width = self.width
        frame.Height = 0.5  # 6" C-channel
        frame.Placement.Base = App.Vector(self.position[0], self.position[1], self.position[2])
        
        # Joists at 16" OC
        num_joists = int((self.length * 12) / joist_spacing) + 1
        for i in range(num_joists):
            joist = self.doc.addObject('Part::Box', f'Joist_{i}')
            joist.Length = 0.5  # 6" web
            joist.Width = self.width - 1.0  # Inside frame
            joist.Height = 0.5
            joist.Placement.Base.x = self.position[0] + (i * joist_spacing) / 12.0
            joist.Placement.Base.y = self.position[1] + 0.5
            joist.Placement.Base.z = self.position[2] + 0.25
            
        self.doc.recompute()
        return frame
        
    def create_sip_walls(self, thickness=6.5):
        """SIP wall panels - OSB skins + EPS core"""
        t = thickness / 12.0
        
        # Front wall (32' side)
        front = self.doc.addObject('Part::Box', 'Wall_Front')
        front.Length = self.width
        front.Width = t
        front.Height = self.height
        front.Placement.Base.x = self.position[0]
        front.Placement.Base.y = self.position[1] + self.length - t
        front.Placement.Base.z = self.position[2]
        
        # Rear wall (32' side)
        rear = self.doc.addObject('Part::Box', 'Wall_Rear')
        rear.Length = self.width
        rear.Width = t
        rear.Height = self.height
        rear.Placement.Base.x = self.position[0]
        rear.Placement.Base.y = self.position[1]
        rear.Placement.Base.z = self.position[2]
        
        # Left wall (10' side) - will be exterior on Module A
        left = self.doc.addObject('Part::Box', 'Wall_Left')
        left.Length = t
        left.Width = self.length
        left.Height = self.height
        left.Placement.Base.x = self.position[0]
        left.Placement.Base.y = self.position[1]
        left.Placement.Base.z = self.position[2]
        
        # Right wall (10' side) - will be exterior on Module B
        right = self.doc.addObject('Part::Box', 'Wall_Right')
        right.Length = t
        right.Width = self.length
        right.Height = self.height
        right.Placement.Base.x = self.position[0] + self.width - t
        right.Placement.Base.y = self.position[1]
        right.Placement.Base.z = self.position[2]
        
        self.walls = [front, rear, left, right]
        self.doc.recompute()
        return self.walls
    
    def create_sip_roof(self, thickness=8.25):
        """SIP roof with overhang"""
        roof = self.doc.addObject('Part::Box', 'Roof')
        roof.Length = self.width + 1.0  # Overhang
        roof.Width = self.length + 1.0
        roof.Height = thickness / 12.0
        roof.Placement.Base.x = self.position[0] - 0.5
        roof.Placement.Base.y = self.position[1] - 0.5
        roof.Placement.Base.z = self.position[2] + self.height
        
        self.doc.recompute()
        return roof
    
    def create_interior_walls(self, layout):
        """Create interior walls based on room layout"""
        t = 4.5 / 12.0  # 2x4 interior wall thickness
        
        for wall in layout.get('interior_walls', []):
            w = self.doc.addObject('Part::Box', wall['name'])
            w.Length = wall.get('length', t)
            w.Width = wall.get('width', t)
            w.Height = self.height
            w.Placement.Base.x = self.position[0] + wall['x']
            w.Placement.Base.y = self.position[1] + wall['y']
            w.Placement.Base.z = self.position[2]
            self.walls.append(w)
        
        self.doc.recompute()
    
    def create_room_footprints(self, rooms):
        """Create 2D floor plan representation of rooms"""
        for room in rooms:
            r = self.doc.addObject('Part::Box', room['name'])
            r.Length = room['width']
            r.Width = room['length']
            r.Height = 0.1  # Thin slab for visualization
            r.Placement.Base.x = self.position[0] + room['x']
            r.Placement.Base.y = self.position[1] + room['y']
            r.Placement.Base.z = self.position[2] + 0.5  # On top of floor frame
            self.rooms.append(r)
        
        self.doc.recompute()
    
    def save(self, path):
        """Save FreeCAD document"""
        self.doc.saveAs(path)
        return path
    
    def export_step(self, path):
        """Export to STEP for manufacturing"""
        objs = [obj for obj in self.doc.Objects if hasattr(obj, 'Shape')]
        if objs:
            import Part
            compound = Part.makeCompound([obj.Shape for obj in objs])
            compound.exportStep(path)
        return path
    
    def export_dxf(self, path):
        """Export 2D floor plan to DXF"""
        # Simple DXF export of floor plan (z=0 cut)
        import Drawing
        page = self.doc.addObject('Drawing::FeaturePage', 'Page')
        page.Template = os.path.join(App.getResourceDir(), 'Mod/Drawing/Templates/A3_Landscape.svg')
        
        # Export each wall as line drawing
        for obj in self.walls:
            view = self.doc.addObject('Drawing::FeatureViewPart', f'View_{obj.Name}')
            view.Source = obj
            view.Direction = (0, 0, 1)
            view.X = 100
            view.Y = 100
            view.Scale = 1/12.0  # 1" = 1'
            page.addObject(view)
        
        self.doc.recompute()
        # Note: Full DXF export requires more setup, using STEP for now
        return self.export_step(path.replace('.dxf', '.stp'))


class Home20x32:
    """20x32 2-bed 2-bath home as 2 transportable modules"""
    
    def __init__(self):
        # Module A: Left side (Bedroom 1 + Bath 1 + Living half)
        # Module B: Right side (Bedroom 2 + Bath 2 + Kitchen half)
        self.module_a = HCDModule('Module_A_Left', 10, 32, position=(0, 0, 0))
        self.module_b = HCDModule('Module_B_Right', 10, 32, position=(10, 0, 0))
        
    def generate(self):
        """Generate complete home with both modules"""
        print("Generating 20x32 2-Bed 2-Bath Home...")
        print("Module A: 10x32 (Left) - Bedroom 1, Bath 1, Living Area")
        print("Module B: 10x32 (Right) - Bedroom 2, Bath 2, Kitchen/Dining")
        
        # Generate Module A
        self._build_module_a()
        
        # Generate Module B  
        self._build_module_b()
        
        # Create combined document showing both modules
        self.combined = App.newDocument('Home_20x32_Combined')
        
        # Save individual modules
        out_dir = '/Users/davidschy/geniinow-projects/modules'
        os.makedirs(out_dir, exist_ok=True)
        
        self.module_a.save(f'{out_dir}/Module_A_10x32_Left.FCStd')
        self.module_b.save(f'{out_dir}/Module_B_10x32_Right.FCStd')
        
        # Export STEP files for manufacturing
        self.module_a.export_step(f'{out_dir}/Module_A_10x32_Left.stp')
        self.module_b.export_step(f'{out_dir}/Module_B_10x32_Right.stp')
        
        print(f"\nFiles saved to {out_dir}:")
        print(f"  Module_A_10x32_Left.FCStd")
        print(f"  Module_B_10x32_Right.FCStd")
        print(f"  Module_A_10x32_Left.stp")
        print(f"  Module_B_10x32_Right.stp")
        
        return self
    
    def _build_module_a(self):
        """Module A: Bedroom 1 (10x12), Bath 1 (5x8), Living (10x12)"""
        mod = self.module_a
        mod.create_steel_floor()
        mod.create_sip_walls()
        
        # Interior layout for Module A
        rooms_a = [
            {'name': 'Bedroom_1', 'width': 10, 'length': 12, 'x': 0, 'y': 0},
            {'name': 'Bathroom_1', 'width': 5, 'length': 8, 'x': 0, 'y': 12},
            {'name': 'Living_Area', 'width': 10, 'length': 12, 'x': 0, 'y': 20},
        ]
        mod.create_room_footprints(rooms_a)
        
        # Interior walls
        interior_a = [
            {'name': 'Wall_Bed_Bath', 'length': 0.375, 'width': 8, 'x': 5, 'y': 12},
            {'name': 'Wall_Bath_Living', 'length': 10, 'width': 0.375, 'x': 0, 'y': 20},
        ]
        mod.create_interior_walls({'interior_walls': interior_a})
        
        mod.create_sip_roof()
    
    def _build_module_b(self):
        """Module B: Bedroom 2 (10x12), Bath 2 (5x8), Kitchen (10x12)"""
        mod = self.module_b
        mod.create_steel_floor()
        mod.create_sip_walls()
        
        # Interior layout for Module B
        rooms_b = [
            {'name': 'Bedroom_2', 'width': 10, 'length': 12, 'x': 0, 'y': 0},
            {'name': 'Bathroom_2', 'width': 5, 'length': 8, 'x': 5, 'y': 12},
            {'name': 'Kitchen', 'width': 10, 'length': 12, 'x': 0, 'y': 20},
        ]
        mod.create_room_footprints(rooms_b)
        
        # Interior walls
        interior_b = [
            {'name': 'Wall_Bed_Bath_B', 'length': 0.375, 'width': 8, 'x': 5, 'y': 12},
            {'name': 'Wall_Bath_Kitchen', 'length': 10, 'width': 0.375, 'x': 0, 'y': 20},
        ]
        mod.create_interior_walls({'interior_walls': interior_b})
        
        mod.create_sip_roof()


def generate_home():
    """FreeCAD macro entry point"""
    home = Home20x32()
    home.generate()
    print("\n=== 20x32 Home Generation Complete ===")
    print("Total footprint: 20' x 32' = 640 sq ft")
    print("Module split: Two 10' x 32' units")
    print("Transport width: 10' (highway compliant)")
    print("On-site join: Along 32' dimension")
    return home


if __name__ == "__main__":
    generate_home()
