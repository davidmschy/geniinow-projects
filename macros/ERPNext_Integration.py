"""
ERPNext_Integration.py

Auto-create ERPNext projects from pipeline output.
Links CAD files, creates tasks, updates manufacturing status.

Usage:
    python3 ERPNext_Integration.py --project-data /path/to/project.json --files "fcstd,step,json"

Requires env vars:
    ERPNEXT_URL=https://erp.geniinow.com
    ERPNEXT_API_KEY=your_key
    ERPNEXT_API_SECRET=your_secret
"""

import json, os, sys, urllib.request, urllib.parse
from pathlib import Path

class ERPNextCADConnector:
    def __init__(self, base_url=None, api_key=None, api_secret=None):
        self.base_url = (base_url or os.getenv("ERPNEXT_URL", "https://erp.geniinow.com")).rstrip('/')
        self.api_key = api_key or os.getenv("ERPNEXT_API_KEY")
        self.api_secret = api_secret or os.getenv("ERPNEXT_API_SECRET")
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.api_key and self.api_secret:
            self.headers['Authorization'] = f'token {self.api_key}:{self.api_secret}'
    
    def health_check(self):
        """Test connectivity."""
        try:
            result = self._get("api/method/ping")
            return {"ok": True, "response": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def create_project(self, project_data):
        """Create ERPNext Project from pipeline output."""
        meta = project_data.get("project_metadata", {})
        lot = project_data.get("lot_information", {})
        dwelling = project_data.get("dwelling_specifications", {})
        compliance = project_data.get("compliance_references", {})
        
        project_name = f"{meta.get('address', 'Unknown')} - {meta.get('apn', 'N/A')}"
        
        data = {
            "doctype": "Project",
            "project_name": project_name,
            "status": "Open",
            "project_type": "Factory Built Housing",
            "expected_start_date": "2026-05-01",
            "expected_end_date": "2026-08-01",
            "custom_apn": meta.get("apn"),
            "custom_address": meta.get("address"),
            "custom_latitude": lot.get("latitude"),
            "custom_longitude": lot.get("longitude"),
            "custom_county": lot.get("county"),
            "custom_state": lot.get("state"),
            "custom_lot_width_ft": lot.get("width_ft"),
            "custom_lot_depth_ft": lot.get("depth_ft"),
            "custom_elevation_ft": lot.get("elevation_ft"),
            "custom_slope_avg_percent": lot.get("slope_avg_percent"),
            "custom_dwelling_width_ft": dwelling.get("width_ft"),
            "custom_dwelling_depth_ft": dwelling.get("depth_ft"),
            "custom_module_type": dwelling.get("module_type"),
            "custom_sip_manufacturer": dwelling.get("sip_manufacturer"),
            "custom_hcd_compliance": "hcd" in compliance,
            "custom_title24_compliance": "title_24" in compliance,
            "custom_calgreen_compliance": "calgreen" in compliance,
            "custom_esr_reference": dwelling.get("sip_specifications", {}).get("esr"),
            "custom_manufacturing_completion": 0.0,
            "custom_github_repo": meta.get("github_repo")
        }
        
        result = self._post("api/resource/Project", data)
        return result
    
    def create_task(self, project_name, subject, description, assigned_to=None, priority="Medium"):
        """Create a task linked to the project."""
        data = {
            "doctype": "Task",
            "subject": subject,
            "description": description,
            "project": project_name,
            "priority": priority,
            "status": "Open",
            "exp_start_date": "2026-05-01",
            "exp_end_date": "2026-05-15"
        }
        if assigned_to:
            data["custom_assigned_agent"] = assigned_to
        
        return self._post("api/resource/Task", data)
    
    def create_standard_tasks(self, project_name):
        """Create standard engineering review tasks."""
        tasks = [
            ("Civil engineer review", "Review site plan, grading, and drainage. Check GIS vs civil discrepancies.", "Robert"),
            ("Structural engineer review", "Review SIP panel specs, foundation design, wind/seismic loads.", "Robert"),
            ("Title 24 energy compliance", "Complete CF1R-ENV and CF1R-PRF calculations. Verify HERS rater assignment.", "Antonio"),
            ("HCD plan check", "Submit to HCD for factory-built approval. Verify insignia requirements.", "Antonio"),
            ("Permit submission", "Submit complete plan set to city/county for building permit.", "Amber"),
        ]
        
        created = []
        for subject, desc, assignee in tasks:
            result = self.create_task(project_name, subject, desc, assignee)
            created.append({"subject": subject, "result": result})
        
        return created
    
    def upload_file(self, file_path, project_name):
        """Upload a CAD file as attachment to project."""
        # ERPNext file upload requires multipart form
        import mimetypes
        
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        body = []
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"'.encode())
        body.append(f"Content-Type: {mime_type}".encode())
        body.append(b"")
        body.append(file_data)
        body.append(f"--{boundary}--".encode())
        
        req_body = b"\r\n".join(body)
        
        headers = dict(self.headers)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        
        req = urllib.request.Request(
            f"{self.base_url}/api/method/upload_file",
            data=req_body,
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            return {"error": str(e)}
    
    def _get(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    
    def _post(self, endpoint, data):
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(
            url, data=json.dumps(data).encode(), headers=self.headers, method='POST'
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

def integrate_project(project_json_path, files_dir=None):
    """Full integration: create project + tasks + upload files."""
    
    connector = ERPNextCADConnector()
    
    # Health check
    health = connector.health_check()
    if not health["ok"]:
        print(f"⚠ ERPNext connection failed: {health.get('error')}")
        print("  Set ERPNEXT_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET env vars")
        return {"status": "error", "message": health.get("error")}
    
    with open(project_json_path) as f:
        data = json.load(f)
    
    # Create project
    print(f"Creating ERPNext project...")
    project = connector.create_project(data)
    
    if "error" in project:
        print(f"  Failed: {project['error']}")
        return {"status": "error", "project": project}
    
    project_name = project.get("data", {}).get("name", "Unknown")
    print(f"  Created: {project_name}")
    
    # Create standard tasks
    print(f"Creating tasks...")
    tasks = connector.create_standard_tasks(project_name)
    print(f"  {len(tasks)} tasks created")
    
    # Upload files if directory provided
    uploaded = []
    if files_dir and os.path.isdir(files_dir):
        print(f"Uploading files from {files_dir}...")
        for ext in [".FCStd", ".stp", ".json"]:
            for file in Path(files_dir).glob(f"*{ext}"):
                result = connector.upload_file(str(file), project_name)
                uploaded.append({"file": file.name, "status": "ok" if "error" not in result else "failed"})
        print(f"  {len(uploaded)} files uploaded")
    
    return {
        "status": "success",
        "project_name": project_name,
        "project": project,
        "tasks": len(tasks),
        "files": uploaded
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-data", required=True)
    parser.add_argument("--files-dir")
    parser.add_argument("--url")
    parser.add_argument("--api-key")
    parser.add_argument("--api-secret")
    args = parser.parse_args()
    
    # Override with CLI args if provided
    if args.url: os.environ["ERPNEXT_URL"] = args.url
    if args.api_key: os.environ["ERPNEXT_API_KEY"] = args.api_key
    if args.api_secret: os.environ["ERPNEXT_API_SECRET"] = args.api_secret
    
    result = integrate_project(args.project_data, args.files_dir)
    print(f"\nResult: {result['status']}")
    if result['status'] == 'success':
        print(f"Project: {result['project_name']}")
        print(f"Tasks: {result['tasks']}")
