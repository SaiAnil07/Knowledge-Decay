import tempfile
import pytest
from pathlib import Path
from backend.app.scanner.repo_scanner import RepositoryScanner

def test_validate_path_nonexistent():
    scanner = RepositoryScanner()
    valid, err, path_obj = scanner.validate_path("non_existent_folder_xyz_123")
    assert not valid
    assert "does not exist" in err

def test_validate_path_empty():
    scanner = RepositoryScanner()
    valid, err, path_obj = scanner.validate_path("")
    assert not valid
    assert "empty" in err

def test_scanner_with_temp_repo():
    scanner = RepositoryScanner()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create sample files
        (tmp_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
        (tmp_path / "README.md").write_text("# Test Project", encoding="utf-8")

        src_dir = tmp_path / "src" / "main" / "java"
        src_dir.mkdir(parents=True)
        (src_dir / "App.java").write_text("public class App {}", encoding="utf-8")

        # Create ignored folder
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config.md").write_text("should be ignored", encoding="utf-8")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        (target_dir / "App.class").write_text("binary", encoding="utf-8")

        res = scanner.scan(str(tmp_path))
        assert res.is_valid
        assert res.total_files_discovered == 3
        assert res.counts_by_type["MAVEN_POM"] == 1
        assert res.counts_by_type["README"] == 1
        assert res.counts_by_type["JAVA"] == 1
        assert res.counts_by_type.get("MARKDOWN", 0) == 0

        # Ensure .git and target files were not discovered
        discovered_paths = [f.relative_path for f in res.files]
        assert not any(".git" in p for p in discovered_paths)
        assert not any("target" in p for p in discovered_paths)
