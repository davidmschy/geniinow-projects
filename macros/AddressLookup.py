"""
AddressLookup.py

Lookup property data by address or APN.
Supports:
- Nominatim (OpenStreetMap) geocoding
- Fresno County Assessor (specific)
- General county GIS REST APIs

Usage:
    python AddressLookup.py --address "549 N Parkview, Fresno, CA"
    python AddressLookup.py --apn "449-341-009"
"""

import json, sys, os, urllib.request, urllib.parse

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def lookup_address(address):
    """Geocode address to lat/lon and structured data."""
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "GeniiStudio/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data:
                result = data[0]
                return {
                    "source": "nominatim",
                    "lat": float(result.get("lat", 0)),
                    "lon": float(result.get("lon", 0)),
                    "display_name": result.get("display_name"),
                    "address": result.get("address", {}),
                    "boundingbox": result.get("boundingbox"),
                    "osm_type": result.get("osm_type"),
                    "osm_id": result.get("osm_id")
                }
    except Exception as e:
        return {"error": str(e)}
    return {"error": "No results found"}

def lookup_apn_fresno(apn):
    """Fresno County specific APN lookup via their REST services."""
    # Fresno County GIS REST endpoint
    base = "https://services3.arcgis.com/Px1LMyVgYqPETlYc/ArcGIS/rest/services"
    
    # Try parcels layer
    parcel_url = f"{base}/Parcels_Public/FeatureServer/0/query"
    params = {
        "where": f"APN='{apn}'",
        "outFields": "*",
        "f": "json",
        "returnGeometry": "true"
    }
    
    try:
        url = f"{parcel_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "GeniiStudio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("features"):
                feat = data["features"][0]
                attrs = feat.get("attributes", {})
                geom = feat.get("geometry", {})
                return {
                    "source": "fresno_county_gis",
                    "apn": apn,
                    "attributes": attrs,
                    "geometry": geom,
                    "raw": feat
                }
    except Exception as e:
        return {"error": str(e), "note": "Fresno County GIS may require different endpoint"}
    
    return {"error": "APN not found in Fresno County GIS"}

def get_elevation_usgs(lat, lon):
    """Get elevation from USGS 3DEP."""
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeniiStudio/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get("results"):
                return {
                    "elevation_m": data["results"][0].get("elevation"),
                    "elevation_ft": data["results"][0].get("elevation", 0) * 3.28084,
                    "source": "usgs_srtm_90m"
                }
    except Exception as e:
        return {"error": str(e)}
    return {"error": "No elevation data"}

def build_project_data(address=None, apn=None, city=None, state="CA"):
    """Full lookup pipeline: address/APN → structured project data."""
    result = {
        "project_metadata": {},
        "lot_information": {},
        "geolocation": {},
        "elevation": {}
    }
    
    # Step 1: Geocode address
    if address:
        geo = lookup_address(address)
        if "error" not in geo:
            result["geolocation"] = geo
            addr = geo.get("address", {})
            result["project_metadata"]["address"] = address
            result["project_metadata"]["city"] = addr.get("city") or addr.get("town")
            result["project_metadata"]["county"] = addr.get("county")
            result["project_metadata"]["state"] = addr.get("state") or state
            result["project_metadata"]["zip"] = addr.get("postcode")
            
            # Get elevation
            elev = get_elevation_usgs(geo["lat"], geo["lon"])
            result["elevation"] = elev
    
    # Step 2: APN lookup (Fresno-specific for now)
    if apn:
        result["project_metadata"]["apn"] = apn
        if "fresno" in (result["project_metadata"].get("county", "")).lower():
            parcel = lookup_apn_fresno(apn)
            if "error" not in parcel:
                attrs = parcel.get("attributes", {})
                result["lot_information"]["apn"] = apn
                result["lot_information"]["geometry"] = parcel.get("geometry")
    
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", help="Property address")
    parser.add_argument("--apn", help="Assessor Parcel Number")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    if not args.address and not args.apn:
        parser.print_help()
        sys.exit(1)
    
    data = build_project_data(address=args.address, apn=args.apn)
    
    output = json.dumps(data, indent=2)
    print(output)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"\nSaved to: {args.output}")
