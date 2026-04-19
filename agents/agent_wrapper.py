"""
agent_wrapper.py - Generic AI agent runtime for Genii Studio team

Each agent runs as a persistent daemon managed by PM2.
Role-specific behavior loaded from environment variable AGENT_ROLE.

Roles: ceo, business_manager, draftsman, labor_coord, land_broker, 
       realtor, accountant, qc_manager, software_engineer, pipeline
"""

import os, sys, json, time, subprocess
from pathlib import Path

class GeniiAgent:
    def __init__(self):
        self.role = os.getenv("AGENT_ROLE", "pipeline")
        self.name = os.getenv("AGENT_NAME", f"agent-{self.role}")
        self.load_config()
    
    def load_config(self):
        """Load role-specific configuration."""
        configs = {
            "ceo": {
                "tools": ["erpnext", "gws", "github", "mattermost"],
                "erpnext_access": "full_admin",
                "gws_access": "full_admin",
                "github_scope": "org",
                "can_approve": True
            },
            "business_manager": {
                "tools": ["erpnext", "gws", "mattermost"],
                "erpnext_access": "full",
                "gws_access": "full",
                "github_scope": "read",
                "can_approve": True
            },
            "draftsman": {
                "tools": ["cad", "github", "erpnext"],
                "erpnext_access": "projects",
                "gws_access": "drive_sheets",
                "github_scope": "repo",
                "can_approve": False
            },
            "labor_coord": {
                "tools": ["erpnext", "mattermost", "gws_calendar"],
                "erpnext_access": "projects",
                "gws_access": "calendar_drive",
                "github_scope": None,
                "can_approve": False
            },
            "land_broker": {
                "tools": ["gws", "erpnext", "maps"],
                "erpnext_access": "land_acq",
                "gws_access": "gmail_calendar",
                "github_scope": None,
                "can_approve": False
            },
            "realtor": {
                "tools": ["gws", "erpnext", "crm"],
                "erpnext_access": "sales",
                "gws_access": "gmail_calendar",
                "github_scope": None,
                "can_approve": False
            },
            "accountant": {
                "tools": ["erpnext", "gws_sheets"],
                "erpnext_access": "financial",
                "gws_access": "sheets_drive",
                "github_scope": None,
                "can_approve": True
            },
            "qc_manager": {
                "tools": ["erpnext", "cad", "github"],
                "erpnext_access": "qc_compliance",
                "gws_access": "drive",
                "github_scope": "repo",
                "can_approve": False
            },
            "software_engineer": {
                "tools": ["github", "erpnext", "api"],
                "erpnext_access": "system_admin",
                "gws_access": "drive",
                "github_scope": "org",
                "can_approve": True
            },
            "pipeline": {
                "tools": ["cad", "github", "erpnext", "mattermost"],
                "erpnext_access": "all_projects",
                "gws_access": "service_account",
                "github_scope": "repo",
                "can_approve": False
            }
        }
        
        self.config = configs.get(self.role, configs["pipeline"])
        print(f"[{self.name}] Loaded config for role: {self.role}")
        print(f"  Tools: {', '.join(self.config['tools'])}")
        print(f"  ERPNext: {self.config['erpnext_access']}")
        print(f"  GWS: {self.config['gws_access']}")
    
    def run(self):
        """Main agent loop."""
        print(f"[{self.name}] Agent started. Role: {self.role}")
        print(f"[{self.name}] Waiting for tasks...")
        
        # In production, this would connect to a message queue or API
        # For now, run a simple heartbeat loop
        while True:
            self.heartbeat()
            time.sleep(30)
    
    def heartbeat(self):
        """Log heartbeat."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {self.name} - {self.role} - OK")

if __name__ == "__main__":
    agent = GeniiAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        print(f"\n[{agent.name}] Shutting down...")
