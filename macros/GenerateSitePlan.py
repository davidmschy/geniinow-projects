"""
GenerateSitePlan.py - System Python entry point

Full pipeline:
  Address/APN → Geocode → GIS (elevation, slope, flood) → Project JSON → FreeCAD Site Plan

Usage:
    python3 GenerateSitePlan.py --address "549 N Parkview, Fresno, CA" --apn "449-341-009"
"""

import sys, os, json, subprocess, argparse

sys.path.insert(0, os.path.expanduser("~/geniinow-projects/macros"))
from AddressLookup import build_project_data
from GISLookup import build_gis_profile

def generate(address=None, apn=None, **kwargs):
    print("=" * 50)
    print("GENII STUDIO - SITE PLAN GENERATOR")
    print("=" * 50)
    print(f"Address: {address or 'N/A'}")
    print(f"APN: {apn or 'N/A'}")
    print()
    
    # Step 1: Geocode + basic lookup
    print("[1/4] Property lookup...")
    lookup_data = build_project_data(address=address, apn=apn)
    geo = lookup_data.get("geolocation", {})
    
    lat = geo.get("lat")
    lon = geo.get("lon")
    county = lookup_data["project_metadata"].get("county")
    
    if lat and lon:
        print(f"  Coordinates: {lat}, {lon}")
        print(f"  County: {county}")
        elev = lookup_data.get("elevation", {})
        if "elevation_ft" in elev:
            print(f"  Elevation: {elev['elevation_ft']:.1f} ft")
    else:
        print("  Warning: Could not geocode")
    
    # Step 2: GIS profile
    print("\n[2/4] GIS analysis...")
    gis_data = {}
    if lat and lon:
        gis_data = build_gis_profile(lat, lon, county)
        elev = gis_data.get("elevation", {})
        slope = gis_data.get("slope", {})
        
        if "elevation_ft" in elev:
            print(f"  Elevation: {elev['elevation_ft']} ft ({elev['source']})")
        if "avg_slope_percent" in slope:
            print(f"  Slope: {slope['avg_slope_percent']}% avg, {slope['max_slope_percent']}% max")
            print(f"  Grade range: {slope['min_elev_ft']} - {slope['max_elev_ft']} ft")
        flood = gis_data.get("flood", {})
        if "flood_zone" in flood:
            print(f"  Flood zone: {flood['flood_zone']}")
    else:
        print("  Skipped (no coordinates)")
    
    # Step 3: Build project schema
    print("\n[3/4] Building project schema...")
    project_data = {
        "project_metadata": {
            "apn": apn or lookup_data["project_metadata"].get("apn", "UNKNOWN"),
            "address": address or lookup_data["project_metadata"].get("address", ""),
            "city": lookup_data["project_metadata"].get("city", ""),
            "county": county or "",
            "state": lookup_data["project_metadata"].get("state", "CA"),
            "zip": lookup_data["project_metadata"].get("zip", ""),
            "developer": "HOME GENII DEVELOPMENT LLC",
            "designer": "PreFab Innovations",
            "generated_by": "Genii Studio AI",
            "generated_date": subprocess.check_output(["date", "+%Y-%m-%d"]).decode().strip()
        },
        "lot_information": {
            "width_ft": kwargs.get("lot_width", 100),
            "depth_ft": kwargs.get("lot_depth", 100),
            "area_sf": kwargs.get("lot_width", 100) * kwargs.get("lot_depth", 100),
            "area_acres": round(kwargs.get("lot_width", 100) * kwargs.get("lot_depth", 100) / 43560, 2),
            "zoning": kwargs.get("zoning", "R-3N"),
            "elevation_ft": gis_data.get("elevation", {}).get("elevation_ft"),
            "slope_avg_percent": gis_data.get("slope", {}).get("avg_slope_percent"),
            "slope_max_percent": gis_data.get("slope", {}).get("max_slope_percent"),
            "latitude": lat,
            "longitude": lon,
            "flood_zone": gis_data.get("flood", {}).get("flood_zone")
        },
        "dwelling_specifications": {
            "type": kwargs.get("dwelling_type", "2-story duplex"),
            "width_ft": kwargs.get("dwelling_width", 21.5),
            "depth_ft": kwargs.get("dwelling_depth", 31),
            "total_sf": kwargs.get("dwelling_sf", 1333),
            "stories": kwargs.get("stories", 2),
            "construction_type": "Factory-built / prefab modular with SIP walls/roof"
        },
        "compliance_references": {
            "title_25": "CCR §3070",
            "hsc_19990": "HSC §19990",
            "hcd": "HCD Factory-built Handbook",
            "title_24": "T-24 energy compliance required",
            "calgreen": "CALGreen Tier 1 required",
            "esr_sip": "ICC-ES ESR-5318 (PREFLEX SIPs)"
        },
        "sip_specifications": {
            "manufacturer": "PREFLEX, Inc.",
            "esr": "ESR-5318",
            "wall_panels": "6.5 inch SIP (R-24.7)",
            "roof_panels": "8.25 inch SIP (R-31.4)",
            "wall_r_value": 24.7,
            "roof_r_value": 31.4
        },
        "gis_data": gis_data
    }
    
    print(f"  Lot: {project_data['lot_information']['width_ft']}' x {project_data['lot_information']['depth_ft']}'")
    print(f"  Dwelling: {project_data['dwelling_specifications']['width_ft']}' x {project_data['dwelling_specifications']['depth_ft']}'")
    print(f"  SIP: {project_data['sip_specifications']['wall_panels']}")
    
    # Save project JSON
    output_dir = os.path.expanduser("~/geniinow-projects/output")
    os.makedirs(output_dir, exist_ok=True)
    apn_clean = project_data['project_metadata']['apn'].replace('-', '_')
    json_path = os.path.join(output_dir, f"SitePlan_{apn_clean}_data.json")
    with open(json_path, "w") as f:
        json.dump(project_data, f, indent=2)
    print(f"  Saved: {json_path}")
    
    # Step 4: Generate CAD
    print("\n[4/4] Generating FreeCAD site plan...")
    freecad_python = "/Applications/FreeCAD.app/Contents/Resources/bin/python"
    freecad_lib = "/Applications/FreeCAD.app/Contents/Resources/lib"
    
    cmd = [
        freecad_python,
        os.path.expanduser("~/geniinow-projects/macros/SitePlanGenerator.py"),
        "--project-data", json_path
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = freecad_lib
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(result.stdout.strip())
    
    print(f"\n{'=' * 50}")
    print("COMPLETE")
    print(f"{'=' * 50}")
    print(f"FreeCAD: {output_dir}/SitePlan_{apn_clean}.FCStd")
    print(f"Project: {json_path}")
    return project_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--address")
    parser.add_argument("--apn")
    parser.add_argument("--lot-width", type=float, default=100)
    parser.add_argument("--lot-depth", type=float, default=100)
    parser.add_argument("--dwelling-width", type=float, default=21.5)
    parser.add_argument("--dwelling-depth", type=float, default=31)
    parser.add_argument("--dwelling-sf", type=int, default=1333)
    parser.add_argument("--stories", type=int, default=2)
    parser.add_argument("--zoning", default="R-3N")
    parser.add_argument("--type", default="2-story duplex", dest="dwelling_type")
    args = parser.parse_args()
    
    generate(**vars(args))
