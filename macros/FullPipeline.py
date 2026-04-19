"""
FullPipeline.py - One command from Address/APN to complete plan set
"""

import sys, os, subprocess, json, argparse

sys.path.insert(0, os.path.expanduser("~/geniinow-projects/macros"))
from GenerateSitePlan import generate as generate_site_plan
from ComplianceEngine import run_compliance_check

def export_step(apn_clean):
    freecad_python = "/Applications/FreeCAD.app/Contents/Resources/bin/python"
    freecad_lib = "/Applications/FreeCAD.app/Contents/Resources/lib"
    fcstd_path = os.path.expanduser(f"~/geniinow-projects/output/SitePlan_{apn_clean}.FCStd")
    step_path = os.path.expanduser(f"~/geniinow-projects/output/SitePlan_{apn_clean}.stp")
    
    script = f"""
import FreeCAD, Part
doc = FreeCAD.openDocument('{fcstd_path}')
objs = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
Part.export(objs, '{step_path}')
print(f'Exported: {step_path}')
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = freecad_lib
    result = subprocess.run([freecad_python, "-c", script], capture_output=True, text=True, env=env)
    return result.stdout.strip()

def publish_github(project_data, apn_clean):
    from PlanSetPublisher import publish_to_github
    json_path = os.path.expanduser(f"~/geniinow-projects/output/SitePlan_{apn_clean}_data.json")
    return publish_to_github(project_data, json_path)

def run_full_pipeline(address=None, apn=None, **kwargs):
    print("=" * 60)
    print("GENII STUDIO - FULL PLAN SET PIPELINE")
    print("=" * 60)
    
    # Generate site plan
    print("\n[STEP 1/5] Generating site plan...")
    project_data = generate_site_plan(address=address, apn=apn, **kwargs)
    apn_clean = project_data['project_metadata']['apn'].replace('-', '_')
    
    # Export STEP
    print("\n[STEP 2/5] Exporting STEP file...")
    step_out = export_step(apn_clean)
    print(f"  {step_out}")
    
    # Compliance check
    print("\n[STEP 3/5] Running compliance check...")
    json_path = os.path.expanduser(f"~/geniinow-projects/output/SitePlan_{apn_clean}_data.json")
    compliance = run_compliance_check(json_path)
    score = compliance['summary']['compliance_score']
    print(f"  Score: {score}%")
    
    project_data['compliance_score'] = score
    project_data['compliance_report'] = compliance
    with open(json_path, "w") as f:
        json.dump(project_data, f, indent=2)
    
    # Publish to GitHub
    print("\n[STEP 4/5] Publishing to GitHub...")
    repo_name = f"site-plan-{apn_clean.lower()}"
    repo_url = f"https://github.com/davidmschy/{repo_name}"
    publish_github(project_data, apn_clean)
    print(f"  {repo_url}")
    
    # Summary
    meta = project_data.get("project_metadata", {})
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Project: {meta.get('address', 'N/A')}")
    print(f"APN: {meta.get('apn', 'N/A')}")
    print(f"Compliance: {score}%")
    print(f"GitHub: {repo_url}")
    print(f"Files:")
    print(f"  - SitePlan_{apn_clean}.FCStd")
    print(f"  - SitePlan_{apn_clean}.stp")
    print(f"  - SitePlan_{apn_clean}_data.json")
    print("=" * 60)
    
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
    
    run_full_pipeline(**vars(args))
