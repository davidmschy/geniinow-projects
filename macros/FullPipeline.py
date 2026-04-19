"""
FullPipeline.py - One-command deployment

Runs: Address → Geo → GIS → Site Plan → Floor Plan → Compliance → ERPNext → GitHub

Usage:
    python3 FullPipeline.py --address "549 N Parkview, Fresno, CA" --apn "449-341-009"
"""

import sys, os, json, subprocess
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/geniinow-projects/macros"))

def run_step(name, cmd, cwd=None):
    print(f"\n[{name}]")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:500]}")
        return None
    print(f"  OK")
    return result.stdout

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required=True)
    parser.add_argument("--apn", required=True)
    parser.add_argument("--lot-width", type=float, default=100)
    parser.add_argument("--lot-depth", type=float, default=100)
    parser.add_argument("--skip-erpnext", action="store_true", help="Skip ERPNext integration")
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub publishing")
    parser.add_argument("--skip-floorplan", action="store_true", help="Skip floor plan generation")
    args = parser.parse_args()
    
    output_dir = os.path.expanduser("~/geniinow-projects/output")
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*60)
    print("GENII STUDIO - FULL PIPELINE")
    print("="*60)
    print(f"Address: {args.address}")
    print(f"APN: {args.apn}")
    
    # Step 1: Generate site plan
    run_step("SITE PLAN",
        [sys.executable, "GenerateSitePlan.py",
         "--address", args.address,
         "--apn", args.apn,
         "--lot-width", str(args.lot_width),
         "--lot-depth", str(args.lot_depth),
         "--output", output_dir],
        cwd=os.path.expanduser("~/geniinow-projects/macros"))
    
    # Find generated data file
    data_file = None
    for f in Path(output_dir).glob(f"*_{args.apn.replace('-', '_')}_data.json"):
        data_file = str(f)
        break
    
    if not data_file:
        print("ERROR: No project data file found")
        return
    
    # Step 2: Floor plan
    if not args.skip_floorplan:
        run_step("FLOOR PLAN",
            [sys.executable, "FloorPlanGenerator.py",
             "--project-data", data_file,
             "--output", output_dir],
            cwd=os.path.expanduser("~/geniinow-projects/macros"))
    
    # Step 3: Compliance check
    run_step("COMPLIANCE",
        [sys.executable, "ComplianceEngine.py",
         "--project-data", data_file],
        cwd=os.path.expanduser("~/geniinow-projects/macros"))
    
    # Step 4: ERPNext integration
    if not args.skip_erpnext:
        run_step("ERPNEXT",
            [sys.executable, "ERPNext_Integration.py",
             "--project-data", data_file,
             "--files-dir", output_dir],
            cwd=os.path.expanduser("~/geniinow-projects/macros"))
    
    # Step 5: GitHub publishing
    if not args.skip_github:
        run_step("GITHUB",
            [sys.executable, "PlanSetPublisher.py",
             "--project-data", data_file],
            cwd=os.path.expanduser("~/geniinow-projects/macros"))
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Project data: {data_file}")
    print(f"Output: {output_dir}")

if __name__ == "__main__":
    main()
