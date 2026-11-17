import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from markdown_it import MarkdownIt

from backend.app.knowledge.representation import (
    KnowledgeRecord,
    ArtifactType,
    ExtractionMethod
)
from backend.app.parsers.java_parser import normalize_path

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

class MarkdownDocAnalyzer:
    """
    Parser for Markdown and README documentation files.
    Extracts API endpoints, HTTP verbs, Java/tech version claims, and behavioral claims.
    Tracks section hierarchy, exact line numbers, and evidence snippets.
    """

    def __init__(self):
        self.md_parser = MarkdownIt("commonmark")

    def parse_file(self, file_path: str, rel_path: Optional[str] = None) -> List[KnowledgeRecord]:
        path_obj = Path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return []

        rel_file = rel_path or path_obj.name
        try:
            with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []

        return self.parse_markdown_content(content, rel_file)

    def parse_markdown_content(self, content: str, file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        lines = content.splitlines()

        # 1. Extract API endpoints using Markdown AST + Regex
        endpoint_records = self._extract_endpoints(lines, content, file_path)
        records.extend(endpoint_records)

        # 2. Extract Java version claims
        version_records = self._extract_java_versions(lines, content, file_path)
        records.extend(version_records)

        # 3. Extract behavioral statements (associated with endpoints or sections)
        behavioral_records = self._extract_behavioral_claims(lines, file_path)
        records.extend(behavioral_records)

        return records

    def _extract_endpoints(self, lines: List[str], full_content: str, file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        seen_endpoints = set()

        # Patterns to catch endpoints:
        # Pattern A: `GET /api/v1/users` or GET /api/v1/users
        # Pattern B: curl -X POST http://localhost:8080/api/v1/orders
        # Pattern C: Markdown table row: | POST | `/api/v1/orders` | Creates an order |
        pattern_plain = re.compile(
            r'(?:^|[\s`|*#(])(GET|POST|PUT|DELETE|PATCH)\s+([/][a-zA-Z0-9_\-\./{}:]+)',
            re.IGNORECASE
        )

        pattern_table_row = re.compile(
            r'\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*`?([/][a-zA-Z0-9_\-\./{}:]+)`?\s*\|',
            re.IGNORECASE
        )

        pattern_curl = re.compile(
            r'curl\s+.*?-(?:X\s+|request\s+)(GET|POST|PUT|DELETE|PATCH)\s+.*?https?://[^/]+([/][a-zA-Z0-9_\-\./{}:]+)',
            re.IGNORECASE
        )

        current_heading = "Top Level"

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                current_heading = stripped.lstrip("#").strip()

            # Check table rows first
            for match in pattern_table_row.finditer(line):
                verb = match.group(1).upper()
                route = normalize_path(match.group(2))
                key = f"{verb} {route}"
                if key not in seen_endpoints:
                    seen_endpoints.add(key)
                    snippet = self._get_snippet(lines, idx)
                    records.append(KnowledgeRecord(
                        id=KnowledgeRecord.generate_id(ArtifactType.DOC_ENDPOINT, key, file_path, idx),
                        artifact_type=ArtifactType.DOC_ENDPOINT,
                        concept_or_claim=key,
                        source_file=file_path,
                        line_number=idx,
                        evidence_snippet=snippet,
                        extraction_method=ExtractionMethod.MARKDOWN_AST_PARSER,
                        metadata={
                            "http_method": verb,
                            "route_path": route,
                            "section": current_heading,
                            "format": "markdown_table"
                        }
                    ))

            # Check standard verb + path pattern
            for match in pattern_plain.finditer(line):
                verb = match.group(1).upper()
                route = normalize_path(match.group(2))
                key = f"{verb} {route}"
                if key not in seen_endpoints:
                    seen_endpoints.add(key)
                    snippet = self._get_snippet(lines, idx)
                    records.append(KnowledgeRecord(
                        id=KnowledgeRecord.generate_id(ArtifactType.DOC_ENDPOINT, key, file_path, idx),
                        artifact_type=ArtifactType.DOC_ENDPOINT,
                        concept_or_claim=key,
                        source_file=file_path,
                        line_number=idx,
                        evidence_snippet=snippet,
                        extraction_method=ExtractionMethod.MARKDOWN_AST_PARSER,
                        metadata={
                            "http_method": verb,
                            "route_path": route,
                            "section": current_heading,
                            "format": "inline_or_block"
                        }
                    ))

            # Check curl command pattern
            for match in pattern_curl.finditer(line):
                verb = match.group(1).upper()
                route = normalize_path(match.group(2))
                key = f"{verb} {route}"
                if key not in seen_endpoints:
                    seen_endpoints.add(key)
                    snippet = self._get_snippet(lines, idx)
                    records.append(KnowledgeRecord(
                        id=KnowledgeRecord.generate_id(ArtifactType.DOC_ENDPOINT, key, file_path, idx),
                        artifact_type=ArtifactType.DOC_ENDPOINT,
                        concept_or_claim=key,
                        source_file=file_path,
                        line_number=idx,
                        evidence_snippet=snippet,
                        extraction_method=ExtractionMethod.MARKDOWN_AST_PARSER,
                        metadata={
                            "http_method": verb,
                            "route_path": route,
                            "section": current_heading,
                            "format": "curl_command"
                        }
                    ))

        return records

    def _extract_java_versions(self, lines: List[str], full_content: str, file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        seen_versions = set()

        # Regex matching:
        # "Java 17", "Java 11", "Java 8", "JDK 17", "JDK 21", "Java: 17", "Java Version: 17"
        version_pattern = re.compile(
            r'(?:(?:Requires|Prerequisites|Requirements|Target)?\s*(?:Java|JDK)\s*(?:Version)?\s*[:=\s]+)(\d+(?:\.\d+)?)',
            re.IGNORECASE
        )

        for idx, line in enumerate(lines, start=1):
            for match in version_pattern.finditer(line):
                raw_ver = match.group(1)
                norm_ver = self.normalize_java_version(raw_ver)
                concept = f"java_version:{norm_ver}"
                if concept not in seen_versions:
                    seen_versions.add(concept)
                    snippet = self._get_snippet(lines, idx)
                    records.append(KnowledgeRecord(
                        id=KnowledgeRecord.generate_id(ArtifactType.DOC_JAVA_VERSION, concept, file_path, idx),
                        artifact_type=ArtifactType.DOC_JAVA_VERSION,
                        concept_or_claim=concept,
                        source_file=file_path,
                        line_number=idx,
                        evidence_snippet=snippet,
                        extraction_method=ExtractionMethod.MARKDOWN_AST_PARSER,
                        metadata={
                            "raw_version": raw_ver,
                            "normalized_version": norm_ver,
                            "matched_text": match.group(0).strip()
                        }
                    ))

        return records

    def _extract_behavioral_claims(self, lines: List[str], file_path: str) -> List[KnowledgeRecord]:
        """
        Extracts semantic descriptions and behavioral claims under sections for semantic similarity checks.
        """
        records: List[KnowledgeRecord] = []
        current_heading = "General"

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                current_heading = stripped.lstrip("#").strip()
                continue

            # Look for descriptive sentences (> 25 characters, ending with a period or description)
            if len(stripped) > 25 and not stripped.startswith("```") and not stripped.startswith("|"):
                # Check if sentence contains descriptive keywords
                lower = stripped.lower()
                if any(kw in lower for kw in ["return", "creates", "deletes", "updates", "requires", "sorted by", "authenticates", "throws"]):
                    concept = f"claim:{stripped[:60]}"
                    snippet = self._get_snippet(lines, idx)
                    records.append(KnowledgeRecord(
                        id=KnowledgeRecord.generate_id(ArtifactType.DOC_BEHAVIORAL_CLAIM, concept, file_path, idx),
                        artifact_type=ArtifactType.DOC_BEHAVIORAL_CLAIM,
                        concept_or_claim=stripped,
                        source_file=file_path,
                        line_number=idx,
                        evidence_snippet=snippet,
                        extraction_method=ExtractionMethod.MARKDOWN_AST_PARSER,
                        metadata={
                            "section": current_heading,
                            "full_text": stripped
                        }
                    ))

        return records

    @staticmethod
    def normalize_java_version(ver_str: str) -> str:
        """Normalizes '1.8' to '8', '11' to '11', '17.0' to '17'."""
        v = ver_str.strip()
        if v.startswith("1."):
            parts = v.split(".")
            if len(parts) > 1:
                return parts[1]
        parts = re.split(r"[\.\-_]", v)
        return parts[0] if parts else v

    def _get_snippet(self, lines: List[str], line_no: int) -> str:
        start = max(0, line_no - 2)
        end = min(len(lines), line_no + 1)
        return "\n".join(lines[start:end]).strip()
