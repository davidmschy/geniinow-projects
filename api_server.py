"""
api_server.py - Simple HTTP API for Genii Studio pipeline

Run: python3 api_server.py

Endpoints:
  POST /generate
    {"address": "549 N Parkview, Fresno, CA", "apn": "449-341-009"}
    → {"status": "complete", "github_url": "...", "compliance_score": 69.0}

  GET /health
    → {"status": "ok", "freecad": true, "gis": true}
"""

import json, os, sys, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.expanduser("~/geniinow-projects/macros"))

PORT = 8765

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_json({
                "status": "ok",
                "freecad": os.path.exists("/Applications/FreeCAD.app"),
                "pipeline_scripts": len([f for f in os.listdir(os.path.expanduser("~/geniinow-projects/macros")) if f.endswith('.py')])
            })
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        if self.path == "/generate":
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
            params = json.loads(body)
            
            address = params.get("address")
            apn = params.get("apn")
            
            if not address or not apn:
                self.send_json({"error": "address and apn required"}, 400)
                return
            
            # Run pipeline
            result = self.run_pipeline(address, apn)
            self.send_json(result)
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def run_pipeline(self, address, apn):
        try:
            cmd = [
                sys.executable,
                os.path.expanduser("~/geniinow-projects/macros/FullPipeline.py"),
                "--address", address,
                "--apn", apn
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse output for key info
            output = result.stdout
            
            # Extract compliance score
            score_match = __import__('re').search(r'Compliance:\s*(\d+\.?\d*)%', output)
            score = float(score_match.group(1)) if score_match else 0
            
            # Extract GitHub URL
            url_match = __import__('re').search(r'(https://github\.com/[^\s]+)', output)
            github_url = url_match.group(1) if url_match else None
            
            return {
                "status": "complete" if result.returncode == 0 else "error",
                "compliance_score": score,
                "github_url": github_url,
                "output": output[-500:] if len(output) > 500 else output
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    print(f"Genii Studio API starting on http://localhost:{PORT}")
    print(f"Health check: curl http://localhost:{PORT}/health")
    print(f"Generate plan: curl -X POST http://localhost:{PORT}/generate \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{{\"address\":\"549 N Parkview, Fresno, CA\",\"apn\":\"449-341-009\"}}'")
    HTTPServer(("", PORT), Handler).serve_forever()
