"""
Plan Set Generator for HCD Modular Housing
Generates complete permit-ready plan sets from text prompts or reference data
"""
import FreeCAD as App
import Part
import os
import json
import re
from datetime import datetime

class PromptParser:
    """Extract design parameters from natural language prompts"""
    
    @staticmethod
    def parse(prompt):
        """Parse a design prompt into structured parameters"""
        result = {
            'type': 'single_family',
            'bedrooms': 2,
            'bathrooms': 2,
            'stories': 1,
            'width': 20,
            'depth': 32,
            'height': 10,
            'construction': 'sip',
            'jurisdiction': 'hanford_ca',
            'climate_zone': 8,
            'modules': [],
            'unit_count': 1,
            'roof_type': 'gable',
            'foundation': 'crawl_space'
        }
        
        prompt_lower = prompt.lower()
        
        # Detect building type
        if 'duplex' in prompt_lower:
            result['type'] = 'duplex'
            result['unit_count'] = 2
        elif 'triplex' in prompt_lower:
            result['type'] = 'triplex'
            result['unit_count'] = 3
        elif 'fourplex' in prompt_lower or 'quadplex' in prompt_lower:
            result['type'] = 'fourplex'
            result['unit_count'] = 4
            
        # Extract bedrooms
        bed_match = re.search(r'(\d+)\s*bed', prompt_lower)
        if bed_match:
            result['bedrooms'] = int(bed_match.group(1))
            
        # Extract bathrooms
        bath_match = re.search(r'(\d+(?:\.5)?)\s*bath', prompt_lower)
        if bath_match:
            result['bathrooms'] = float(bath_match.group(1))
            
        # Extract stories
        if '2-story' in prompt_lower or 'two-story' in prompt_lower or '2 story' in prompt_lower:
            result['stories'] = 2
        elif '3-story' in prompt_lower or 'three-story' in prompt_lower or '3 story' in prompt_lower:
            result['stories'] = 3
            
        # Extract dimensions (WxD or WxL)
        dim_match = re.search(r'(\d+)\s*[xX]\s*(\d+)', prompt_lower)
        if dim_match:
            result['width'] = int(dim_match.group(1))
            result['depth'] = int(dim_match.group(2))
            
        # Detect construction type
        if 'sip' in prompt_lower or 'structural insulated panel' in prompt_lower:
            result['construction'] = 'sip'
        elif 'stick' in prompt_lower or 'framing' in prompt_lower:
            result['construction'] = 'stick_frame'
        elif 'steel' in prompt_lower:
            result['construction'] = 'steel'
            
        # Detect jurisdiction/climate zone
        if 'hanford' in prompt_lower:
            result['jurisdiction'] = 'hanford_ca'
            result['climate_zone'] = 8
        elif 'fresno' in prompt_lower:
            result['jurisdiction'] = 'fresno_ca'
            result['climate_zone'] = 13
        elif 'bakersfield' in prompt_lower:
            result['jurisdiction'] = 'bakersfield_ca'
            result['climate_zone'] = 13
        elif 'sacramento' in prompt_lower:
            result['jurisdiction'] = 'sacramento_ca'
            result['climate_zone'] = 12
        elif 'los angeles' in prompt_lower or 'la' in prompt_lower:
            result['jurisdiction'] = 'los_angeles_ca'
            result['climate_zone'] = 9
            
        # Detect roof type
        if 'flat' in prompt_lower:
            result['roof_type'] = 'flat'
        elif 'hip' in prompt_lower:
            result['roof_type'] = 'hip'
        elif 'gable' in prompt_lower:
            result['roof_type'] = 'gable'
            
        return result


