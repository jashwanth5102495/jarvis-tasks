
"""
report_generator.py
===================
Report generator for JARVIS master testing system.
Produces HTML, JSON, and Markdown reports.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from master_testing.milestone_validator import MilestoneValidationResult


class ReportGenerator:
    """Generates reports in multiple formats."""

    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_report(
        self,
        test_results: Dict[int, MilestoneValidationResult],
        filename: Optional[str] = None
    ) -> Path:
        """Generate a JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"jarvis_test_report_{timestamp}.json"
        report_path = self.reports_dir / filename
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "milestones": {}
        }
        
        for milestone, result in test_results.items():
            report_data["milestones"][milestone] = {
                "name": MilestoneValidator.MILESTONE_NAMES.get(milestone, f"Milestone {milestone}"),
                "passed": result.passed,
                "execution_time": result.execution_time,
                "test_output": result.test_output
            }
        
        # Add summary
        total_passed = sum(1 for r in test_results.values() if r.passed)
        total_tested = len(test_results)
        report_data["summary"] = {
            "total_tested": total_tested,
            "total_passed": total_passed,
            "total_failed": total_tested - total_passed,
            "pass_rate": f"{(total_passed / total_tested * 100):.1f}%" if total_tested > 0 else "0%"
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON report saved to: {report_path}")
        return report_path

    def generate_markdown_report(
        self,
        test_results: Dict[int, MilestoneValidationResult],
        filename: Optional[str] = None
    ) -> Path:
        """Generate a Markdown report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"jarvis_test_report_{timestamp}.md"
        report_path = self.reports_dir / filename
        
        total_passed = sum(1 for r in test_results.values() if r.passed)
        total_tested = len(test_results)
        
        md_content = "# JARVIS AI Operating System Test Report\n\n"
        md_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        md_content += "## Summary\n\n"
        md_content += f"- Total tested: {total_tested}\n"
        md_content += f"- Passed: {total_passed} [OK]\n"
        md_content += f"- Failed: {total_tested - total_passed} [FAIL]\n"
        md_content += f"- Pass rate: {(total_passed/total_tested*100):.1f}% \n\n"
        
        md_content += "## Milestone Results\n\n"
        
        for milestone, result in sorted(test_results.items()):
            name = MilestoneValidator.MILESTONE_NAMES.get(milestone, f"Milestone {milestone}")
            status_text = "[OK] Passed" if result.passed else "[FAIL] Failed"
            md_content += f"### Milestone {milestone}: {name}\n"
            md_content += f"- Status: {status_text}\n"
            md_content += f"- Execution time: {result.execution_time:.2f} seconds\n"
            md_content += "\n---\n"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[OK] Markdown report saved to: {report_path}")
        return report_path

    def generate_html_report(
        self,
        test_results: Dict[int, MilestoneValidationResult],
        filename: Optional[str] = None
    ) -> Path:
        """Generate a basic HTML report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"jarvis_test_report_{timestamp}.html"
        report_path = self.reports_dir / filename
        
        total_passed = sum(1 for r in test_results.values() if r.passed)
        total_tested = len(test_results)
        total_failed = total_tested - total_passed
        
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f5f7fa; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }}
        .summary {{ display: flex; gap: 2rem; margin: 2rem 0; }}
        .summary-card {{ flex:1; background: #f8f9fa; padding:1.5rem; border-radius:8px; text-align:center; }}
        .pass {{ background: #d4edda; color: #155724; }}
        .fail {{ background: #f8d7da; color: #721c24; }}
        .milestone {{ margin: 1.5rem 0; padding: 1.5rem; border:1px solid #eee; border-radius: 8px; }}
        .milestone.passed {{ border-left:5px solid #28a745; }}
        .milestone.failed {{ border-left:5px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>JARVIS AI Operating System - Test Report</h1>
        <p>Generated: {timestamp}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tested</h3>
                <p style="font-size: 2rem;">{total_tested}</p>
            </div>
            <div class="summary-card pass">
                <h3>Passed</h3>
                <p style="font-size: 2rem;">{total_passed}</p>
            </div>
            <div class="summary-card fail">
                <h3>Failed</h3>
                <p style="font-size: 2rem;">{total_failed}</p>
            </div>
        </div>
        
        <h2>Milestone Results</h2>
""".format(
    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    total_tested=total_tested,
    total_passed=total_passed,
    total_failed=total_failed
)
        
        for milestone, result in sorted(test_results.items()):
            name = MilestoneValidator.MILESTONE_NAMES.get(milestone, f"Milestone {milestone}")
            status_class = "passed" if result.passed else "failed"
            status_text = "PASSED" if result.passed else "FAILED"
            html_content += f"""
            <div class="milestone {status_class}">
                <h3>Milestone {milestone}: {name}</h3>
                <p>Status: <strong>{status_text}</strong></p>
                <p>Execution Time: {result.execution_time:.2f} seconds</p>
            </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[OK] HTML report saved to: {report_path}")
        return report_path


# Import MilestoneValidator here to avoid circular dependency issues later
from master_testing.milestone_validator import MilestoneValidator

# Singleton instance
reports_dir = Path(__file__).parent.parent / "reports"
report_generator = ReportGenerator(reports_dir=reports_dir)
