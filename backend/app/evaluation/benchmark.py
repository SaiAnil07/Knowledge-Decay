from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.scanner.repo_scanner import RepositoryScanner
from backend.app.parsers.java_parser import JavaSourceAnalyzer
from backend.app.parsers.maven_parser import MavenPomAnalyzer
from backend.app.parsers.markdown_parser import MarkdownDocAnalyzer
from backend.app.knowledge.representation import KnowledgeRecord, Finding, Classification
from backend.app.engine.consistency_engine import ConsistencyEngine

class GroundTruthCase(BaseModel):
    id: str
    description: str
    expected_classification: Classification
    concept_keyword: str

# Labeled ground truth for sample_java_project
SAMPLE_GROUND_TRUTH: List[GroundTruthCase] = [
    GroundTruthCase(
        id="TC-1",
        description="GET /api/v1/users is consistent between code and doc",
        expected_classification=Classification.CONSISTENT,
        concept_keyword="/api/v1/users"
    ),
    GroundTruthCase(
        id="TC-2",
        description="GET /api/v1/orders in doc vs POST /api/v1/orders in code is contradictory",
        expected_classification=Classification.CONTRADICTORY,
        concept_keyword="/api/v1/orders"
    ),
    GroundTruthCase(
        id="TC-3",
        description="Java 11 in doc vs Java 17 in pom.xml is contradictory",
        expected_classification=Classification.CONTRADICTORY,
        concept_keyword="java_version"
    ),
    GroundTruthCase(
        id="TC-4",
        description="DELETE /api/v1/legacy/accounts in doc is potentially outdated / removed",
        expected_classification=Classification.POTENTIALLY_OUTDATED,
        concept_keyword="/api/v1/legacy/accounts"
    ),
    GroundTruthCase(
        id="TC-5",
        description="POST /api/v1/payments/process in code is missing from docs",
        expected_classification=Classification.MISSING,
        concept_keyword="/api/v1/payments/process"
    ),
    GroundTruthCase(
        id="TC-6",
        description="User sorting behavioral claim divergence is uncertain / potentially outdated",
        expected_classification=Classification.POTENTIALLY_OUTDATED,
        concept_keyword="sorted by"
    )
]

class EvaluationMetrics(BaseModel):
    mode: str  # "rule_based_only" or "hybrid_semantic"
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    total_evaluated_cases: int = 0
    case_breakdown: List[Dict[str, Any]] = Field(default_factory=list)

class BenchmarkEvaluator:
    """
    Evaluates detector performance against labeled benchmark cases.
    Computes precision, recall, and F1-score for rule-based vs hybrid semantic modes.
    """

    def __init__(self, ground_truth: Optional[List[GroundTruthCase]] = None):
        self.ground_truth = ground_truth or SAMPLE_GROUND_TRUTH

    def evaluate(self, repo_path: str, enable_semantic: bool = True) -> EvaluationMetrics:
        scanner = RepositoryScanner()
        scan_res = scanner.scan(repo_path)
        if not scan_res.is_valid:
            raise ValueError(f"Invalid repository path for evaluation: {scan_res.error_message}")

        java_parser = JavaSourceAnalyzer()
        maven_parser = MavenPomAnalyzer()
        doc_parser = MarkdownDocAnalyzer()

        records: List[KnowledgeRecord] = []
        for file in scan_res.files:
            if file.file_type == "JAVA":
                records.extend(java_parser.parse_file(file.absolute_path, file.relative_path))
            elif file.file_type == "MAVEN_POM":
                records.extend(maven_parser.parse_file(file.absolute_path, file.relative_path))
            elif file.file_type in ("MARKDOWN", "README"):
                records.extend(doc_parser.parse_file(file.absolute_path, file.relative_path))

        engine = ConsistencyEngine(enable_semantic=enable_semantic)
        findings = engine.analyze(records)

        return self.compute_metrics(findings, mode="hybrid_semantic" if enable_semantic else "rule_based_only")

    def compute_metrics(self, findings: List[Finding], mode: str) -> EvaluationMetrics:
        tp = 0
        fp = 0
        fn = 0
        tn = 0
        case_details = []

        for case in self.ground_truth:
            matched_finding = None
            for f in findings:
                # Check if concept or title matches
                f_text = f"{f.title} {f.doc_claim or ''} {f.code_evidence or ''} {f.explanation}".lower()
                if case.concept_keyword.lower() in f_text:
                    matched_finding = f
                    break

            if matched_finding:
                is_correct = (
                    matched_finding.classification == case.expected_classification
                    or (case.expected_classification in (Classification.POTENTIALLY_OUTDATED, Classification.UNCERTAIN)
                        and matched_finding.classification in (Classification.POTENTIALLY_OUTDATED, Classification.UNCERTAIN))
                )

                if is_correct:
                    if case.expected_classification == Classification.CONSISTENT:
                        tn += 1
                        status = "TRUE_NEGATIVE"
                    else:
                        tp += 1
                        status = "TRUE_POSITIVE"
                else:
                    fp += 1
                    status = "FALSE_POSITIVE"

                case_details.append({
                    "case_id": case.id,
                    "description": case.description,
                    "expected": case.expected_classification.value,
                    "actual": matched_finding.classification.value,
                    "status": status,
                    "finding_id": matched_finding.id,
                    "title": matched_finding.title
                })
            else:
                # Inconsistency missed
                if case.expected_classification != Classification.CONSISTENT:
                    fn += 1
                    status = "FALSE_NEGATIVE"
                else:
                    tn += 1
                    status = "TRUE_NEGATIVE"

                case_details.append({
                    "case_id": case.id,
                    "description": case.description,
                    "expected": case.expected_classification.value,
                    "actual": "NONE",
                    "status": status,
                    "finding_id": None,
                    "title": "No finding generated"
                })

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        total_eval = tp + fp + fn + tn
        accuracy = (tp + tn) / total_eval if total_eval > 0 else 0.0

        return EvaluationMetrics(
            mode=mode,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            accuracy=round(accuracy, 4),
            total_evaluated_cases=len(self.ground_truth),
            case_breakdown=case_details
        )
