"""
CivilPlanIngestor.py - Ingest civil engineer PDFs, compare to GIS data
"""

import json, re, sys, os
from pathlib import Path
from pypdf import PdfReader

class CivilPlanIngestor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.reader = PdfReader(str(pdf_path))
        self.text = "\n".join([page.extract_text() or "" for page in self.reader.pages])
    
    def extract_address(self):
        patterns = [
            r'(\d+\s+N\s+[A-Z]+\s+(?:DRIVE|ST|AVE|ROAD|BLVD|WAY|DR),?\s+[A-Z\s]+(?:\d{5}))',
            r'(\d+\s+[A-Z]+\s+(?:DRIVE|ST|AVE|ROAD|BLVD|WAY|DR),?\s+FRESNO\s+CALIFORNIA\s+\d{5})',
        ]
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_apn(self):
        patterns = [
            r'APN[S]?\s+(\d{3}-\d{3}-\d{2,3})',
            r'APN[S]?\s*:?\s*(\d{9})',
        ]
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_elevations(self):
        ff_match = re.search(r'FF\s*=\s*(\d+\.?\d*)', self.text)
        finished_floor = float(ff_match.group(1)) if ff_match else None
        
        all_numbers = re.findall(r'\b(29\d\.\d{2})\b', self.text)
        contour_elevs = sorted(list(set([float(n) for n in all_numbers])))
        
        drain_pattern = r'INV\s*=\s*(\d+\.?\d*)'
        inverts = [float(m) for m in re.findall(drain_pattern, self.text)]
        
        grate_pattern = r'GRATE\s*=\s*(\d+\.?\d*)'
        grates = [float(m) for m in re.findall(grate_pattern, self.text)]
        
        return {
            "finished_floor_ft": finished_floor,
            "contour_elevations_ft": contour_elevs,
            "drain_inverts_ft": inverts,
            "drain_grates_ft": grates,
            "min_elevation": min(contour_elevs) if contour_elevs else None,
            "max_elevation": max(contour_elevs) if contour_elevs else None
        }
    
    def extract_setbacks(self):
        front = re.search(r'(?:front|FRONT)\s*(?:setback|SETBACK)?[\s:=]*(\d+)', self.text)
        side = re.search(r'(?:side|SIDE)\s*(?:setback|SETBACK)?[\s:=]*(\d+)', self.text)
        rear = re.search(r'(?:rear|REAR)\s*(?:setback|SETBACK)?[\s:=]*(\d+)', self.text)
        return {
            "front_ft": int(front.group(1)) if front else 25,
            "side_ft": int(side.group(1)) if side else 5,
            "rear_ft": int(rear.group(1)) if rear else 20
        }
    
    def extract_drainage(self):
        inlets = []
        pattern = r'PROPOSED\s+SD\s+DRAIN\s*\(?(\w+)\)?\s*GRATE\s*=\s*(\d+\.?\d*)\s*INV\s*=\s*(\d+\.?\d*)'
        for match in re.finditer(pattern, self.text, re.IGNORECASE):
            inlets.append({
                "type": match.group(1),
                "grate_ft": float(match.group(2)),
                "invert_ft": float(match.group(3))
            })
        slope_match = re.search(r'MIN\s+SLOPE\s*=\s*(\d+\.?\d*)', self.text)
        return {
            "inlets": inlets,
            "pipe_slope_min": float(slope_match.group(1)) if slope_match else 0.005
        }
    
    def extract_utilities(self):
        return {
            "water_service": bool(re.search(r'WATER\s+SERVICE', self.text, re.IGNORECASE)),
            "sewer_service": bool(re.search(r'SEWER\s+SERVICE', self.text, re.IGNORECASE)),
            "electric_service": bool(re.search(r'POWER|ELECTRIC', self.text, re.IGNORECASE))
        }
    
    def extract_project_info(self):
        proj_match = re.search(r'[Pp](\d{2}-\d{5})', self.text)
        sheet_match = re.search(r'(C\d{3})', self.text)
        scale_match = re.search(r'SCALE\s+(\d+\s+IN\s*=\s+\d+\s+FT)', self.text)
        designer_match = re.search(r'DESIGNER\s*([A-Z]+)', self.text)
        return {
            "project_number": f"P{proj_match.group(1)}" if proj_match else None,
            "sheet": sheet_match.group(1) if sheet_match else None,
            "scale": scale_match.group(1) if scale_match else None,
            "designer": designer_match.group(1) if designer_match else None
        }
    
    def ingest(self):
        return {
            "source_pdf": os.path.basename(self.pdf_path),
            "address": self.extract_address(),
            "apn": self.extract_apn(),
            "elevations": self.extract_elevations(),
            "setbacks": self.extract_setbacks(),
            "drainage": self.extract_drainage(),
            "utilities": self.extract_utilities(),
            "project_info": self.extract_project_info()
        }

