"""
MattermostBot.py - Plan notification bot for Genii Studio

Posts to Mattermost when plans are generated, compliance checks complete,
or tasks need attention.

Usage:
    python3 MattermostBot.py --message "Site plan generated" --channel "engineering"
    
Env vars:
    MATTERMOST_URL=https://mm.geniinow.com
    MATTERMOST_TOKEN=your_token
    MATTERMOST_CHANNEL=engineering
"""

import json, os, urllib.request, urllib.parse

class GeniiMattermostBot:
    def __init__(self, url=None, token=None, default_channel=None):
        self.url = (url or os.getenv("MATTERMOST_URL", "https://mm.geniinow.com")).rstrip('/')
        self.token = token or os.getenv("MATTERMOST_TOKEN")
        self.default_channel = default_channel or os.getenv("MATTERMOST_CHANNEL", "engineering")
        self.headers = {'Content-Type': 'application/json'}
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'
    
    def health_check(self):
        try:
            req = urllib.request.Request(f"{self.url}/api/v4/system/ping", headers=self.headers)
            with urllib.request.urlopen(req) as resp:
                return {"ok": True, "status": json.loads(resp.read().decode())}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def post_message(self, message, channel=None, props=None):
        channel = channel or self.default_channel
        data = {
            "channel_id": channel if channel.startswith('#') else self._get_channel_id(channel),
            "message": message,
            "props": props or {}
        }
        return self._post("/api/v4/posts", data)
    
    def post_plan_generated(self, project_data, files, compliance_score):
        """Formatted notification when a plan set is generated."""
        meta = project_data.get("project_metadata", {})
        address = meta.get("address", "Unknown")
        apn = meta.get("apn", "N/A")
        
        message = f""":house: **New Plan Set Generated**

**Address:** {address}
**APN:** {apn}
**Compliance Score:** {compliance_score:.1f}%

**Files:**
"""
        for f in files:
            message += f"- `{f}`\n"
        
        message += "\n**Next Steps:**"
        message += "\n- [ ] Civil engineer review"
        message += "\n- [ ] Structural engineer review"
        message += "\n- [ ] Title 24 energy compliance"
        message += "\n- [ ] HCD plan check"
        message += "\n- [ ] Permit submission"
        
        return self.post_message(message, props={
            "attachments": [{
                "color": "#00AA00" if compliance_score >= 80 else "#FFAA00",
                "title": f"Plan Set: {address}",
                "title_link": meta.get("github_repo", ""),
                "fields": [
                    {"title": "APN", "value": apn, "short": True},
                    {"title": "Compliance", "value": f"{compliance_score:.1f}%", "short": True}
                ]
            }]
        })
    
    def post_compliance_alert(self, project_data, warnings, failures):
        """Alert when compliance issues are found."""
        meta = project_data.get("project_metadata", {})
        address = meta.get("address", "Unknown")
        
        message = f""":warning: **Compliance Alert: {address}**

"""
        if failures:
            message += "**FAILURES:**\n"
            for f in failures:
                message += f"- ❌ {f['check']}: {f['message']}\n"
        
        if warnings:
            message += "\n**WARNINGS:**\n"
            for w in warnings:
                message += f"- ⚠️ {w['check']}: {w['message']} (got {w['actual']}, need {w['required']})\n"
        
        return self.post_message(message, channel="compliance")
    
    def _get_channel_id(self, channel_name):
        """Lookup channel ID by name."""
        try:
            req = urllib.request.Request(
                f"{self.url}/api/v4/teams/name/homegenii/channels/name/{channel_name}",
                headers=self.headers
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                return data.get("id", channel_name)
        except:
            return channel_name
    
    def _post(self, endpoint, data):
        url = f"{self.url}{endpoint}"
        req = urllib.request.Request(
            url, data=json.dumps(data).encode(), headers=self.headers, method='POST'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

def notify_plan_complete(project_json_path, files_dir=None):
    """Full notification after pipeline completion."""
    bot = GeniiMattermostBot()
    
    health = bot.health_check()
    if not health["ok"]:
        print(f"Mattermost unavailable: {health.get('error')}")
        return {"status": "skipped", "reason": health.get("error")}
    
    with open(project_json_path) as f:
        data = json.load(f)
    
    # Load compliance results if available
    compliance_score = 0.0
    warnings = []
    failures = []
    
    compliance_file = project_json_path.replace("_data.json", "_compliance.json")
    if os.path.exists(compliance_file):
        with open(compliance_file) as f:
            comp = json.load(f)
            compliance_score = comp.get("score", 0.0)
            warnings = comp.get("warnings", [])
            failures = comp.get("failures", [])
    
    # List generated files
    files = []
    if files_dir:
        import glob
        for ext in ["*.FCStd", "*.stp", "*.dxf", "*_data.json"]:
            files.extend(glob.glob(os.path.join(files_dir, ext)))
        files = [os.path.basename(f) for f in files]
    
    # Post main notification
    result = bot.post_plan_generated(data, files, compliance_score)
    
    # Post compliance alert if needed
    if warnings or failures:
        bot.post_compliance_alert(data, warnings, failures)
    
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-data", required=True)
    parser.add_argument("--files-dir")
    parser.add_argument("--message")
    parser.add_argument("--channel")
    args = parser.parse_args()
    
    if args.message:
        bot = GeniiMattermostBot()
        result = bot.post_message(args.message, args.channel)
        print(result)
    else:
        result = notify_plan_complete(args.project_data, args.files_dir)
        print(f"Notification: {result}")
