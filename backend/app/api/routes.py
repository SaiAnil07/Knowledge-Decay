import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.scanner.repo_scanner import RepositoryScanner, ScanResult
from backend.app.parsers.java_parser import JavaSourceAnalyzer
from backend.app.parsers.maven_parser import MavenPomAnalyzer
from backend.app.parsers.markdown_parser import MarkdownDocAnalyzer
from backend.app.knowledge.representation import KnowledgeRecord, Finding, Classification, CertaintyLevel
from backend.app.engine.consistency_engine import ConsistencyEngine
from backend.app.reporting.report_generator import ReportGenerator
from backend.app.evaluation.benchmark import BenchmarkEvaluator
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import AnalysisRun, FindingModel, DiscoveredFileModel

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class ScanRequest(BaseModel):
    repo_path: str = Field(description="Local repository directory path")

class AnalyzeRequest(BaseModel):
    repo_path: str = Field(description="Local repository directory path")
    enable_semantic: bool = Field(default=True, description="Enable local semantic NLP similarity")

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Knowledge Decay Detection System",
        "mode": "privacy_preserving_local",
        "external_llm_required": False,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/sample-project")
async def get_sample_project():
    """Returns absolute path to the bundled sample Java project for 1-click testing."""
    sample_path = Path(__file__).resolve().parent.parent.parent.parent / "sample_java_project"
    exists = sample_path.exists()
    return {
        "sample_path": str(sample_path).replace("\\", "/"),
        "exists": exists,
        "description": "Bundled Java Spring Boot project with intentional documentation decay benchmark cases"
    }

@router.post("/scan")
async def scan_repository(req: ScanRequest):
    """
    Validates repository path and discovers supported source and documentation files.
    """
    scanner = RepositoryScanner()
    result = scanner.scan(req.repo_path)
    if not result.is_valid:
        raise HTTPException(status_code=400, detail=result.error_message)
    return result