def check_discrepancies(civil_data, project_data=None):
    """Compare civil data to GIS/project data and flag discrepancies."""
    discrepancies = []
    
    gis_elev = None
    if project_data:
        # Try multiple paths for elevation data
        gis_data = project_data.get("gis_data", {})
        if "elevation" in gis_data:
            gis_elev = gis_data["elevation"].get("elevation_ft")
        elif "elevation_ft" in project_data.get("lot_information", {}):
            gis_elev = project_data["lot_information"]["elevation_ft"]
    
    civil_ff = civil_data.get("elevations", {}).get("finished_floor_ft")
    civil_min = civil_data.get("elevations", {}).get("min_elevation")
    
    if gis_elev and civil_ff:
        diff = abs(gis_elev - civil_ff)
        if diff > 3:
            discrepancies.append({
                "type": "elevation",
                "severity": "warning",
                "message": f"GIS elevation ({gis_elev}') differs from civil FF ({civil_ff}') by {diff:.1f}'",
                "note": "May be due to different datum or SRTM 90m resolution"
            })
    
    if gis_elev and civil_min:
        if civil_min > gis_elev + 2:
            discrepancies.append({
                "type": "elevation_low",
                "severity": "info",
                "message": f"Civil min contour ({civil_min}') is higher than GIS elevation ({gis_elev}')",
                "note": "GIS may be reading nearby terrain, not building pad"
            })
    
    return discrepancies

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--gis-data")
    parser.add_argument("--output")
    args = parser.parse_args()
    
    print(f"Ingesting: {args.pdf}")
    ingestor = CivilPlanIngestor(args.pdf)
    civil_data = ingestor.ingest()
    
    project_data = None
    if args.gis_data:
        with open(args.gis_data) as f:
            project_data = json.load(f)
    
    discrepancies = check_discrepancies(civil_data, project_data)
    
    print(f"\n{'='*50}")
    print(f"CIVIL PLAN INGESTION")
    print(f"{'='*50}")
    print(f"Address: {civil_data['address']}")
    print(f"APN: {civil_data['apn']}")
    print(f"FF Elevation: {civil_data['elevations']['finished_floor_ft']} ft")
    print(f"Contour range: {civil_data['elevations']['min_elevation']} - {civil_data['elevations']['max_elevation']} ft")
    print(f"Storm inlets: {len(civil_data['drainage']['inlets'])}")
    print(f"Setbacks: F={civil_data['setbacks']['front_ft']}', S={civil_data['setbacks']['side_ft']}', R={civil_data['setbacks']['rear_ft']}'")
    
    if discrepancies:
        print(f"\n⚠ DISCREPANCIES:")
        for d in discrepancies:
            print(f"  [{d['severity'].upper()}] {d['message']}")
            print(f"    {d['note']}")
    else:
        print(f"\n✓ No significant discrepancies")
    
    if args.output:
        output = {"civil_data": civil_data, "discrepancies": discrepancies}
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved: {args.output}")
