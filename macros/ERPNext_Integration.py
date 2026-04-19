"""
ERPNext Integration for Genii Studio CAD/BIM Workflow
Pushes BOMs, manufacturing status, and module data to ERPNext
"""
import json
import urllib.request
import urllib.parse

class ERPNextCADConnector:
    """Connects FreeCAD modules to ERPNext Project/Manufacturing workflow"""
    
    def __init__(self, base_url="http://localhost:8081", api_key=None, api_secret=None):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if api_key and api_secret:
            self.headers['Authorization'] = f'token {api_key}:{api_secret}'
    
    def create_project(self, project_name, module_count, site_address):
        """Create ERPNext Project for modular housing development"""
        data = {
            "doctype": "Project",
            "project_name": project_name,
            "expected_start_date": "2026-05-01",
            "expected_end_date": "2026-08-01",
            "status": "Open",
            "project_type": "Factory Built Housing",
            "custom_module_count": module_count,
            "custom_site_address": site_address,
            "custom_manufacturing_completion": 0.0
        }
        return self._post("api/resource/Project", data)
    
    def create_module_item(self, module_name, module_type, dimensions, project):
        """Create Module item in ERPNext"""
        data = {
            "doctype": "Item",
            "item_code": module_name,
            "item_name": f"HCD Module {module_type}",
            "item_group": "Modular Housing Units",
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "custom_module_width_ft": dimensions.get('width'),
            "custom_module_length_ft": dimensions.get('length'),
            "custom_module_height_ft": dimensions.get('height'),
            "custom_sip_wall_thickness_in": dimensions.get('wall_thickness', 6.5),
            "custom_steel_gauge": dimensions.get('steel_gauge', 14),
            "custom_project": project,
            "custom_manufacturing_status": "Planned"
        }
        return self._post("api/resource/Item", data)
    
    def create_bom(self, module_name, materials):
        """Create Bill of Materials for a module"""
        items = []
        for mat in materials:
            items.append({
                "item_code": mat['code'],
                "qty": mat['qty'],
                "uom": mat['uom'],
                "rate": mat.get('rate', 0)
            })
        
        data = {
            "doctype": "BOM",
            "item": module_name,
            "quantity": 1,
            "items": items,
            "custom_is_manufacturing_bom": 1
        }
        return self._post("api/resource/BOM", data)
    
    def update_manufacturing_status(self, module_name, status, completion_pct):
        """Update manufacturing completion status"""
        # Update the Item's custom fields
        data = {
            "custom_manufacturing_status": status,
            "custom_manufacturing_completion_pct": completion_pct
        }
        return self._put(f"api/resource/Item/{urllib.parse.quote(module_name)}", data)
    
    def _post(self, endpoint, data):
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode(),
            headers=self.headers,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            return {"error": str(e)}
    
    def _put(self, endpoint, data):
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=self.headers,
            method='PUT'
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            return {"error": str(e)}


def export_module_to_erpnext(doc, module_type="HCD_14x40", project_name="Test Project"):
    """
    FreeCAD macro entry point.
    Call from FreeCAD: import ERPNext_Integration; ERPNext_Integration.export_module_to_erpnext(FreeCAD.ActiveDocument)
    """
    connector = ERPNextCADConnector()
    
    # Extract dimensions from document
    dims = {"width": 14, "length": 40, "height": 10.5}
    
    # Create project if not exists
    project = connector.create_project(project_name, 1, "TBD")
    
    # Create module item
    module_name = f"{project_name}_{module_type}"
    item = connector.create_module_item(module_name, module_type, dims, project_name)
    
    # Standard HCD materials BOM
    materials = [
        {"code": "SIP-WALL-6.5", "qty": 180, "uom": "Sq Ft", "rate": 12.50},
        {"code": "SIP-ROOF-8.25", "qty": 560, "uom": "Sq Ft", "rate": 14.00},
        {"code": "C-CH-14GA", "qty": 320, "uom": "LF", "rate": 4.50},
        {"code": "OSB-7/16", "qty": 800, "uom": "Sq Ft", "rate": 0.85},
        {"code": "EPS-CORE", "qty": 45, "uom": "Cu Ft", "rate": 2.20},
    ]
    
    bom = connector.create_bom(module_name, materials)
    
    print(f"Exported {module_name} to ERPNext")
    print(f"Project: {project}")
    print(f"Item: {item}")
    print(f"BOM: {bom}")
    
    return {"project": project, "item": item, "bom": bom}