class ModuleDesigner:
    """Split building into transportable modules"""
    
    MAX_MODULE_WIDTH = 16.0  # feet (transport limit)
    MAX_MODULE_HEIGHT = 13.5  # feet (transport limit)
    MAX_MODULE_LENGTH = 76.0  # feet (transport limit)
    
    @staticmethod
    def design_modules(params):
        """Determine module configuration from building parameters"""
        width = params['width']
        depth = params['depth']
        stories = params['stories']
        unit_count = params['unit_count']
        
        modules = []
        
        if unit_count == 1:
            # Single family - simple split if needed
            if width <= ModuleDesigner.MAX_MODULE_WIDTH:
                modules.append({
                    'id': 'Module_1',
                    'width': width,
                    'depth': depth,
                    'height': params['height'],
                    'floor': 1,
                    'unit': 1,
                    'type': 'complete'
                })
            else:
                # Split width-wise
                half_width = width / 2
                modules.append({
                    'id': 'Module_A',
                    'width': half_width,
                    'depth': depth,
                    'height': params['height'],
                    'floor': 1,
                    'unit': 1,
                    'type': 'left_half'
                })
                modules.append({
                    'id': 'Module_B',
                    'width': half_width,
                    'depth': depth,
                    'height': params['height'],
                    'floor': 1,
                    'unit': 1,
                    'type': 'right_half'
                })
                
        elif unit_count == 2:
            # Duplex - typically 2 modules per floor, side by side
            unit_width = width / 2
            for story in range(1, stories + 1):
                for unit in range(1, 3):
                    module_id = f'Module_{chr(64 + (story-1)*2 + unit)}'
                    modules.append({
                        'id': module_id,
                        'width': unit_width,
                        'depth': depth,
                        'height': params['height'],
                        'floor': story,
                        'unit': unit,
                        'type': 'unit_half'
                    })
                    
        elif unit_count >= 3:
            # Multi-family - more complex splitting
            unit_width = width / unit_count
            for story in range(1, stories + 1):
                for unit in range(1, unit_count + 1):
                    module_id = f'Module_{story}{chr(64 + unit)}'
                    modules.append({
                        'id': module_id,
                        'width': unit_width,
                        'depth': depth,
                        'height': params['height'],
                        'floor': story,
                        'unit': unit,
                        'type': 'unit_segment'
                    })
        
        # Add balcony/deck modules for 2nd story if applicable
        if stories > 1:
            modules.append({
                'id': f'Module_{len(modules)+1}',
                'width': width,
                'depth': 4.0,  # 4' deep balcony
                'height': 0.5,
                'floor': 2,
                'unit': 0,
                'type': 'balcony_on_site'
            })
        
        return modules


