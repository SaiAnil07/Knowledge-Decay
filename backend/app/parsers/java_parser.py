import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import javalang
from javalang.tree import ClassDeclaration, MethodDeclaration, Annotation

from backend.app.knowledge.representation import (
    KnowledgeRecord,
    ArtifactType,
    ExtractionMethod
)

SPRING_MAPPING_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
    "RequestMapping": "REQUEST_MAPPING"
}

def normalize_path(path: str) -> str:
    """Normalizes an endpoint path, standardizing slashes and route params."""
    if not path:
        return "/"
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    # Replace multiple slashes with single slash
    p = re.sub(r"/+", "/", p)
    # Remove trailing slash unless path is just "/"
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p

def combine_routes(base_path: str, method_path: str) -> str:
    """Combines class-level base path with method-level subpath."""
    base = normalize_path(base_path or "")
    sub = normalize_path(method_path or "")
    if base == "/":
        return sub
    if sub == "/":
        return base
    return normalize_path(f"{base}{sub}")

class JavaSourceAnalyzer:
    """
    Syntax-aware parser for Java source files.
    Extracts REST API endpoints, annotations, class structures, and method metadata.
    Uses AST parsing with a resilient syntax-aware fallback mechanism.
    """

    def parse_file(self, file_path: str, rel_path: Optional[str] = None) -> List[KnowledgeRecord]:
        path_obj = Path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return []

        rel_file = rel_path or path_obj.name
        try:
            with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
                code_content = f.read()
        except Exception:
            return []

        return self.parse_source_code(code_content, rel_file)

    def parse_source_code(self, code: str, file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        lines = code.splitlines()

        # Try AST parsing first
        try:
            tree = javalang.parse.parse(code)
            records = self._parse_ast(tree, lines, file_path)
        except Exception:
            # Fallback to syntax-aware regex tokenizer
            records = self._parse_syntax_fallback(code, lines, file_path)

        return records

    def _extract_annotation_path(self, annotation: Annotation) -> Tuple[str, Optional[str]]:
        """
        Extracts (path, http_method) from an AST Annotation node.
        Handles both `@GetMapping("/path")` and `@RequestMapping(value="/path", method=RequestMethod.POST)`.
        """
        path = ""
        http_method: Optional[str] = None

        if annotation.element is None:
            return "", None

        # Case: @GetMapping("/users") -> Literal argument
        if isinstance(annotation.element, javalang.tree.Literal):
            val = str(annotation.element.value).strip("\"'")
            return val, None

        # Case: @RequestMapping(value = "/users", method = RequestMethod.GET)
        if isinstance(annotation.element, list):
            for elem in annotation.element:
                name = getattr(elem, "name", None)
                val_node = getattr(elem, "value", None)
                if name in ("value", "path") or name is None:
                    if isinstance(val_node, javalang.tree.Literal):
                        path = str(val_node.value).strip("\"'")
                    elif isinstance(val_node, list) and len(val_node) > 0:
                        first = val_node[0]
                        if hasattr(first, "value"):
                            path = str(first.value).strip("\"'")
                elif name == "method":
                    if hasattr(val_node, "member"):
                        http_method = str(val_node.member).upper()
                    elif hasattr(val_node, "value"):
                        http_method = str(val_node.value).upper()

        return path, http_method

    def _parse_ast(self, tree: Any, lines: List[str], file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []

        for path, node in tree.filter(ClassDeclaration):
            class_name = node.name
            class_base_path = ""

            # Check class annotations for @RequestMapping
            if node.annotations:
                for ann in node.annotations:
                    if ann.name == "RequestMapping":
                        sub_path, _ = self._extract_annotation_path(ann)
                        if sub_path:
                            class_base_path = sub_path

            # Process methods
            for method in node.methods:
                if not method.annotations:
                    continue

                for ann in method.annotations:
                    ann_name = ann.name
                    if ann_name in SPRING_MAPPING_ANNOTATIONS:
                        mapped_http = SPRING_MAPPING_ANNOTATIONS[ann_name]
                        extracted_path, explicit_method = self._extract_annotation_path(ann)
                        http_method = explicit_method or (mapped_http if mapped_http != "REQUEST_MAPPING" else "GET")

                        full_path = combine_routes(class_base_path, extracted_path)
                        line_no = method.position.line if method.position else 1

                        snippet = self._get_snippet(lines, line_no)
                        concept = f"{http_method} {full_path}"

                        metadata = {
                            "class_name": class_name,
                            "method_name": method.name,
                            "http_method": http_method,
                            "route_path": full_path,
                            "annotation": ann_name,
                            "parameters": [p.name for p in method.parameters] if method.parameters else []
                        }

                        rec = KnowledgeRecord(
                            id=KnowledgeRecord.generate_id(ArtifactType.CODE_ENDPOINT, concept, file_path, line_no),
                            artifact_type=ArtifactType.CODE_ENDPOINT,
                            concept_or_claim=concept,
                            source_file=file_path,
                            line_number=line_no,
                            evidence_snippet=snippet,
                            extraction_method=ExtractionMethod.AST_JAVA_PARSER,
                            metadata=metadata
                        )
                        records.append(rec)

        return records

    def _parse_syntax_fallback(self, code: str, lines: List[str], file_path: str) -> List[KnowledgeRecord]:
        """
        Syntax-aware regex fallback when AST parser encounters newer syntax dialect.
        Extracts class base path and mapping annotations with line numbers.
        """
        records: List[KnowledgeRecord] = []
        class_base_path = ""
        class_name = "UnknownClass"

        # Find class level @RequestMapping
        class_match = re.search(r'@(?:RestController|Controller)[^\{]*?(?:@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'])?[^\{]*?class\s+(\w+)', code, re.DOTALL)
        if class_match:
            if class_match.group(1):
                class_base_path = class_match.group(1)
            if class_match.group(2):
                class_name = class_match.group(2)

        # Regex for method mappings
        # Example: @GetMapping("/api/v1/users")
        mapping_pattern = re.compile(
            r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*'
            r'(?:\(\s*(?:(?:value|path)\s*=\s*)?["\']([^"\']*)["\']'
            r'(?:.*?method\s*=\s*(?:RequestMethod\.)?([A-Z]+))?.*?\))?\s*'
            r'(?:@\w+(?:\(.*?\))?\s*)*'  # other annotations
            r'(?:public|protected|private)?\s*(?:static\s+)?[\w<>,\[\]\s]+\s+(\w+)\s*\(',
            re.MULTILINE
        )

        for match in mapping_pattern.finditer(code):
            ann_type = match.group(1)
            sub_path = match.group(2) or ""
            explicit_verb = match.group(3)
            method_name = match.group(4) or "method"

            mapped_http = SPRING_MAPPING_ANNOTATIONS.get(ann_type, "GET")
            http_method = explicit_verb or (mapped_http if mapped_http != "REQUEST_MAPPING" else "GET")
            full_path = combine_routes(class_base_path, sub_path)

            # Determine line number
            char_idx = match.start()
            line_no = code[:char_idx].count("\n") + 1
            snippet = self._get_snippet(lines, line_no)
            concept = f"{http_method} {full_path}"

            metadata = {
                "class_name": class_name,
                "method_name": method_name,
                "http_method": http_method,
                "route_path": full_path,
                "annotation": ann_type
            }

            rec = KnowledgeRecord(
                id=KnowledgeRecord.generate_id(ArtifactType.CODE_ENDPOINT, concept, file_path, line_no),
                artifact_type=ArtifactType.CODE_ENDPOINT,
                concept_or_claim=concept,
                source_file=file_path,
                line_number=line_no,
                evidence_snippet=snippet,
                extraction_method=ExtractionMethod.SYNTAX_FALLBACK_PARSER,
                metadata=metadata
            )
            records.append(rec)

        return records

    def _get_snippet(self, lines: List[str], line_no: int, context_lines: int = 2) -> str:
        """Extracts context lines around a target line."""
        start = max(0, line_no - context_lines - 1)
        end = min(len(lines), line_no + context_lines)
        return "\n".join(lines[start:end]).strip()
