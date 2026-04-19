"""
FreeCAD Drawing Templates & Parametric Details for HCD Modular Plan Sets
FreeCAD 1.1.1 compatible - Uses TechDraw instead of deprecated Drawing workbench
"""
import FreeCAD as App
import Part
import TechDraw
import os

class DrawingTemplate:
    """A-size drawing template with title block for HCD modular plans"""
    
    def __init__(self, doc_name="PlanSet_Template"):
        self.doc = App.newDocument(doc_name)
        self.width = 24.0   # inches (D-size horizontal)
        self.height = 18.0  # inches
        
    def create_title_block(self, project_info=None):
        """Create title block geometry in model space"""
        info = project_info or {}
        
        # Title block rectangle (bottom right corner)
        tb_width = 8.0
        tb_height = 2.5
        tb_x = self.width - tb_width - 0.5
        tb_y = 0.5
        
        # Outer border
        border = self.doc.addObject('Part::Box', 'TitleBlock_Border')
        border.Length = tb_width
        border.Width = 0.02
        border.Height = tb_height
        border.Placement.Base = App.Vector(tb_x, tb_y, 0)
        
        # Horizontal divisions
        for i, h in enumerate([0.5, 1.0, 1.5, 2.0]):
            line = self.doc.addObject('Part::Box', f'TB_HLine_{i}')
            line.Length = tb_width
            line.Width = 0.01
            line.Height = 0.01
            line.Placement.Base = App.Vector(tb_x, tb_y + h, 0)
        
        # Vertical divisions
        for i, x in enumerate([3.0, 5.0, 6.5]):
            line = self.doc.addObject('Part::Box', f'TB_VLine_{i}')
            line.Length = 0.01
            line.Width = 0.01
            line.Height = tb_height
            line.Placement.Base = App.Vector(tb_x + x, tb_y, 0)
        
        # Revision block (top right, above title block)
        rev_width = 4.0
        rev_height = 1.0
        rev_x = self.width - rev_width - 0.5
        rev_y = tb_y + tb_height + 0.1
        
        rev_border = self.doc.addObject('Part::Box', 'RevBlock_Border')
        rev_border.Length = rev_width
        rev_border.Width = 0.02
        rev_border.Height = rev_height
        rev_border.Placement.Base = App.Vector(rev_x, rev_y, 0)
        
        self.doc.recompute()
        return border
    
    def create_sheet_border(self):
        """Create drawing sheet border with margins"""
        margin = 0.5
        
        # Outer border
        outer = self.doc.addObject('Part::Box', 'Border_Outer')
        outer.Length = self.width - 2*margin
        outer.Width = 0.02
        outer.Height = self.height - 2*margin
        outer.Placement.Base = App.Vector(margin, margin, 0)
        
        # Inner border (trim line)
        inner = self.doc.addObject('Part::Box', 'Border_Inner')
        inner.Length = self.width - 2*margin - 0.25
        inner.Width = 0.01
        inner.Height = self.height - 2*margin - 0.25
        inner.Placement.Base = App.Vector(margin + 0.125, margin + 0.125, 0)
        
        self.doc.recompute()
        return outer
    
    def save_template(self, path):
        """Save as FreeCAD template for TechDraw workbench"""
        self.doc.saveAs(path)
        return path