class FloorPlanGenerator:
    """Generate 2D floor plan geometry from parameters"""
    
    WALL_THICKNESS = 0.5  # feet (6" SIP + gyp)
    
    @staticmethod
    def generate_floor_plan(doc, params, floor=1, unit=1):
        """Generate floor plan for a specific floor and unit"""
        width = params['width']
        depth = params['depth']
        bedrooms = params['bedrooms']
        bathrooms = params['bathrooms']
        
        # For multi-unit, divide dimensions
        if params['unit_count'] > 1:
            width = width / params['unit_count']
            bedrooms = max(1, bedrooms // params['unit_count'])
            bathrooms = max(1, round(bathrooms / params['unit_count']))
        
        # Outer walls
        outer_wall = FloorPlanGenerator._create_rectangle(
            doc, f'Floor{floor}_Unit{unit}_OuterWall',
            0, 0, width, depth, FloorPlanGenerator.WALL_THICKNESS
        )
        
        # Interior walls based on bedroom/bathroom count
        interior_walls = []
        
        if bedrooms == 1:
            # Simple 1-bed layout
            # Bedroom at back
            bed_width = width * 0.6
            bed_depth = depth * 0.4
            bed_x = (width - bed_width) / 2
            bed_y = depth - bed_depth
            
            wall1 = FloorPlanGenerator._create_wall(
                doc, f'Floor{floor}_Unit{unit}_BedWall1',
                bed_x, bed_y, bed_x + bed_width, bed_y, 0.25
            )
            wall2 = FloorPlanGenerator._create_wall(
                doc, f'Floor{floor}_Unit{unit}_BedWall2',
                bed_x, bed_y, bed_x, bed_y + bed_depth, 0.25
            )
            wall3 = FloorPlanGenerator._create_wall(
                doc, f'Floor{floor}_Unit{unit}_BedWall3',
                bed_x + bed_width, bed_y, bed_x + bed_width, bed_y + bed_depth, 0.25
            )
            interior_walls.extend([wall1, wall2, wall3])
            
        elif bedrooms == 2:
            # 2-bed layout
            # Split width into 2 bedrooms at back
            bed_width = (width - FloorPlanGenerator.WALL_THICKNESS) / 2
            bed_depth = depth * 0.35
            
            # Bedroom 1
            wall1 = FloorPlanGenerator._create_wall(
                doc, f'Floor{floor}_Unit{unit}_Bed1Wall',
                0, depth - bed_depth, width/2, depth - bed_depth, 0.25
            )
            wall2 = FloorPlanGenerator._create_wall(
                doc, f'Floor{floor}_Unit{unit}_BedDivider',
                width/2, depth - bed_depth, width/2, depth, 0.25
            )
            # Bedroom 2
            wall3 = FloorPlanGenerator._create_wall(
                doc, f'Floor{floor}_Unit{unit}_Bed2Wall',
                width/2, depth - bed_depth, width, depth - bed_depth, 0.25
            )
            interior_walls.extend([wall1, wall2, wall3])
        
        # Bathroom (always at front corner)
        bath_width = 5.0
        bath_depth = 8.0
        bath_x = width - bath_width - FloorPlanGenerator.WALL_THICKNESS
        bath_y = FloorPlanGenerator.WALL_THICKNESS
        
        bath_wall1 = FloorPlanGenerator._create_wall(
            doc, f'Floor{floor}_Unit{unit}_BathWall1',
            bath_x, bath_y, bath_x, bath_y + bath_depth, 0.25
        )
        bath_wall2 = FloorPlanGenerator._create_wall(
            doc, f'Floor{floor}_Unit{unit}_BathWall2',
            bath_x, bath_y + bath_depth, bath_x + bath_width, bath_y + bath_depth, 0.25
        )
        interior_walls.extend([bath_wall1, bath_wall2])
        
        # Kitchen/Living area (remaining space)
        # Just annotate with text lines
        
        doc.recompute()
        return outer_wall, interior_walls
    
    @staticmethod
    def _create_rectangle(doc, name, x, y, w, h, thickness):
        """Create rectangular wall outline"""
        # Bottom wall
        bottom = doc.addObject('Part::Box', f'{name}_Bottom')
        bottom.Length = w
        bottom.Width = thickness
        bottom.Height = 0.1
        bottom.Placement.Base = App.Vector(x, y, 0)
        
        # Top wall
        top = doc.addObject('Part::Box', f'{name}_Top')
        top.Length = w
        top.Width = thickness
        top.Height = 0.1
        top.Placement.Base = App.Vector(x, y + h - thickness, 0)
        
        # Left wall
        left = doc.addObject('Part::Box', f'{name}_Left')
        left.Length = thickness
        left.Width = h - 2*thickness
        left.Height = 0.1
        left.Placement.Base = App.Vector(x, y + thickness, 0)
        
        # Right wall
        right = doc.addObject('Part::Box', f'{name}_Right')
        right.Length = thickness
        right.Width = h - 2*thickness
        right.Height = 0.1
        right.Placement.Base = App.Vector(x + w - thickness, y + thickness, 0)
        
        return [bottom, top, left, right]
    
    @staticmethod
    def _create_wall(doc, name, x1, y1, x2, y2, thickness):
        """Create a wall segment between two points"""
        length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        angle = 0
        if x2 != x1:
            angle = (y2 - y1) / (x2 - x1)
        
        wall = doc.addObject('Part::Box', name)
        wall.Length = max(thickness, abs(x2 - x1))
        wall.Width = max(thickness, abs(y2 - y1))
        wall.Height = 0.1
        wall.Placement.Base = App.Vector(min(x1, x2), min(y1, y2), 0)
        
        return wall


class ElevationGenerator:
    """Generate building elevations"""
    
    @staticmethod
    def generate_elevations(doc, params):
        """Generate front, rear, left, and right elevations"""
        width = params['width']
        height = params['height'] * params['stories']
        
        # Front elevation
        front = ElevationGenerator._create_elevation(
            doc, 'Elevation_Front', 0, 0, width, height
        )
        
        # Rear elevation
        rear = ElevationGenerator._create_elevation(
            doc, 'Elevation_Rear', 0, -5, width, height
        )
        
        # Left elevation
        left = ElevationGenerator._create_elevation(
            doc, 'Elevation_Left', -5, 0, params['depth'], height
        )
        
        # Right elevation
        right = ElevationGenerator._create_elevation(
            doc, 'Elevation_Right', width + 5, 0, params['depth'], height
        )
        
        doc.recompute()
        return front, rear, left, right
    
    @staticmethod
    def _create_elevation(doc, name, x, y, width, height):
        """Create elevation rectangle with roof line"""
        # Wall outline
        outline = doc.addObject('Part::Box', f'{name}_Outline')
        outline.Length = width
        outline.Width = 0.1
        outline.Height = height
        outline.Placement.Base = App.Vector(x, y, 0)
        
        # Roof (triangle for gable)
        if width > 0:
            roof = doc.addObject('Part::Box', f'{name}_Roof')
            roof.Length = width + 2  # Overhang
            roof.Width = 0.1
            roof.Height = 3  # Roof height
            roof.Placement.Base = App.Vector(x - 1, y, height)
        
        return outline


class PlanSetGenerator:
    """Master orchestrator for generating complete plan sets"""
    
    def __init__(self, output_dir='/Users/davidschy/geniinow-projects/modules/generated_plans'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.detail_library = '/Users/davidschy/geniinow-projects/modules/detail_library'
        
    def generate_from_prompt(self, prompt, project_name=None):
        """Generate complete plan set from a text prompt"""
        # Parse prompt
        params = PromptParser.parse(prompt)
        
        # Generate project name if not provided
        if not project_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            project_name = f"PlanSet_{params['type']}_{params['width']}x{params['depth']}_{timestamp}"
        
        params['project_name'] = project_name
        
        # Design modules
        modules = ModuleDesigner.design_modules(params)
        params['modules'] = modules
        
        # Create master document
        doc = App.newDocument(project_name)
        
        # Generate floor plans
        for story in range(1, params['stories'] + 1):
            for unit in range(1, params['unit_count'] + 1):
                FloorPlanGenerator.generate_floor_plan(doc, params, story, unit)
        
        # Generate elevations
        ElevationGenerator.generate_elevations(doc, params)
        
        # Save project
        project_path = os.path.join(self.output_dir, f'{project_name}.FCStd')
        doc.saveAs(project_path)
        App.closeDocument(project_name)
        
        # Generate metadata
        metadata = {
            'project_name': project_name,
            'prompt': prompt,
            'parameters': params,
            'generated_at': datetime.now().isoformat(),
            'file_path': project_path
        }
        
        meta_path = os.path.join(self.output_dir, f'{project_name}.json')
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Plan set generated: {project_name}")
        print(f"  FreeCAD model: {project_path}")
        print(f"  Metadata: {meta_path}")
        print(f"  Modules: {len(modules)}")
        for m in modules:
            print(f"    - {m['id']}: {m['width']:.1f}' x {m['depth']:.1f}' x {m['height']:.1f}' ({m['type']})")
        
        return metadata
    
    def generate_sheets(self, project_name):
        """Generate individual drawing sheets from project"""
        # This would create TechDraw pages for each sheet
        # A0.0 Legend, A1.0 Plans, E1.0 Electrical, P1.0 Plumbing, etc.
        pass


def demo():
    """Demo the plan set generator"""
    generator = PlanSetGenerator()
    
    # Test prompts
    prompts = [
        "20x32 2-bed 2-bath duplex, 2-story, SIP construction, Hanford CA",
        "24x40 3-bed 2-bath single family, 1-story, SIP, Fresno CA",
    ]
    
    for prompt in prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print('='*60)
        generator.generate_from_prompt(prompt)


if __name__ == "__main__":
    demo()
