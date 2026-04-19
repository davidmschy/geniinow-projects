"""
PlanSetPublisher.py

Publish generated plan sets to GitHub for collaboration:
1. Create repo per project (if not exists)
2. Git LFS for CAD files
3. Push project JSON, FCStd, STEP files
4. Create README with project summary

Usage:
    python3 PlanSetPublisher.py --project-data /path/to/project.json
"""

import json, os, subprocess, sys

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def publish_to_github(project_data, project_json_path):
    """Publish plan set to GitHub."""
    meta = project_data.get("project_metadata", {})
    apn = meta.get("apn", "UNKNOWN").replace("-", "_")
    repo_name = f"site-plan-{apn.lower()}"
    
    output_dir = os.path.expanduser("~/geniinow-projects/output")
    repo_dir = os.path.join(output_dir, repo_name)
    
    print(f"=== Publishing to GitHub: {repo_name} ===")
    
    # Check if repo exists on GitHub
    stdout, stderr, rc = run_cmd(f"gh repo view davidmschy/{repo_name}")
    repo_exists = rc == 0
    
    if not repo_exists:
        print(f"[1/5] Creating GitHub repo: davidmschy/{repo_name}")
        stdout, stderr, rc = run_cmd(f"gh repo create {repo_name} --private --description \"Site plan for APN {meta.get('apn')}\" --gitignore Python")
        if rc != 0 and "already exists" not in stderr:
            print(f"Error creating repo: {stderr}")
            return False
    else:
        print(f"[1/5] Repo exists: davidmschy/{repo_name}")
    
    # Setup local repo
    print(f"[2/5] Setting up local repo...")
    os.makedirs(repo_dir, exist_ok=True)
    
    # Init git if needed
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        run_cmd("git init", cwd=repo_dir)
        run_cmd(f"git remote add origin https://github.com/davidmschy/{repo_name}.git", cwd=repo_dir)
    
    # Setup Git LFS
    run_cmd("git lfs install", cwd=repo_dir)
    
    # Create .gitattributes for CAD files
    gitattrs = """*.FCStd filter=lfs diff=lfs merge=lfs -text
*.stp filter=lfs diff=lfs merge=lfs -text
*.step filter=lfs diff=lfs merge=lfs -text
*.dwg filter=lfs diff=lfs merge=lfs -text
*.dxf filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text
"""
    with open(os.path.join(repo_dir, ".gitattributes"), "w") as f:
        f.write(gitattrs)
    
    # Copy project files
    print(f"[3/5] Copying project files...")
    fcstd_file = f"SitePlan_{apn}.FCStd"
    step_file = f"SitePlan_{apn}.stp"
    json_file = f"SitePlan_{apn}_data.json"
    
    for fname in [fcstd_file, step_file, json_file]:
        src = os.path.join(output_dir, fname)
        if os.path.exists(src):
            run_cmd(f"cp \"{src}\" \"{repo_dir}/\"")
    
    # Generate README
    readme = f"""# Site Plan - APN {meta.get('apn', 'N/A')}

## Property
- **Address:** {meta.get('address', 'N/A')}
- **APN:** {meta.get('apn', 'N/A')}
- **City:** {meta.get('city', 'N/A')}, {meta.get('state', 'CA')} {meta.get('zip', '')}
- **County:** {meta.get('county', 'N/A')}

## Lot
- **Dimensions:** {project_data.get('lot_information', {}).get('width_ft', 'N/A')}' x {project_data.get('lot_information', {}).get('depth_ft', 'N/A')}'
- **Area:** {project_data.get('lot_information', {}).get('area_acres', 'N/A')} acres
- **Zoning:** {project_data.get('lot_information', {}).get('zoning', 'N/A')}
- **Elevation:** {project_data.get('lot_information', {}).get('elevation_ft', 'N/A')} ft
- **Slope:** {project_data.get('lot_information', {}).get('slope_avg_percent', 'N/A')}% avg

## Dwelling
- **Type:** {project_data.get('dwelling_specifications', {}).get('type', 'N/A')}
- **Size:** {project_data.get('dwelling_specifications', {}).get('width_ft', 'N/A')}' x {project_data.get('dwelling_specifications', {}).get('depth_ft', 'N/A')}'
- **Total SF:** {project_data.get('dwelling_specifications', {}).get('total_sf', 'N/A')}
- **Stories:** {project_data.get('dwelling_specifications', {}).get('stories', 'N/A')}

## SIP Specifications
- **Manufacturer:** {project_data.get('sip_specifications', {}).get('manufacturer', 'N/A')}
- **ESR:** {project_data.get('sip_specifications', {}).get('esr', 'N/A')}
- **Walls:** {project_data.get('sip_specifications', {}).get('wall_panels', 'N/A')}
- **Roof:** {project_data.get('sip_specifications', {}).get('roof_panels', 'N/A')}

## Files
- `SitePlan_{apn}.FCStd` - FreeCAD native file
- `SitePlan_{apn}.stp` - STEP file for engineers
- `SitePlan_{apn}_data.json` - Structured project data

## Compliance
Score: {project_data.get('compliance_score', 'N/A')}%

## Generated
- **Date:** {meta.get('generated_date', 'N/A')}
- **By:** {meta.get('generated_by', 'Genii Studio AI')}

## Collaboration
Engineers: Please clone this repo, open the .FCStd file in FreeCAD, and submit changes via PR.
"""
    with open(os.path.join(repo_dir, "README.md"), "w") as f:
        f.write(readme)
    
    # Commit and push
    print(f"[4/5] Committing...")
    run_cmd("git add -A", cwd=repo_dir)
    stdout, stderr, rc = run_cmd('git commit -m "Initial site plan generation"', cwd=repo_dir)
    if rc != 0 and "nothing to commit" not in stderr:
        print(f"Commit issue: {stderr}")
    
    print(f"[5/5] Pushing to GitHub...")
    stdout, stderr, rc = run_cmd("git push -u origin main 2>&1 || git push -u origin master 2>&1", cwd=repo_dir)
    if rc != 0:
        print(f"Push issue: {stderr}")
    else:
        print(f"Published: https://github.com/davidmschy/{repo_name}")
    
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-data", required=True)
    args = parser.parse_args()
    
    with open(args.project_data) as f:
        data = json.load(f)
    
    publish_to_github(data, args.project_data)
