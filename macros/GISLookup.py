"""
GISLookup.py - Fetch GIS data for a property
"""
import json, urllib.request, urllib.parse, math

def get_elevation(lat, lon):
    """Get elevation from OpenTopography SRTM (primary, free, no API key)."""
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeniiStudio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("results"):
                r = data["results"][0]
                return {
                    "elevation_m": r.get("elevation"),
                    "elevation_ft": round(r.get("elevation", 0) * 3.28084, 1),
                    "resolution_m": 90,
                    "source": "SRTM 90m (OpenTopography)"
                }
    except Exception as e:
        return {"error": str(e)}
    return {"error": "No elevation data"}

def get_slope(lat, lon, spacing_ft=50, grid=3):
    """Sample elevation grid to estimate slope."""
    spacing_deg = spacing_ft / 364000.0
    samples = []
    for dy in range(-grid//2, grid//2 + 1):
        for dx in range(-grid//2, grid//2 + 1):
            e = get_elevation(lat + dy*spacing_deg, lon + dx*spacing_deg)
            if "elevation_ft" in e:
                samples.append({
                    "dx_ft": dx * spacing_ft,
                    "dy_ft": dy * spacing_ft,
                    "elev_ft": e["elevation_ft"]
                })
    
    if len(samples) < 2:
        return {"error": "Insufficient samples"}
    
    elevs = [s["elev_ft"] for s in samples]
    max_drop = max(elevs) - min(elevs)
    diagonal_dist = math.sqrt(2) * grid * spacing_ft
    
    return {
        "sample_count": len(samples),
        "spacing_ft": spacing_ft,
        "min_elev_ft": round(min(elevs), 1),
        "max_elev_ft": round(max(elevs), 1),
        "range_ft": round(max_drop, 1),
        "avg_slope_percent": round((max_drop / diagonal_dist) * 100, 2),
        "max_slope_percent": round((max_drop / (grid * spacing_ft)) * 100, 2),
        "samples": samples
    }

def get_flood_zone(lat, lon):
    """Query FEMA flood zones via msc.fema.gov (public, no key)."""
    # FEMA's public map service
    url = "https://msc.fema.gov/portal/rest/services/PrelimDraft/MapServer/0/query"
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY",
        "f": "json"
    }
    try:
        url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "GeniiStudio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("features"):
                attrs = data["features"][0].get("attributes", {})
                return {
                    "flood_zone": attrs.get("FLD_ZONE", "Unknown"),
                    "zone_subtype": attrs.get("ZONE_SUBTY", "N/A"),
                    "source": "FEMA"
                }
            return {"flood_zone": "X (Outside flood zone)", "source": "FEMA"}
    except Exception as e:
        return {"error": str(e), "note": "FEMA service may be unavailable"}

def get_parcel_by_coords(lat, lon):
    """Generic parcel lookup - tries multiple county GIS endpoints."""
    # Fresno County parcels
    endpoints = [
        ("Fresno County", "https://services3.arcgis.com/Px1LMyVgYqPETlYc/ArcGIS/rest/services/Parcels_Public/FeatureServer/0"),
    ]
    
    for county_name, base_url in endpoints:
        try:
            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "f": "json"
            }
            url = f"{base_url}/query?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "GeniiStudio/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get("features"):
                    attrs = data["features"][0].get("attributes", {})
                    return {
                        "county": county_name,
                        "apn": attrs.get("APN") or attrs.get("APN_1"),
                        "acreage": attrs.get("ACREAGE") or attrs.get("Shape_Area"),
                        "land_use": attrs.get("LANDUSE"),
                        "zoning": attrs.get("ZONING"),
                        "source": county_name
                    }
        except Exception as e:
            continue
    
    return {"error": "No parcel found in known GIS databases", "note": "Manual lookup may be required"}

def build_gis_profile(lat, lon, county=None):
    """Full GIS profile."""
    profile = {
        "coordinates": {"lat": lat, "lon": lon},
        "elevation": get_elevation(lat, lon),
        "slope": get_slope(lat, lon),
        "flood": get_flood_zone(lat, lon),
        "parcel": get_parcel_by_coords(lat, lon)
    }
    return profile

if __name__ == "__main__":
    import argparse, math
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--county")
    parser.add_argument("--output")
    args = parser.parse_args()
    
    profile = build_gis_profile(args.lat, args.lon, args.county)
    print(json.dumps(profile, indent=2))
    if args.output:
        with open(args.output, "w") as f:
            json.dump(profile, f, indent=2)
