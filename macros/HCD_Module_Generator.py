"""
HCD Modular Housing - Parametric Module Generator
Generates HCD-compliant modular units with SIP walls, steel flooring
"""
import FreeCAD as App
import Part
import Sketcher
import Draft

class HCDModule:
    """Base class for HCD-compliant modular housing units"""
    
    def __init__(self, width=14.0, length=40.0, height=10.5, unit='ft'):
        self.width = width    # Module width
        self.length = length  # Module length  
        self.height = height  # Ceiling height
        self.unit = unit
        self.doc = App.newDocument(f"HCD_Module_{width}x{length}")
        
    def create_steel_floor(self, gauge=14, joist_spacing=16):
        """Create 14-gauge C-channel steel subfloor frame"""
        # C-channel profile
        frame = self.doc.addObject('Part::Box', 'SteelFloorFrame')
        frame.Length = self.length
        frame.Width = self.width  
        frame.Height = 0.5  # 6" C-channel depth
        
        # Add joists at 16" OC
        num_joists = int((self.length * 12) / joist_spacing)
        for i in range(num_joists):
            joist = self.doc.addObject('Part::Box', f'Joist_{i}')
            joist.Length = 0.5  # 6" web
            joist.Width = self.width - 1.0  # Inside frame
            joist.Height = 0.5
            joist.Placement.Base.x = (i * joist_spacing) / 12.0
            joist.Placement.Base.z = 0.25
            
        self.doc.recompute()
        return frame
        
    def create_sip_walls(self, thickness=6.5):
        """Create SIP wall panels with OSB skins and EPS core"""
        # Front wall
        front = self.doc.addObject('Part::Box', 'SIP_FrontWall')
        front.Length = self.width
        front.Width = thickness / 12.0
        front.Height = self.height
        front.Placement.Base.y = self.length
        
        # Rear wall
        rear = self.doc.addObject('Part::Box', 'SIP_RearWall')
        rear.Length = self.width
        rear.Width = thickness / 12.0
        rear.Height = self.height
        
        # Side walls
        left = self.doc.addObject('Part::Box', 'SIP_LeftWall')
        left.Length = thickness / 12.0
        left.Width = self.length
        left.Height = self.height
        
        right = self.doc.addObject('Part::Box', 'SIP_RightWall')
        right.Length = thickness / 12.0
        right.Width = self.length
        right.Height = self.height
        right.Placement.Base.x = self.width - (thickness / 12.0)
        
        self.doc.recompute()
        return [front, rear, left, right]
        
    def create_sip_roof(self, thickness=8.25, pitch=0.25):
        """Create SIP roof panels with specified pitch"""
        roof = self.doc.addObject('Part::Box', 'SIP_Roof')
        roof.Length = self.width + 1.0  # Overhang
        roof.Width = self.length + 1.0
        roof.Height = thickness / 12.0
        roof.Placement.Base.z = self.height
        roof.Placement.Base.x = -0.5
        roof.Placement.Base.y = -0.5
        
        self.doc.recompute()
        return roof
        
    def export_ifc(self, filepath):
        """Export module to IFC for BIM coordination"""
        import importIFC
        importIFC.export([obj for obj in self.doc.Objects if hasattr(obj, 'Shape')], filepath)
        
    def export_manufacturing_dxf(self, filepath):
        """Export 2D manufacturing drawings to DXF"""
        import importDXF
        for obj in self.doc.Objects:
            if hasattr(obj, 'Shape'):
                importDXF.export([obj], filepath.replace('.dxf', f'_{obj.Name}.dxf'))


def create_standard_modules():
    """Create standard HCD module sizes"""
    modules = {
        'HCD_14x40': HCDModule(14, 40, 10.5),
        'HCD_14x56': HCDModule(14, 56, 10.5), 
        'HCD_16x40': HCDModule(16, 40, 10.5),
        'HCD_16x56': HCDModule(16, 56, 10.5),
    }
    
    for name, mod in modules.items():
        mod.create_steel_floor()
        mod.create_sip_walls()
        mod.create_sip_roof()
        mod.doc.saveAs(f"/Users/davidschy/geniinow-projects/modules/{name}.FCStd")
        print(f"Created {name}")
        
    return modules


if __name__ == "__main__":
    modules = create_standard_modules()
    print("Standard HCD modules generated successfully")
