import json
import csv
import io
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.knowledge.representation import Finding, Classification

class ReportGenerator:
    """
    Generates downloadable reports in JSON, CSV, and HTML formats.
    """

    @staticmethod
    def generate_json_report(analysis_data: Dict[str, Any]) -> str:
        """Generates formatted JSON string."""
        return json.dumps(analysis_data, indent=2, default=str)

    @staticmethod
    def generate_csv_report(findings: List[Dict[str, Any]]) -> str:
        """Generates CSV string summarizing findings."""
        output = io.StringIO()
        fieldnames = [
            "id", "classification", "certainty", "title",
            "doc_file", "doc_line", "doc_claim",
            "code_file", "code_line", "code_evidence",
            "detection_method", "suggested_action"
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for f in findings:
            writer.writerow(f)

        return output.getvalue()

    @staticmethod
    def generate_html_report(analysis_data: Dict[str, Any]) -> str:
        """Generates standalone styled HTML report."""
        repo_path = analysis_data.get("repo_path", "Unknown Repository")
        timestamp = analysis_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        summary = analysis_data.get("summary", {})
        findings = analysis_data.get("findings", [])

        # Color codes
        badge_colors = {
            "CONSISTENT": "#10B981",
            "CONTRADICTORY": "#EF4444",
            "POTENTIALLY_OUTDATED": "#F59E0B",
            "MISSING": "#6366F1",
            "UNCERTAIN": "#8B5CF6"
        }

        finding_cards_html = ""
        for f in findings:
            classification = f.get("classification", "UNCERTAIN")
            color = badge_colors.get(classification, "#6B7280")
            doc_file = f.get("doc_file") or "N/A"
            doc_line = f.get("doc_line") or "N/A"
            code_file = f.get("code_file") or "N/A"
            code_line = f.get("code_line") or "N/A"
            doc_snippet = (f.get("doc_snippet") or f.get("doc_claim") or "").replace("<", "&lt;").replace(">", "&gt;")
            code_snippet = (f.get("code_snippet") or f.get("code_evidence") or "").replace("<", "&lt;").replace(">", "&gt;")
            action = f.get("suggested_action", "")

            finding_cards_html += f"""
            <div class="card" style="border-left: 5px solid {color}; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #1E293B;">{f.get('title', 'Finding')}</h3>
                    <span class="badge" style="background-color: {color}; color: white;">{classification}</span>
                </div>
                <p style="color: #475569; margin: 10px 0;">{f.get('explanation', '')}</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0;">
                    <div style="background: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
                        <div style="font-weight: 600; font-size: 13px; color: #64748B;">DOCUMENTATION CLAIM</div>
                        <div style="font-size: 13px; color: #334155; margin-top: 4px;">{doc_file} (line {doc_line})</div>
                        {f'<pre style="background: #FFFFFF; padding: 8px; font-size: 12px; border-radius: 4px; overflow-x: auto; margin-top: 8px;">{doc_snippet}</pre>' if doc_snippet else ''}
                    </div>
                    <div style="background: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
                        <div style="font-weight: 600; font-size: 13px; color: #64748B;">CODE IMPLEMENTATION EVIDENCE</div>
                        <div style="font-size: 13px; color: #334155; margin-top: 4px;">{code_file} (line {code_line})</div>
                        {f'<pre style="background: #FFFFFF; padding: 8px; font-size: 12px; border-radius: 4px; overflow-x: auto; margin-top: 8px;">{code_snippet}</pre>' if code_snippet else ''}
                    </div>
                </div>

                <div style="background: #EFF6FF; border-left: 3px solid #3B82F6; padding: 10px 14px; font-size: 13px; color: #1E40AF; border-radius: 0 4px 4px 0;">
                    <strong>Recommended Action:</strong> {action}
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Decay Report - {repo_path}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #F1F5F9;
            color: #0F172A;
            line-height: 1.5;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #FFFFFF;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #F8FAFC;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            text-align: center;
        }}
        .stat-value {{
            font-size: 26px;
            font-weight: 700;
            color: #0F172A;
        }}
        .stat-label {{
            font-size: 13px;
            color: #64748B;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .card {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0 0 10px 0;">Knowledge Decay Consistency Report</h1>
            <div style="color: #64748B; font-size: 14px;">
                Repository: <strong>{repo_path}</strong> | Generated: {timestamp}
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{summary.get('total_files', 0)}</div>
                <div class="stat-label">Files Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #10B981;">{summary.get('consistent', 0)}</div>
                <div class="stat-label">Consistent</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #EF4444;">{summary.get('contradictory', 0)}</div>
                <div class="stat-label">Contradictions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #F59E0B;">{summary.get('potentially_outdated', 0)}</div>
                <div class="stat-label">Outdated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #6366F1;">{summary.get('missing', 0)}</div>
                <div class="stat-label">Missing Docs</div>
            </div>
        </div>

        <h2>Detailed Inconsistency Findings ({len(findings)})</h2>
        {finding_cards_html if findings else '<p style="color: #64748B;">No issues found. Documentation is synchronized.</p>'}
    </div>
</body>
</html>
"""
        return html
