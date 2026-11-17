from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import hashlib

class ArtifactType(str, Enum):
    CODE_ENDPOINT = "CODE_ENDPOINT"
    DOC_ENDPOINT = "DOC_ENDPOINT"
    CODE_JAVA_VERSION = "CODE_JAVA_VERSION"
    DOC_JAVA_VERSION = "DOC_JAVA_VERSION"
    CODE_CONFIG = "CODE_CONFIG"
    DOC_CONFIG = "DOC_CONFIG"
    DOC_BEHAVIORAL_CLAIM = "DOC_BEHAVIORAL_CLAIM"

class ExtractionMethod(str, Enum):
    AST_JAVA_PARSER = "AST_JAVA_PARSER"
    SYNTAX_FALLBACK_PARSER = "SYNTAX_FALLBACK_PARSER"
    XML_MAVEN_PARSER = "XML_MAVEN_PARSER"
    MARKDOWN_AST_PARSER = "MARKDOWN_AST_PARSER"
    REGEX_EXTRACTION = "REGEX_EXTRACTION"
    SEMANTIC_EMBEDDING = "SEMANTIC_EMBEDDING"

class Classification(str, Enum):
    CONSISTENT = "CONSISTENT"
    POTENTIALLY_OUTDATED = "POTENTIALLY_OUTDATED"
    CONTRADICTORY = "CONTRADICTORY"
    MISSING = "MISSING"
    UNCERTAIN = "UNCERTAIN"

class CertaintyLevel(str, Enum):
    DEFINITIVE_MISMATCH = "DEFINITIVE_MISMATCH"
    HIGH_PROBABILITY = "HIGH_PROBABILITY"
    HUMAN_REVIEW_RECOMMENDED = "HUMAN_REVIEW_RECOMMENDED"
    VERIFIED_CONSISTENT = "VERIFIED_CONSISTENT"

class KnowledgeRecord(BaseModel):
    id: str = Field(description="Deterministic or UUID identifier for record")
    artifact_type: ArtifactType
    concept_or_claim: str = Field(description="Normalized concept, route, or version identifier")
    source_file: str = Field(description="Relative path of file")
    line_number: Optional[int] = Field(default=None, description="Line number if available (1-indexed)")
    evidence_snippet: str = Field(default="", description="Source code or documentation line excerpt")
    extraction_method: ExtractionMethod
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Parsed attributes like HTTP method, params, etc.")

    @classmethod
    def generate_id(cls, artifact_type: str, concept: str, source_file: str, line_number: Optional[int] = None) -> str:
        key = f"{artifact_type}:{concept}:{source_file}:{line_number or 0}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

class Finding(BaseModel):
    id: str
    classification: Classification
    certainty: CertaintyLevel
    title: str
    explanation: str
    doc_file: Optional[str] = None
    doc_line: Optional[int] = None
    doc_claim: Optional[str] = None
    doc_snippet: Optional[str] = None
    code_file: Optional[str] = None
    code_line: Optional[int] = None
    code_evidence: Optional[str] = None
    code_snippet: Optional[str] = None
    detection_method: str
    suggested_action: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
