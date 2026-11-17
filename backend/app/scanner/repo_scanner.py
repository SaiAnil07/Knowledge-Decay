import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field

# Directories to ignore during recursive repository discovery
DEFAULT_EXCLUDED_DIRS: Set[str] = {
    ".git", ".github", ".svn", ".hg",
    "node_modules", "target", "build", "bin", "out", "dist",
    ".idea", ".vscode", ".settings", ".project", ".classpath",
    ".gradle", ".mvn", "wrapper",
    "venv", ".env", "env", "__pycache__", ".pytest_cache", ".tox",
    "coverage", ".nyc_output", "target_classes"
}

# File extensions or names to ignore
IGNORED_FILE_EXTENSIONS: Set[str] = {
    ".class", ".jar", ".war", ".ear", ".zip", ".tar", ".gz",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".exe", ".dll", ".so", ".dylib", ".pyc"
}

class DiscoveredFile(BaseModel):
    relative_path: str
    absolute_path: str
    file_type: str  # "JAVA", "MARKDOWN", "MAVEN_POM", "README"
    size_bytes: int
    line_count: int = 0
    modified_time: float

class ScanResult(BaseModel):
    repo_path: str
    is_valid: bool
    error_message: Optional[str] = None
    total_files_discovered: int = 0
    total_lines: int = 0
    total_size_bytes: int = 0
    counts_by_type: Dict[str, int] = Field(default_factory=dict)
    files: List[DiscoveredFile] = Field(default_factory=list)
    scan_duration_ms: float = 0.0

class RepositoryScanner:
    def __init__(self, excluded_dirs: Optional[Set[str]] = None, max_file_size: int = 5 * 1024 * 1024):
        self.excluded_dirs = excluded_dirs or DEFAULT_EXCLUDED_DIRS
        self.max_file_size = max_file_size

    def validate_path(self, raw_path: str) -> tuple[bool, Optional[str], Optional[Path]]:
        """
        Validates that raw_path exists, is a directory, and is readable.
        Prevents path traversal vulnerabilities and returns resolved canonical path.
        """
        if not raw_path or not raw_path.strip():
            return False, "Repository path cannot be empty.", None

        try:
            path_obj = Path(raw_path.strip()).expanduser().resolve()
        except Exception as e:
            return False, f"Invalid path syntax: {str(e)}", None

        if not path_obj.exists():
            return False, f"Directory does not exist: {path_obj}", None

        if not path_obj.is_dir():
            return False, f"Path is a file, not a directory: {path_obj}", None

        if not os.access(path_obj, os.R_OK):
            return False, f"Directory is not readable (Permission Denied): {path_obj}", None

        return True, None, path_obj

    def classify_file(self, path: Path) -> Optional[str]:
        """Classify file into one of the supported types or return None if unsupported."""
        name_lower = path.name.lower()
        suffix_lower = path.suffix.lower()

        if suffix_lower in IGNORED_FILE_EXTENSIONS:
            return None

        if name_lower == "pom.xml":
            return "MAVEN_POM"
        elif name_lower.startswith("readme"):
            return "README"
        elif suffix_lower in {".md", ".markdown"}:
            return "MARKDOWN"
        elif suffix_lower == ".java":
            return "JAVA"

        return None

    def scan(self, raw_path: str) -> ScanResult:
        """
        Recursively scans the local repository for supported files while ignoring excluded directories.
        """
        start_time = time.perf_counter()
        is_valid, error, path_obj = self.validate_path(raw_path)

        if not is_valid or path_obj is None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ScanResult(
                repo_path=raw_path,
                is_valid=False,
                error_message=error,
                scan_duration_ms=round(duration_ms, 2)
            )

        discovered: List[DiscoveredFile] = []
        counts: Dict[str, int] = {"JAVA": 0, "MARKDOWN": 0, "README": 0, "MAVEN_POM": 0}
        total_size = 0
        total_lines = 0

        try:
            for root, dirs, files in os.walk(path_obj, topdown=True, followlinks=False):
                # Prune excluded directories in-place so os.walk does not traverse into them
                dirs[:] = [d for d in dirs if d not in self.excluded_dirs and not d.startswith(".")]

                for file_name in files:
                    file_path = Path(root) / file_name

                    # Check classification
                    file_type = self.classify_file(file_path)
                    if not file_type:
                        continue

                    try:
                        stat_info = file_path.stat()
                        size = stat_info.st_size

                        # Skip overly large files for safety
                        if size > self.max_file_size:
                            continue

                        # Count lines safely
                        line_count = 0
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                line_count = sum(1 for _ in f)
                        except Exception:
                            line_count = 0

                        rel_path = str(file_path.relative_to(path_obj)).replace("\\", "/")
                        abs_path = str(file_path.resolve()).replace("\\", "/")

                        discovered_file = DiscoveredFile(
                            relative_path=rel_path,
                            absolute_path=abs_path,
                            file_type=file_type,
                            size_bytes=size,
                            line_count=line_count,
                            modified_time=stat_info.st_mtime
                        )

                        discovered.append(discovered_file)
                        counts[file_type] = counts.get(file_type, 0) + 1
                        total_size += size
                        total_lines += line_count

                    except (PermissionError, FileNotFoundError):
                        continue

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ScanResult(
                repo_path=str(path_obj),
                is_valid=False,
                error_message=f"Error during repository scan: {str(e)}",
                scan_duration_ms=round(duration_ms, 2)
            )

        # Sort files deterministically by relative path
        discovered.sort(key=lambda x: x.relative_path)
        duration_ms = (time.perf_counter() - start_time) * 1000

        return ScanResult(
            repo_path=str(path_obj).replace("\\", "/"),
            is_valid=True,
            total_files_discovered=len(discovered),
            total_lines=total_lines,
            total_size_bytes=total_size,
            counts_by_type=counts,
            files=discovered,
            scan_duration_ms=round(duration_ms, 2)
        )