@router.post("/analyze")
async def run_analysis(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """
    Runs full static consistency analysis on repository and persists findings to SQLite.
    """
    scanner = RepositoryScanner()
    scan_res = scanner.scan(req.repo_path)
    if not scan_res.is_valid:
        raise HTTPException(status_code=400, detail=scan_res.error_message)

    java_parser = JavaSourceAnalyzer()
    maven_parser = MavenPomAnalyzer()
    doc_parser = MarkdownDocAnalyzer()

    records: List[KnowledgeRecord] = []
    for f in scan_res.files:
        if f.file_type == "JAVA":
            records.extend(java_parser.parse_file(f.absolute_path, f.relative_path))
        elif f.file_type == "MAVEN_POM":
            records.extend(maven_parser.parse_file(f.absolute_path, f.relative_path))
        elif f.file_type in ("MARKDOWN", "README"):
            records.extend(doc_parser.parse_file(f.absolute_path, f.relative_path))

    # Run consistency engine
    engine = ConsistencyEngine(enable_semantic=req.enable_semantic)
    findings = engine.analyze(records)

    # Compute breakdown counts
    counts = {
        Classification.CONSISTENT: 0,
        Classification.CONTRADICTORY: 0,
        Classification.POTENTIALLY_OUTDATED: 0,
        Classification.MISSING: 0,
        Classification.UNCERTAIN: 0
    }
    for item in findings:
        counts[item.classification] = counts.get(item.classification, 0) + 1

    # Persist run to SQLite
    run_id = str(uuid.uuid4())
    run_model = AnalysisRun(
        id=run_id,
        repo_path=scan_res.repo_path,
        timestamp=datetime.now(timezone.utc),
        status="COMPLETED",
        total_files=scan_res.total_files_discovered,
        total_lines=scan_res.total_lines,
        scan_duration_ms=scan_res.scan_duration_ms,
        counts_consistent=counts[Classification.CONSISTENT],
        counts_contradictory=counts[Classification.CONTRADICTORY],
        counts_outdated=counts[Classification.POTENTIALLY_OUTDATED],
        counts_missing=counts[Classification.MISSING],
        counts_uncertain=counts[Classification.UNCERTAIN]
    )
    db.add(run_model)

    # Persist findings
    for idx, f in enumerate(findings):
        db_finding_id = f"{run_id[:8]}_{idx}_{f.id}"
        finding_model = FindingModel(
            id=db_finding_id,
            analysis_id=run_id,
            classification=f.classification.value,
            certainty=f.certainty.value,
            title=f.title,
            explanation=f.explanation,
            doc_file=f.doc_file,
            doc_line=f.doc_line,
            doc_claim=f.doc_claim,
            doc_snippet=f.doc_snippet,
            code_file=f.code_file,
            code_line=f.code_line,
            code_evidence=f.code_evidence,
            code_snippet=f.code_snippet,
            detection_method=f.detection_method,
            suggested_action=f.suggested_action,
            meta_json=json.dumps(f.metadata)
        )
        db.add(finding_model)

    # Persist discovered files
    for file in scan_res.files:
        file_model = DiscoveredFileModel(
            analysis_id=run_id,
            relative_path=file.relative_path,
            absolute_path=file.absolute_path,
            file_type=file.file_type,
            size_bytes=file.size_bytes,
            line_count=file.line_count
        )
        db.add(file_model)

    await db.commit()

    return {
        "analysis_id": run_id,
        "repo_path": scan_res.repo_path,
        "timestamp": run_model.timestamp.isoformat(),
        "summary": {
            "total_files": scan_res.total_files_discovered,
            "total_lines": scan_res.total_lines,
            "scan_duration_ms": scan_res.scan_duration_ms,
            "consistent": counts[Classification.CONSISTENT],
            "contradictory": counts[Classification.CONTRADICTORY],
            "potentially_outdated": counts[Classification.POTENTIALLY_OUTDATED],
            "missing": counts[Classification.MISSING],
            "uncertain": counts[Classification.UNCERTAIN]
        },
        "findings": [f.model_dump() for f in findings],
        "files": [f.model_dump() for f in scan_res.files]
    }

@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    """Retrieves list of past analysis runs."""
    stmt = select(AnalysisRun).order_by(desc(AnalysisRun.timestamp)).limit(20)
    result = await db.execute(stmt)
    runs = result.scalars().all()

    return [
        {
            "id": r.id,
            "repo_path": r.repo_path,
            "timestamp": r.timestamp.isoformat(),
            "total_files": r.total_files,
            "consistent": r.counts_consistent,
            "contradictory": r.counts_contradictory,
            "outdated": r.counts_outdated,
            "missing": r.counts_missing,
            "uncertain": r.counts_uncertain
        }
        for r in runs
    ]

@router.get("/reports/{analysis_id}")
async def get_report(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full analysis report by ID."""
    stmt = select(AnalysisRun).where(AnalysisRun.id == analysis_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    # Fetch findings
    f_stmt = select(FindingModel).where(FindingModel.analysis_id == analysis_id)
    f_res = await db.execute(f_stmt)
    findings = f_res.scalars().all()

    # Fetch files
    files_stmt = select(DiscoveredFileModel).where(DiscoveredFileModel.analysis_id == analysis_id)
    files_res = await db.execute(files_stmt)
    files = files_res.scalars().all()

    return {
        "analysis_id": run.id,
        "repo_path": run.repo_path,
        "timestamp": run.timestamp.isoformat(),
        "summary": {
            "total_files": run.total_files,
            "total_lines": run.total_lines,
            "scan_duration_ms": run.scan_duration_ms,
            "consistent": run.counts_consistent,
            "contradictory": run.counts_contradictory,
            "potentially_outdated": run.counts_outdated,
            "missing": run.counts_missing,
            "uncertain": run.counts_uncertain
        },
        "findings": [
            {
                "id": f.id,
                "classification": f.classification,
                "certainty": f.certainty,
                "title": f.title,
                "explanation": f.explanation,
                "doc_file": f.doc_file,
                "doc_line": f.doc_line,
                "doc_claim": f.doc_claim,
                "doc_snippet": f.doc_snippet,
                "code_file": f.code_file,
                "code_line": f.code_line,
                "code_evidence": f.code_evidence,
                "code_snippet": f.code_snippet,
                "detection_method": f.detection_method,
                "suggested_action": f.suggested_action,
                "metadata": json.loads(f.meta_json or "{}")
            }
            for f in findings
        ],
        "files": [
            {
                "relative_path": file.relative_path,
                "file_type": file.file_type,
                "size_bytes": file.size_bytes,
                "line_count": file.line_count
            }
            for file in files
        ]
    }

@router.get("/reports/{analysis_id}/export")
async def export_report(
    analysis_id: str,
    format: str = Query(default="json", pattern="^(json|csv|html)$"),
    db: AsyncSession = Depends(get_db)
):
    """Exports analysis report in JSON, CSV, or HTML format."""
    report_data = await get_report(analysis_id, db)

    if format == "json":
        content = ReportGenerator.generate_json_report(report_data)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{analysis_id[:8]}.json"}
        )
    elif format == "csv":
        content = ReportGenerator.generate_csv_report(report_data["findings"])
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{analysis_id[:8]}.csv"}
        )
    elif format == "html":
        content = ReportGenerator.generate_html_report(report_data)
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=report_{analysis_id[:8]}.html"}
        )

@router.post("/evaluate")
async def run_evaluation(enable_semantic: bool = Query(default=True)):
    """Runs evaluation on sample Java benchmark repository and calculates Precision, Recall, and F1."""
    sample_path = Path(__file__).resolve().parent.parent.parent.parent / "sample_java_project"
    evaluator = BenchmarkEvaluator()
    metrics = evaluator.evaluate(str(sample_path), enable_semantic=enable_semantic)
    return metrics
