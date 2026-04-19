"""
ComplianceEngine.py

Check project compliance against:
- HCD SHL 620 (Factory-built housing - State Housing Law)
- Title 24 CF1R (Energy compliance)
- CALGreen Tier 1
- ICC-ES ESR-5318 (SIP panels)
- Local zoning/setbacks

Usage:
    python3 ComplianceEngine.py --project-data /path/to/project.json
"""

import json, sys, os

class ComplianceEngine:
    def __init__(self, project_data):
        self.data = project_data
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def check(self, category, item, condition, required, severity="error"):
        status = "PASS" if condition else "FAIL"
        if not condition and severity == "warning":
            status = "WARN"
        
        check = {
            "category": category,
            "item": item,
            "required": required,
            "status": status,
            "severity": severity
        }
        self.checks.append(check)
        
        if status == "PASS": self.passed += 1
        elif status == "FAIL": self.failed += 1
        else: self.warnings += 1
        
        return condition
    
    def run_all_checks(self):
        lot = self.data.get("lot_information", {})
        dwelling = self.data.get("dwelling_specifications", {})
        sip = self.data.get("sip_specifications", {})
        compliance = self.data.get("compliance_references", {})
        
        # === HCD SHL 620 (Factory-Built Housing) ===
        self.check("HCD-SHL620", "HCD insignia requirement noted",
            "hcd" in compliance,
            "Factory-built units must display HCD insignia per HSC §19990")
        
        self.check("HCD-SHL620", "Title 25 CCR §3070 reference",
            "title_25" in compliance,
            "Must reference Title 25 CCR §3070 for factory-built standards")
        
        self.check("HCD-SHL620", "Transport dimensions declared",
            bool(dwelling.get("width_ft") and dwelling.get("depth_ft")),
            "Transport width/depth must be declared (max 16' wide per transport reg)")
        
        self.check("HCD-SHL620", "Module width ≤ 16 feet (transport limit)",
            dwelling.get("width_ft", 0) <= 16,
            f"Module width must be ≤ 16' for highway transport (found: {dwelling.get('width_ft', 'N/A')}')",
            severity="warning")
        
        self.check("HCD-SHL620", "Foundation/anchorage details referenced",
            bool(self.data.get("foundation_type") or "foundation" in str(compliance).lower()),
            "Must reference foundation/anchorage per HCD installation requirements",
            severity="warning")
        
        self.check("HCD-SHL620", "Installation manual referenced",
            bool(self.data.get("installation_manual")),
            "Must reference manufacturer installation manual",
            severity="warning")
        
        # === Title 24 CF1R (Energy) ===
        self.check("T24-CF1R", "Title 24 compliance noted",
            "title_24" in compliance,
            "Must note Title 24 energy compliance")
        
        self.check("T24-CF1R", "Wall insulation ≥ R-21 (wood frame)",
            sip.get("wall_r_value", 0) >= 21,
            f"Wall R-value must be ≥ R-21 (found: R-{sip.get('wall_r_value', 0)})")
        
        self.check("T24-CF1R", "Roof insulation ≥ R-30 (low-rise residential)",
            sip.get("roof_r_value", 0) >= 30,
            f"Roof R-value must be ≥ R-30 for Title 24 compliance (found: R-{sip.get('roof_r_value', 0)})")
        
        self.check("T24-CF1R", "CF1R-ENV (envelope) indicated",
            bool(self.data.get("cf1r_env") or "cf1r" in str(compliance).lower()),
            "CF1R-ENV energy calculation required for envelope",
            severity="warning")
        
        self.check("T24-CF1R", "CF1R-PRF (performance) indicated",
            bool(self.data.get("cf1r_prf")),
            "CF1R-PRF performance method calculation required",
            severity="warning")
        
        self.check("T24-CF1R", "Solar readiness noted",
            bool(self.data.get("solar_ready")),
            "Solar PV readiness required for new construction in CA",
            severity="warning")
        
        self.check("T24-CF1R", "HERS rater indicated",
            bool(self.data.get("hers_rater")),
            "HERS verification required for Title 24 compliance",
            severity="warning")
        
        # === CALGreen Tier 1 ===
        self.check("CALGreen", "CALGreen compliance noted",
            "calgreen" in compliance,
            "Must note CALGreen compliance")
        
        self.check("CALGreen", "Storm water pollution prevention plan (SWPPP)",
            bool(self.data.get("swppp") or "swppp" in str(compliance).lower()),
            "SWPPP required for construction sites > 1 acre",
            severity="warning")
        
        self.check("CALGreen", "Construction waste management plan",
            bool(self.data.get("waste_plan")),
            "Waste diversion plan required for CALGreen",
            severity="warning")
        
        # === SIP / Structural ===
        self.check("SIP", "ICC-ES ESR reference",
            sip.get("esr") == "ESR-5318",
            "Must reference ICC-ES ESR-5318 for PREFLEX SIPs")
        
        self.check("SIP", "SIP manufacturer declared",
            bool(sip.get("manufacturer")),
            "Must declare SIP manufacturer")
        
        self.check("SIP", "Wall panel spec declared",
            bool(sip.get("wall_panels")),
            "Must declare wall panel specification")
        
        self.check("SIP", "Roof panel spec declared",
            bool(sip.get("roof_panels")),
            "Must declare roof panel specification")
        
        # === Site / Civil ===
        self.check("Site", "Lot dimensions declared",
            lot.get("width_ft", 0) > 0 and lot.get("depth_ft", 0) > 0,
            "Must declare lot dimensions")
        
        self.check("Site", "Zoning declared",
            bool(lot.get("zoning")),
            "Must declare zoning designation")
        
        self.check("Site", "Address declared",
            bool(self.data.get("project_metadata", {}).get("address")),
            "Must declare property address")
        
        self.check("Site", "APN declared",
            bool(self.data.get("project_metadata", {}).get("apn")),
            "Must declare APN")
        
        self.check("Site", "Elevation data available",
            lot.get("elevation_ft") is not None,
            "Should have elevation data for drainage design",
            severity="warning")
        
        self.check("Site", "Slope data available",
            lot.get("slope_avg_percent") is not None,
            "Should have slope data for grading design",
            severity="warning")
        
        self.check("Site", "Front setback ≥ 20 ft",
            lot.get("front_setback_ft", 25) >= 20,
            "Front setback typically minimum 20' for residential",
            severity="warning")
        
        self.check("Site", "Side setbacks ≥ 3 ft",
            lot.get("side_setback_ft", 5) >= 3,
            "Side setbacks typically minimum 3-5'",
            severity="warning")
        
        self.check("Site", "Rear setback ≥ 15 ft",
            lot.get("rear_setback_ft", 20) >= 15,
            "Rear setback typically minimum 15-20'",
            severity="warning")
        
        return self.get_report()
    
    def get_report(self):
        return {
            "summary": {
                "total_checks": len(self.checks),
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "compliance_score": round(self.passed / len(self.checks) * 100, 1) if self.checks else 0
            },
            "checks": self.checks,
            "submit_ready": self.failed == 0
        }

def run_compliance_check(project_json_path):
    with open(project_json_path) as f:
        data = json.load(f)
    engine = ComplianceEngine(data)
    return engine.run_all_checks()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-data", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    
    report = run_compliance_check(args.project_data)
    
    print(f"\n{'='*50}")
    print(f"COMPLIANCE REPORT")
    print(f"{'='*50}")
    print(f"Score: {report['summary']['compliance_score']}%")
    print(f"Passed: {report['summary']['passed']} / {report['summary']['total_checks']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Submit Ready: {'YES' if report['submit_ready'] else 'NO'}")
    print(f"{'='*50}")
    
    for check in report["checks"]:
        icon = "✓" if check["status"] == "PASS" else ("⚠" if check["status"] == "WARN" else "✗")
        print(f"{icon} [{check['category']}] {check['item']}")
        if check["status"] != "PASS":
            print(f"    Required: {check['required']}")
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {args.output}")