class ParametricDetails:
    """Library of parametric construction details"""
    
    @staticmethod
    def sip_wall_section(doc, scale=1.0, position=(0,0,0)):
        """
        Generate SIP wall section detail
        8" SIP panel: 7/16" OSB + 7.25" EPS + 7/16" OSB
        With 2x4 plates, 1/2" gyp each side
        """
        x, y, z = position
        
        # Wall panel core (EPS)
        eps = doc.addObject('Part::Box', 'SIP_EPS_Core')
        eps.Length = 8.0 * scale
        eps.Width = 7.25/12.0 * scale
        eps.Height = 10.0 * scale  # 10' height
        eps.Placement.Base = App.Vector(x, y + (0.5 + 0.5/12.0)*scale, z + (1.5/12.0)*scale)
        
        # OSB skins
        osb_out = doc.addObject('Part::Box', 'SIP_OSB_Exterior')
        osb_out.Length = 8.0 * scale
        osb_out.Width = (7.0/16.0)/12.0 * scale
        osb_out.Height = 10.0 * scale
        osb_out.Placement.Base = App.Vector(x, y + (0.5 + 0.5/12.0 - 7/16/12.0)*scale, z + (1.5/12.0)*scale)
        
        osb_in = doc.addObject('Part::Box', 'SIP_OSB_Interior')
        osb_in.Length = 8.0 * scale
        osb_in.Width = (7.0/16.0)/12.0 * scale
        osb_in.Height = 10.0 * scale
        osb_in.Placement.Base = App.Vector(x, y + (0.5 + 0.5/12.0 + 7.25/12.0)*scale, z + (1.5/12.0)*scale)
        
        # Gypsum board interior
        gyp = doc.addObject('Part::Box', 'Gyp_Board')
        gyp.Length = 8.0 * scale
        gyp.Width = (0.5/12.0) * scale
        gyp.Height = 10.0 * scale
        gyp.Placement.Base = App.Vector(x, y + (0.5 + 0.5/12.0 + 7.25/12.0 + 7/16/12.0)*scale, z + (1.5/12.0)*scale)
        
        # Bottom plate (2x4)
        bot_plate = doc.addObject('Part::Box', 'Bottom_Plate')
        bot_plate.Length = 8.0 * scale
        bot_plate.Width = (3.5/12.0) * scale
        bot_plate.Height = (1.5/12.0) * scale
        bot_plate.Placement.Base = App.Vector(x, y + 0.5*scale, z)
        
        # Top plate (double 2x4)
        top_plate = doc.addObject('Part::Box', 'Top_Plate')
        top_plate.Length = 8.0 * scale
        top_plate.Width = (3.5/12.0) * scale
        top_plate.Height = (3.0/12.0) * scale
        top_plate.Placement.Base = App.Vector(x, y + 0.5*scale, z + (10.0 + 1.5/12.0)*scale)
        
        # Studs @ 16" OC
        num_studs = int((8.0 * 12) / 16) + 1
        for i in range(num_studs):
            stud = doc.addObject('Part::Box', f'Stud_{i}')
            stud.Length = (1.5/12.0) * scale
            stud.Width = (3.5/12.0) * scale
            stud.Height = 10.0 * scale
            stud_x = x + (i * 16.0/12.0) * scale
            stud.Placement.Base = App.Vector(stud_x, y + 0.5*scale, z + (1.5/12.0)*scale)
        
        doc.recompute()
        return [eps, osb_out, osb_in, gyp, bot_plate, top_plate]
    
    @staticmethod
    def sip_roof_section(doc, scale=1.0, position=(0,0,0)):
        """
        Generate SIP roof section detail
        8" SIP panel with overhang, fascia, optional standing seam
        """
        x, y, z = position
        
        # Roof panel (8" SIP)
        roof = doc.addObject('Part::Box', 'SIP_Roof_Panel')
        roof.Length = 8.0 * scale
        roof.Width = (8.25/12.0) * scale
        roof.Height = 0.5 * scale  # Thin for section view
        roof.Placement.Base = App.Vector(x, y, z + 10.5*scale)
        
        # Fascia (2x12)
        fascia = doc.addObject('Part::Box', 'Fascia')
        fascia.Length = (1.5/12.0) * scale
        fascia.Width = (11.25/12.0) * scale
        fascia.Height = 0.5 * scale
        fascia.Placement.Base = App.Vector(x, y - (11.25/12.0)*scale, z + 10.5*scale)
        
        # Overhang (2' typical)
        overhang = doc.addObject('Part::Box', 'Overhang')
        overhang.Length = 2.0 * scale
        overhang.Width = (8.25/12.0) * scale
        overhang.Height = 0.5 * scale
        overhang.Placement.Base = App.Vector(x - 2.0*scale, y, z + 10.5*scale)
        
        # Top plate connection
        plate = doc.addObject('Part::Box', 'Top_Plate_Roof')
        plate.Length = 8.0 * scale
        plate.Width = (3.5/12.0) * scale
        plate.Height = (3.0/12.0) * scale
        plate.Placement.Base = App.Vector(x, y + 0.5*scale, z + 10.0*scale)
        
        doc.recompute()
        return [roof, fascia, overhang, plate]
    
    @staticmethod
    def sip_floor_section(doc, scale=1.0, position=(0,0,0)):
        """
        Generate SIP floor section detail
        TJI joists @ 14" OC with 6" SIP floor panel
        """
        x, y, z = position
        
        # TJI joists
        num_joists = int((8.0 * 12) / 14) + 1
        for i in range(num_joists):
            joist = doc.addObject('Part::Box', f'TJI_{i}')
            joist.Length = (1.5/12.0) * scale
            joist.Width = (9.5/12.0) * scale  # TJI 10
            joist.Height = 8.0 * scale  # Span direction
            joist_x = x + (i * 14.0/12.0) * scale
            joist.Placement.Base = App.Vector(joist_x, y + 0.5*scale, z)
        
        # SIP floor panel (6")
        floor = doc.addObject('Part::Box', 'SIP_Floor')
        floor.Length = 8.0 * scale
        floor.Width = (6.0/12.0) * scale
        floor.Height = 0.5 * scale
        floor.Placement.Base = App.Vector(x, y + 0.5*scale, z + (9.5/12.0)*scale)
        
        # Subfloor (3/4" plywood)
        subfloor = doc.addObject('Part::Box', 'Subfloor')
        subfloor.Length = 8.0 * scale
        subfloor.Width = (0.75/12.0) * scale
        subfloor.Height = 0.5 * scale
        subfloor.Placement.Base = App.Vector(x, y + 0.5*scale, z + (9.5/12.0 + 6.0/12.0)*scale)
        
        # Rim joist (LVL 1.5" x 9.5")
        rim = doc.addObject('Part::Box', 'Rim_Joist')
        rim.Length = (1.5/12.0) * scale
        rim.Width = (9.5/12.0) * scale
        rim.Height = 8.0 * scale
        rim.Placement.Base = App.Vector(x, y + 0.5*scale, z)
        
        doc.recompute()
        return [floor, subfloor, rim]
    
    @staticmethod
    def module_connection_detail(doc, scale=1.0, position=(0,0,0)):
        """
        Generate module-to-module connection detail
        Butt joint with dimensional lumber spline, sealant, fasteners
        """
        x, y, z = position
        
        # Module A wall end
        mod_a = doc.addObject('Part::Box', 'Module_A_Wall')
        mod_a.Length = (3.5/12.0) * scale
        mod_a.Width = (5.5/12.0) * scale  # 2x6 plate
        mod_a.Height = 10.0 * scale
        mod_a.Placement.Base = App.Vector(x, y, z)
        
        # Module B wall end
        mod_b = doc.addObject('Part::Box', 'Module_B_Wall')
        mod_b.Length = (3.5/12.0) * scale
        mod_b.Width = (5.5/12.0) * scale
        mod_b.Height = 10.0 * scale
        mod_b.Placement.Base = App.Vector(x + (3.5/12.0 + 1.5/12.0)*scale, y, z)
        
        # Spline (2x lumber between modules)
        spline = doc.addObject('Part::Box', 'Connection_Spline')
        spline.Length = (1.5/12.0) * scale
        spline.Width = (5.5/12.0) * scale
        spline.Height = 10.0 * scale
        spline.Placement.Base = App.Vector(x + (3.5/12.0)*scale, y, z)
        
        # Sealant gap representation
        sealant = doc.addObject('Part::Box', 'Sealant')
        sealant.Length = 0.5/12.0 * scale
        sealant.Width = 5.5/12.0 * scale
        sealant.Height = 10.0 * scale
        sealant.Placement.Base = App.Vector(x + (3.5/12.0 + 1.5/12.0)*scale, y, z)
        
        doc.recompute()
        return [mod_a, mod_b, spline, sealant]


