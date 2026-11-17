import re
import hashlib
from typing import List, Dict, Any, Tuple, Optional, Set

from backend.app.knowledge.representation import (
    KnowledgeRecord,
    ArtifactType,
    Classification,
    CertaintyLevel,
    Finding
)
from backend.app.engine.semantic_analyzer import LocalSemanticAnalyzer

def canonicalize_route(route: str) -> str:
    """
    Replaces route parameters with a canonical wildcard token:
    e.g. '/api/v1/users/{id}' -> '/api/v1/users/{*}'
    e.g. '/api/v1/users/:userId' -> '/api/v1/users/{*}'
    """
    clean = route.strip()
    # Replace {param_name} or :param_name with {*}
    clean = re.sub(r'\{[a-zA-Z0-9_\-]+\}', '{*}', clean)
    clean = re.sub(r':([a-zA-Z0-9_\-]+)', '{*}', clean)
    # Strip trailing slashes
    if len(clean) > 1 and clean.endswith("/"):
        clean = clean[:-1]
    return clean

class ConsistencyEngine:
    """
    Consistency Analysis Engine for detecting knowledge decay.
    Combines deterministic rules (concrete syntax/version properties) with
    local NLP semantic similarity analysis.
    """

    def __init__(self, enable_semantic: bool = True):
        self.enable_semantic = enable_semantic
        self.semantic_analyzer = LocalSemanticAnalyzer() if enable_semantic else None

    def analyze(self, records: List[KnowledgeRecord]) -> List[Finding]:
        findings: List[Finding] = []

        # Partition records by artifact type
        code_endpoints = [r for r in records if r.artifact_type == ArtifactType.CODE_ENDPOINT]
        doc_endpoints = [r for r in records if r.artifact_type == ArtifactType.DOC_ENDPOINT]
        code_versions = [r for r in records if r.artifact_type == ArtifactType.CODE_JAVA_VERSION]
        doc_versions = [r for r in records if r.artifact_type == ArtifactType.DOC_JAVA_VERSION]
        doc_claims = [r for r in records if r.artifact_type == ArtifactType.DOC_BEHAVIORAL_CLAIM]

        # 1. Analyze Java Version Consistency
        version_findings = self._analyze_versions(code_versions, doc_versions)
        findings.extend(version_findings)

        # 2. Analyze REST API Endpoint Consistency
        endpoint_findings = self._analyze_endpoints(code_endpoints, doc_endpoints)
        findings.extend(endpoint_findings)

        # 3. Analyze Behavioral & Semantic Claims
        if self.enable_semantic and self.semantic_analyzer:
            semantic_findings = self._analyze_semantic_claims(code_endpoints, doc_claims)
            findings.extend(semantic_findings)

        return findings

    def _analyze_versions(
        self,
        code_versions: List[KnowledgeRecord],
        doc_versions: List[KnowledgeRecord]
    ) -> List[Finding]:
        findings: List[Finding] = []

        if not code_versions or not doc_versions:
            return findings

        # Check latest or primary code version
        primary_code_ver = code_versions[0]
        code_val = primary_code_ver.metadata.get("normalized_version", "")

        for doc_ver in doc_versions:
            doc_val = doc_ver.metadata.get("normalized_version", "")
            finding_id = hashlib.sha256(f"ver:{primary_code_ver.id}:{doc_ver.id}".encode("utf-8")).hexdigest()[:16]

            if code_val and doc_val and code_val == doc_val:
                findings.append(Finding(
                    id=finding_id,
                    classification=Classification.CONSISTENT,
                    certainty=CertaintyLevel.VERIFIED_CONSISTENT,
                    title=f"Java Version Consistent: Java {code_val}",
                    explanation=f"Documentation in '{doc_ver.source_file}' specifies Java {doc_val}, matching pom.xml ({primary_code_ver.source_file}).",
                    doc_file=doc_ver.source_file,
                    doc_line=doc_ver.line_number,
                    doc_claim=doc_ver.concept_or_claim,
                    doc_snippet=doc_ver.evidence_snippet,
                    code_file=primary_code_ver.source_file,
                    code_line=primary_code_ver.line_number,
                    code_evidence=primary_code_ver.concept_or_claim,
                    code_snippet=primary_code_ver.evidence_snippet,
                    detection_method="DETERMINISTIC_VERSION_RULE",
                    suggested_action="No action needed. Documentation and build configuration are synchronized.",
                    metadata={"code_version": code_val, "doc_version": doc_val}
                ))
            elif code_val and doc_val and code_val != doc_val:
                findings.append(Finding(
                    id=finding_id,
                    classification=Classification.CONTRADICTORY,
                    certainty=CertaintyLevel.DEFINITIVE_MISMATCH,
                    title=f"Java Version Contradiction: Doc specifies Java {doc_val}, but pom.xml requires Java {code_val}",
                    explanation=(
                        f"Documentation in '{doc_ver.source_file}' (line {doc_ver.line_number}) specifies Java {doc_val}, "
                        f"whereas Maven configuration in '{primary_code_ver.source_file}' (line {primary_code_ver.line_number}) "
                        f"targets Java {code_val}. Developers attempting to build the project under Java {doc_val} will encounter build errors."
                    ),
                    doc_file=doc_ver.source_file,
                    doc_line=doc_ver.line_number,
                    doc_claim=doc_ver.concept_or_claim,
                    doc_snippet=doc_ver.evidence_snippet,
                    code_file=primary_code_ver.source_file,
                    code_line=primary_code_ver.line_number,
                    code_evidence=primary_code_ver.concept_or_claim,
                    code_snippet=primary_code_ver.evidence_snippet,
                    detection_method="DETERMINISTIC_VERSION_RULE",
                    suggested_action=f"Update '{doc_ver.source_file}' around line {doc_ver.line_number}: change required Java version from {doc_val} to {code_val}.",
                    metadata={"code_version": code_val, "doc_version": doc_val}
                ))

        return findings

    def _analyze_endpoints(
        self,
        code_endpoints: List[KnowledgeRecord],
        doc_endpoints: List[KnowledgeRecord]
    ) -> List[Finding]:
        findings: List[Finding] = []

        # Index code endpoints:
        # Key 1: exact (verb, canonical_path)
        # Key 2: path only (canonical_path) -> list of code records
        code_by_exact: Dict[Tuple[str, str], KnowledgeRecord] = {}
        code_by_path: Dict[str, List[KnowledgeRecord]] = {}

        for code_rec in code_endpoints:
            verb = code_rec.metadata.get("http_method", "GET").upper()
            route = code_rec.metadata.get("route_path", "/")
            canon_route = canonicalize_route(route)

            code_by_exact[(verb, canon_route)] = code_rec
            code_by_path.setdefault(canon_route, []).append(code_rec)

        matched_code_ids: Set[str] = set()

        # Step A: Evaluate every documented endpoint
        for doc_rec in doc_endpoints:
            doc_verb = doc_rec.metadata.get("http_method", "GET").upper()
            doc_route = doc_rec.metadata.get("route_path", "/")
            doc_canon = canonicalize_route(doc_route)
            finding_key = hashlib.sha256(f"ep:{doc_rec.id}".encode("utf-8")).hexdigest()[:16]

            # Case 1: Exact match on both HTTP method and route path
            if (doc_verb, doc_canon) in code_by_exact:
                matched_code = code_by_exact[(doc_verb, doc_canon)]
                matched_code_ids.add(matched_code.id)

                findings.append(Finding(
                    id=finding_key,
                    classification=Classification.CONSISTENT,
                    certainty=CertaintyLevel.VERIFIED_CONSISTENT,
                    title=f"Endpoint Consistent: {doc_verb} {doc_route}",
                    explanation=(
                        f"Documented endpoint '{doc_verb} {doc_route}' in '{doc_rec.source_file}' matches "
                        f"controller implementation in '{matched_code.source_file}' (method '{matched_code.metadata.get('method_name', '')}')."
                    ),
                    doc_file=doc_rec.source_file,
                    doc_line=doc_rec.line_number,
                    doc_claim=doc_rec.concept_or_claim,
                    doc_snippet=doc_rec.evidence_snippet,
                    code_file=matched_code.source_file,
                    code_line=matched_code.line_number,
                    code_evidence=matched_code.concept_or_claim,
                    code_snippet=matched_code.evidence_snippet,
                    detection_method="DETERMINISTIC_ENDPOINT_RULE",
                    suggested_action="No action needed. Documentation matches implementation.",
                    metadata={"doc_route": doc_route, "code_route": matched_code.metadata.get("route_path")}
                ))

            # Case 2: Route path exists in code, but HTTP method is CONTRADICTORY
            elif doc_canon in code_by_path:
                candidates = code_by_path[doc_canon]
                matched_code = candidates[0]
                matched_code_ids.add(matched_code.id)
                actual_verbs = [c.metadata.get("http_method", "GET").upper() for c in candidates]
                actual_verbs_str = ", ".join(actual_verbs)

                findings.append(Finding(
                    id=finding_key,
                    classification=Classification.CONTRADICTORY,
                    certainty=CertaintyLevel.DEFINITIVE_MISMATCH,
                    title=f"HTTP Method Contradiction: Doc specifies {doc_verb} {doc_route}, but code expects {actual_verbs_str}",
                    explanation=(
                        f"Documentation in '{doc_rec.source_file}' (line {doc_rec.line_number}) documents "
                        f"HTTP method '{doc_verb}' for route '{doc_route}', but the actual Java controller in "
                        f"'{matched_code.source_file}' (line {matched_code.line_number}) defines {actual_verbs_str} "
                        f"(method '{matched_code.metadata.get('method_name', '')}'). Clients calling {doc_verb} will receive 405 Method Not Allowed."
                    ),
                    doc_file=doc_rec.source_file,
                    doc_line=doc_rec.line_number,
                    doc_claim=doc_rec.concept_or_claim,
                    doc_snippet=doc_rec.evidence_snippet,
                    code_file=matched_code.source_file,
                    code_line=matched_code.line_number,
                    code_evidence=matched_code.concept_or_claim,
                    code_snippet=matched_code.evidence_snippet,
                    detection_method="DETERMINISTIC_ENDPOINT_RULE",
                    suggested_action=f"Update '{doc_rec.source_file}' at line {doc_rec.line_number}: change HTTP method '{doc_verb}' to '{actual_verbs_str}'.",
                    metadata={"doc_verb": doc_verb, "code_verbs": actual_verbs, "route": doc_route}
                ))

            # Case 3: Documented endpoint does NOT exist in code (Phantom / Removed / Outdated)
            else:
                # Check if there is a similar route via local semantic / string similarity
                closest_route = None
                highest_sim = 0.0

                if self.semantic_analyzer and code_endpoints:
                    code_routes = [c.metadata.get("route_path", "") for c in code_endpoints]
                    best_cand, sim_score, _ = self.semantic_analyzer.find_best_semantic_match(doc_route, code_routes)
                    if sim_score > 0.4:
                        closest_route = best_cand
                        highest_sim = sim_score

                explanation_extra = ""
                if closest_route:
                    explanation_extra = f" A similarly named route '{closest_route}' exists in code (semantic similarity: {highest_sim:.2f}), suggesting this route may have been renamed."

                findings.append(Finding(
                    id=finding_key,
                    classification=Classification.POTENTIALLY_OUTDATED,
                    certainty=CertaintyLevel.HIGH_PROBABILITY,
                    title=f"Potentially Removed Endpoint Documented: {doc_verb} {doc_route}",
                    explanation=(
                        f"Documentation in '{doc_rec.source_file}' (line {doc_rec.line_number}) documents '{doc_verb} {doc_route}', "
                        f"but no matching Spring controller endpoint was found anywhere in the source code."
                        f"{explanation_extra}"
                    ),
                    doc_file=doc_rec.source_file,
                    doc_line=doc_rec.line_number,
                    doc_claim=doc_rec.concept_or_claim,
                    doc_snippet=doc_rec.evidence_snippet,
                    code_file=None,
                    code_line=None,
                    code_evidence=None,
                    code_snippet=None,
                    detection_method="DETERMINISTIC_ENDPOINT_RULE",
                    suggested_action=(
                        f"Verify if '{doc_verb} {doc_route}' was deprecated or removed. "
                        f"If removed, remove the section from '{doc_rec.source_file}'. "
                        + (f"If renamed to '{closest_route}', update the route path." if closest_route else "")
                    ),
                    metadata={"doc_endpoint": f"{doc_verb} {doc_route}", "similar_route": closest_route, "similarity": highest_sim}
                ))

        # Step B: Identify code endpoints that are missing from documentation
        for code_rec in code_endpoints:
            if code_rec.id not in matched_code_ids:
                code_verb = code_rec.metadata.get("http_method", "GET").upper()
                code_route = code_rec.metadata.get("route_path", "/")
                code_canon = canonicalize_route(code_route)

                # Double check if any doc matched the canonical route
                doc_matches = [
                    d for d in doc_endpoints
                    if canonicalize_route(d.metadata.get("route_path", "/")) == code_canon
                ]
                if not doc_matches:
                    finding_key = hashlib.sha256(f"missing:{code_rec.id}".encode("utf-8")).hexdigest()[:16]
                    findings.append(Finding(
                        id=finding_key,
                        classification=Classification.MISSING,
                        certainty=CertaintyLevel.HIGH_PROBABILITY,
                        title=f"Undocumented API Endpoint in Code: {code_verb} {code_route}",
                        explanation=(
                            f"Java controller in '{code_rec.source_file}' (method '{code_rec.metadata.get('method_name', '')}', line {code_rec.line_number}) "
                            f"implements '{code_verb} {code_route}', but this endpoint is completely absent from all documentation files."
                        ),
                        doc_file=None,
                        doc_line=None,
                        doc_claim=None,
                        doc_snippet=None,
                        code_file=code_rec.source_file,
                        code_line=code_rec.line_number,
                        code_evidence=code_rec.concept_or_claim,
                        code_snippet=code_rec.evidence_snippet,
                        detection_method="DETERMINISTIC_ENDPOINT_RULE",
                        suggested_action=f"Add documentation for '{code_verb} {code_route}' in the project API documentation guide.",
                        metadata={"code_endpoint": f"{code_verb} {code_route}"}
                    ))

        return findings

    def _analyze_semantic_claims(
        self,
        code_endpoints: List[KnowledgeRecord],
        doc_claims: List[KnowledgeRecord]
    ) -> List[Finding]:
        """
        Analyzes natural language claims in documentation against code implementation symbols.
        Distinguishes potential mismatches needing human review from verified facts.
        """
        findings: List[Finding] = []
        if not self.semantic_analyzer or not doc_claims or not code_endpoints:
            return findings

        # Create candidate text descriptions from code endpoints
        code_texts = []
        for c in code_endpoints:
            desc = f"{c.metadata.get('http_method', '')} {c.metadata.get('route_path', '')} {c.metadata.get('method_name', '')} {c.evidence_snippet}"
            code_texts.append(desc)

        for claim in doc_claims:
            claim_text = claim.concept_or_claim
            best_cand, sim_score, best_idx = self.semantic_analyzer.find_best_semantic_match(claim_text, code_texts)

            # Look for semantic divergence: moderate similarity where text describes behavior
            # e.g., claim describes "sorted by registration date" while method name is "findAllOrderByUsername"
            if best_cand and 0.25 <= sim_score <= 0.75:
                matched_code = code_endpoints[best_idx]
                lower_claim = claim_text.lower()
                method_name = matched_code.metadata.get("method_name", "").lower()

                # Detect conflicting order or query modifiers
                order_conflict = ("date" in lower_claim and "username" in method_name) or ("asc" in lower_claim and "desc" in method_name)

                if order_conflict or "sorted by" in lower_claim:
                    finding_key = hashlib.sha256(f"sem:{claim.id}:{matched_code.id}".encode("utf-8")).hexdigest()[:16]
                    findings.append(Finding(
                        id=finding_key,
                        classification=Classification.POTENTIALLY_OUTDATED if order_conflict else Classification.UNCERTAIN,
                        certainty=CertaintyLevel.HUMAN_REVIEW_RECOMMENDED,
                        title=f"Behavioral Claim Divergence: Documentation vs Code Method",
                        explanation=(
                            f"Documentation claim in '{claim.source_file}' (line {claim.line_number}) states: '{claim_text}'. "
                            f"However, the corresponding implementation in '{matched_code.source_file}' (line {matched_code.line_number}) "
                            f"implements method '{matched_code.metadata.get('method_name', '')}' with semantic similarity {sim_score:.2f}. "
                            f"Human review is recommended to verify if the sorting/behavior documented is still accurate."
                        ),
                        doc_file=claim.source_file,
                        doc_line=claim.line_number,
                        doc_claim=claim_text,
                        doc_snippet=claim.evidence_snippet,
                        code_file=matched_code.source_file,
                        code_line=matched_code.line_number,
                        code_evidence=matched_code.concept_or_claim,
                        code_snippet=matched_code.evidence_snippet,
                        detection_method="SEMANTIC_COSINE_SIMILARITY",
                        suggested_action="Review documentation claim and compare with method implementation logic to confirm whether behavior is up to date.",
                        metadata={"semantic_similarity": sim_score}
                    ))

        return findings
