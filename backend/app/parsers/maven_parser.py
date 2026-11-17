import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.app.knowledge.representation import (
    KnowledgeRecord,
    ArtifactType,
    ExtractionMethod
)

class MavenPomAnalyzer:
    """
    Parser for Maven pom.xml files.
    Extracts Java source/target versions, build properties, and dependency declarations.
    """

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

        return self.parse_pom_content(content, rel_file)

    def parse_pom_content(self, content: str, file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        lines = content.splitlines()

        # Remove XML namespace prefix to ease tag querying
        clean_content = re.sub(r'\sxmlns="[^"]+"', '', content, count=1)

        try:
            root = ET.fromstring(clean_content)
        except Exception:
            # If XML malformed, use line scanning
            return self._fallback_version_search(content, lines, file_path)

        # 1. Look for Java version in properties
        java_version = None
        tag_matched = None
        properties = root.find("properties")

        if properties is not None:
            for child in properties:
                tag = child.tag
                if tag in ("java.version", "maven.compiler.source", "maven.compiler.target", "maven.compiler.release"):
                    java_version = child.text.strip() if child.text else None
                    tag_matched = tag
                    break

        # 2. Look in plugins (maven-compiler-plugin)
        if not java_version:
            for plugin in root.iter("plugin"):
                art_id = plugin.find("artifactId")
                if art_id is not None and art_id.text == "maven-compiler-plugin":
                    config = plugin.find("configuration")
                    if config is not None:
                        for target_tag in ("release", "source", "target"):
                            val = config.find(target_tag)
                            if val is not None and val.text:
                                java_version = val.text.strip()
                                tag_matched = f"maven-compiler-plugin.{target_tag}"
                                break
                    if java_version:
                        break

        if java_version:
            # Normalize version (e.g., "1.8" -> "8", "17" -> "17")
            norm_ver = self.normalize_java_version(java_version)
            line_no = self._find_line_number(lines, tag_matched or java_version)
            snippet = self._get_snippet(lines, line_no)

            rec = KnowledgeRecord(
                id=KnowledgeRecord.generate_id(ArtifactType.CODE_JAVA_VERSION, f"java_version:{norm_ver}", file_path, line_no),
                artifact_type=ArtifactType.CODE_JAVA_VERSION,
                concept_or_claim=f"java_version:{norm_ver}",
                source_file=file_path,
                line_number=line_no,
                evidence_snippet=snippet,
                extraction_method=ExtractionMethod.XML_MAVEN_PARSER,
                metadata={
                    "raw_version": java_version,
                    "normalized_version": norm_ver,
                    "matched_tag": tag_matched
                }
            )
            records.append(rec)

        # 3. Extract project coordinates
        group_id = root.findtext("groupId") or ""
        artifact_id = root.findtext("artifactId") or ""
        version = root.findtext("version") or ""

        if artifact_id:
            concept = f"maven_artifact:{group_id}:{artifact_id}:{version}"
            line_no = self._find_line_number(lines, artifact_id)
            snippet = self._get_snippet(lines, line_no)
            records.append(KnowledgeRecord(
                id=KnowledgeRecord.generate_id(ArtifactType.CODE_CONFIG, concept, file_path, line_no),
                artifact_type=ArtifactType.CODE_CONFIG,
                concept_or_claim=concept,
                source_file=file_path,
                line_number=line_no,
                evidence_snippet=snippet,
                extraction_method=ExtractionMethod.XML_MAVEN_PARSER,
                metadata={"groupId": group_id, "artifactId": artifact_id, "version": version}
            ))

        return records

    def _fallback_version_search(self, content: str, lines: List[str], file_path: str) -> List[KnowledgeRecord]:
        records: List[KnowledgeRecord] = []
        match = re.search(r'<(?:java\.version|maven\.compiler\.source|maven\.compiler\.target)>([^<]+)<', content)
        if match:
            raw_ver = match.group(1).strip()
            norm_ver = self.normalize_java_version(raw_ver)
            line_no = content[:match.start()].count("\n") + 1
            snippet = self._get_snippet(lines, line_no)
            records.append(KnowledgeRecord(
                id=KnowledgeRecord.generate_id(ArtifactType.CODE_JAVA_VERSION, f"java_version:{norm_ver}", file_path, line_no),
                artifact_type=ArtifactType.CODE_JAVA_VERSION,
                concept_or_claim=f"java_version:{norm_ver}",
                source_file=file_path,
                line_number=line_no,
                evidence_snippet=snippet,
                extraction_method=ExtractionMethod.REGEX_EXTRACTION,
                metadata={"raw_version": raw_ver, "normalized_version": norm_ver}
            ))
        return records

    @staticmethod
    def normalize_java_version(ver_str: str) -> str:
        """Normalizes '1.8' to '8', '11.0.2' to '11', '17' to '17'."""
        v = ver_str.strip()
        if v.startswith("1."):
            parts = v.split(".")
            if len(parts) > 1:
                return parts[1]
        parts = re.split(r"[\.\-_]", v)
        return parts[0] if parts else v

    def _find_line_number(self, lines: List[str], target: str) -> int:
        for idx, line in enumerate(lines, start=1):
            if target in line:
                return idx
        return 1

    def _get_snippet(self, lines: List[str], line_no: int) -> str:
        start = max(0, line_no - 2)
        end = min(len(lines), line_no + 1)
        return "\n".join(lines[start:end]).strip()
