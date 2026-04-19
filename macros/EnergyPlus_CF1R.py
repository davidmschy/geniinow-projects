"""
EnergyPlus_CF1R.py - Title 24 CF1R-ENV and CF1R-PRF calculations

Generates compliance forms for:
- CF1R-ENV: Envelope efficiency (U-factors, area-weighted assemblies)
- CF1R-PRF: Performance compliance ( modeled vs standard building)

Usage:
    python3 EnergyPlus_CF1R.py --project-data /path/to/project.json
"""

import json, math
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Assembly:
    name: str
    u_factor: float  # BTU/(hr·ft²·°F)
    area_sqft: float
    description: str

@dataclass
class CF1RResults:
    envelope_score: float
    total_ua: float
    standard_ua: float
    compliance_ratio: float
    status: str
    failures: List[str]

class CF1RCalculator:
    """Title 24 Part 6 CF1R calculation engine."""
    
    # Title 24 Table 140.3-B baseline U-factors (Climate Zone 12 - Fresno)
    BASELINE_U = {
        "wood_frame_wall": 0.051,
        "metal_frame_wall": 0.077,
        "ceiling_roof": 0.027,
        "floor": 0.029,
        "slab_edge": 0.70,
        "window": 0.32,
        "skylight": 0.46,
        "opaque_door": 0.20,
        "swinging_door": 0.50,
    }
    
    # SHGC baselines
    BASELINE_SHGC = {
        "window": 0.25,
        "skylight": 0.30,
    }
    
    def __init__(self, project_data: dict):
        self.data = project_data
        self.dwelling = project_data.get("dwelling_specifications", {})
        self.sip = project_data.get("sip_specifications", {})
        self.modules = project_data.get("modules", [])
        self.assemblies: List[Assembly] = []
        self._build_assemblies()
    
    def _build_assemblies(self):
        """Build thermal assembly list from project specs."""
        sip = self.sip
        width = self.dwelling.get("width_ft", 20)
        depth = self.dwelling.get("depth_ft", 32)
        height = self.dwelling.get("height_ft", 10.5)
        
        # Calculate surface areas
        floor_area = width * depth
        wall_area = 2 * (width + depth) * height
        roof_area = width * depth * 1.15  # pitched roof factor
        
        # SIP wall assembly (ICC-ESR-5318)
        wall_u = sip.get("wall_r_value", 29.3)
        if wall_u > 0:
            wall_u = 1.0 / wall_u  # Convert R to U
        else:
            wall_u = 0.034  # default for 6.5" SIP
        
        self.assemblies.append(Assembly(
            name="SIP Wall",
            u_factor=wall_u,
            area_sqft=wall_area,
            description=f"{sip.get('wall_thickness_in', 6.5)}\" SIP wall, R-{1/wall_u:.1f}"
        ))
        
        # SIP roof assembly
        roof_u = sip.get("roof_r_value", 31.4)
        if roof_u > 0:
            roof_u = 1.0 / roof_u
        else:
            roof_u = 0.032
        
        self.assemblies.append(Assembly(
            name="SIP Roof",
            u_factor=roof_u,
            area_sqft=roof_area,
            description=f"{sip.get('roof_thickness_in', 8.25)}\" SIP roof, R-{1/roof_u:.1f}"
        ))
        
        # Floor (14-gauge C-channel + insulation)
        self.assemblies.append(Assembly(
            name="Steel Floor",
            u_factor=0.029,
            area_sqft=floor_area,
            description="14-ga C-channel steel subfloor with insulation"
        ))
        
        # Windows (default if not specified)
        win_area = floor_area * 0.15  # 15% WWR typical
        self.assemblies.append(Assembly(
            name="Window",
            u_factor=0.30,
            area_sqft=win_area,
            description="Double-pane low-E vinyl window"
        ))
    
    def calculate_cf1r_env(self) -> dict:
        """Generate CF1R-ENV: Envelope efficiency report."""
        total_ua = 0.0
        standard_ua = 0.0
        failures = []
        
        for asm in self.assemblies:
            ua = asm.u_factor * asm.area_sqft
            total_ua += ua
            
            # Map to baseline
            baseline_key = self._map_to_baseline(asm.name)
            baseline_u = self.BASELINE_U.get(baseline_key, asm.u_factor)
            standard_ua += baseline_u * asm.area_sqft
            
            # Check compliance
            if asm.u_factor > baseline_u * 1.05:  # 5% tolerance
                failures.append(
                    f"{asm.name}: U={asm.u_factor:.4f} exceeds baseline {baseline_u:.4f}"
                )
        
        compliance_ratio = total_ua / standard_ua if standard_ua > 0 else 1.0
        
        # Fresno Climate Zone 12 requirements
        # Total UA must be <= standard building UA
        status = "PASS" if compliance_ratio <= 1.0 and not failures else "FAIL"
        
        return {
            "form": "CF1R-ENV",
            "climate_zone": "12",
            "city": self.data.get("lot_information", {}).get("city", "Fresno"),
            "total_ua_btu_hr_f": round(total_ua, 2),
            "standard_ua_btu_hr_f": round(standard_ua, 2),
            "compliance_ratio": round(compliance_ratio, 4),
            "status": status,
            "assemblies": [
                {
                    "name": a.name,
                    "u_factor": a.u_factor,
                    "area_sqft": a.area_sqft,
                    "ua": round(a.u_factor * a.area_sqft, 2),
                    "description": a.description
                }
                for a in self.assemblies
            ],
            "failures": failures
        }
    
    def calculate_cf1r_prf(self) -> dict:
        """Generate CF1R-PRF: Performance compliance."""
        env = self.calculate_cf1r_env()
        
        # Simplified performance model
        # Full EnergyPlus modeling would go here
        floor_area = sum(a.area_sqft for a in self.assemblies if "Floor" in a.name)
        
        # Standard design energy (kBtu/ft²/yr)
        standard_energy = 25.0  # Climate Zone 12 reference
        
        # Proposed design energy (adjusted by envelope UA ratio)
        proposed_energy = standard_energy * env["compliance_ratio"]
        
        # TDV (Time Dependent Valuation) compliance
        tdv_compliance = proposed_energy <= standard_energy * 1.0
        
        return {
            "form": "CF1R-PRF",
            "climate_zone": "12",
            "floor_area_sqft": floor_area,
            "standard_energy_kbtu_ft2_yr": standard_energy,
            "proposed_energy_kbtu_ft2_yr": round(proposed_energy, 2),
            "tdv_compliance": tdv_compliance,
            "envelope_multiplier": env["compliance_ratio"],
            "status": "PASS" if tdv_compliance else "FAIL",
            "note": "Simplified calculation. Full EnergyPlus modeling recommended for submission."
        }
    
    def _map_to_baseline(self, name: str) -> str:
        name_lower = name.lower()
        if "wall" in name_lower:
            return "wood_frame_wall" if "sip" in name_lower else "metal_frame_wall"
        if "roof" in name_lower or "ceiling" in name_lower:
            return "ceiling_roof"
        if "floor" in name_lower:
            return "floor"
        if "window" in name_lower:
            return "window"
        if "skylight" in name_lower:
            return "skylight"
        if "door" in name_lower:
            return "opaque_door"
        return "wood_frame_wall"
    
    def generate_idf(self, output_path: str):
        """Generate EnergyPlus IDF file for full simulation."""
        # Simplified IDF generation
        idf_content = f"""! Generated by Genii Studio CF1R Calculator
! Climate Zone 12 - Fresno
Version, 22.2;

Building,
    GeniiHCD,                !- Name
    0.0000,                  !- North Axis 0
    Suburbs,                 !- Terrain
    0.04,                    !- Loads Convergence Tolerance Value
    0.4,                     !- Temperature Convergence Tolerance Value
    FullExterior,            !- Solar Distribution
    25,                      !- Maximum Number of Warmup Days
    6;                       !- Minimum Number of Warmup Days

! Zone definition
Zone,
    LivingZone,              !- Name
    0,                       !- Direction of Relative North
    0,                       !- X Origin
    0,                       !- Y Origin
    0,                       !- Z Origin
    1,                       !- Type
    1,                       !- Multiplier
    autocalculate,           !- Ceiling Height
    autocalculate;           !- Volume

! Simplified - full IDF would include surfaces, schedules, HVAC
"""
        with open(output_path, 'w') as f:
            f.write(idf_content)
        return output_path