def generate_detail_library():
    """Generate all parametric details and save"""
    out_dir = '/Users/davidschy/geniinow-projects/modules/detail_library'
    os.makedirs(out_dir, exist_ok=True)
    
    # SIP Wall Section
    doc = App.newDocument('SIP_Wall_Section')
    ParametricDetails.sip_wall_section(doc, scale=3.0)
    doc.saveAs(f'{out_dir}/SIP_Wall_Section.FCStd')
    App.closeDocument('SIP_Wall_Section')
    
    # SIP Roof Section
    doc2 = App.newDocument('SIP_Roof_Section')
    ParametricDetails.sip_roof_section(doc2, scale=3.0)
    doc2.saveAs(f'{out_dir}/SIP_Roof_Section.FCStd')
    App.closeDocument('SIP_Roof_Section')
    
    # SIP Floor Section
    doc3 = App.newDocument('SIP_Floor_Section')
    ParametricDetails.sip_floor_section(doc3, scale=3.0)
    doc3.saveAs(f'{out_dir}/SIP_Floor_Section.FCStd')
    App.closeDocument('SIP_Floor_Section')
    
    # Module Connection
    doc4 = App.newDocument('Module_Connection')
    ParametricDetails.module_connection_detail(doc4, scale=3.0)
    doc4.saveAs(f'{out_dir}/Module_Connection.FCStd')
    App.closeDocument('Module_Connection')
    
    # Title Block Template
    tmpl = DrawingTemplate('Title_Block_Template')
    tmpl.create_sheet_border()
    tmpl.create_title_block()
    tmpl.save_template(f'{out_dir}/Title_Block_Template.FCStd')
    App.closeDocument('Title_Block_Template')
    
    print(f"Detail library generated in {out_dir}")
    print("Files:")
    for f in os.listdir(out_dir):
        print(f"  {f}")
    
    return out_dir


if __name__ == "__main__":
    generate_detail_library()