def main():
    import os
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-data", required=True)
    parser.add_argument("--output", default=os.path.expanduser("~/geniinow-projects/output"))
    args = parser.parse_args()
    
    with open(args.project_data) as f:
        data = json.load(f)
    
    calc = CF1RCalculator(data)
    
    env = calc.calculate_cf1r_env()
    prf = calc.calculate_cf1r_prf()
    
    results = {
        "project": data.get("project_metadata", {}),
        "cf1r_env": env,
        "cf1r_prf": prf,
        "generated_at": __import__('datetime').datetime.now().isoformat()
    }
    
    output_file = os.path.join(args.output, f"CF1R_{data['project_metadata']['apn']}.json")
    os.makedirs(args.output, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate IDF for EnergyPlus
    idf_file = os.path.join(args.output, f"Model_{data['project_metadata']['apn']}.idf")
    calc.generate_idf(idf_file)
    
    print(f"CF1R-ENV: {env['status']} (UA: {env['total_ua_btu_hr_f']:.2f})")
    print(f"CF1R-PRF: {prf['status']} (Energy: {prf['proposed_energy_kbtu_ft2_yr']:.2f} kBtu/ft²/yr)")
    print(f"Results: {output_file}")
    print(f"IDF: {idf_file}")

if __name__ == "__main__":
    main()
