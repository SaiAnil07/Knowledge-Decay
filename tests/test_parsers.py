import pytest
from backend.app.parsers.java_parser import JavaSourceAnalyzer, normalize_path, combine_routes
from backend.app.parsers.maven_parser import MavenPomAnalyzer
from backend.app.parsers.markdown_parser import MarkdownDocAnalyzer
from backend.app.knowledge.representation import ArtifactType

SAMPLE_JAVA_CODE = """package com.example.demo;

import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @GetMapping
    public List<String> getAllUsers() {
        return List.of("Alice", "Bob");
    }

    @GetMapping("/{id}")
    public String getUserById(@PathVariable Long id) {
        return "User " + id;
    }

    @PostMapping
    public String createUser(@RequestBody String user) {
        return "Created";
    }

    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        // delete logic
    }
}
"""

SAMPLE_POM_XML = """<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>knowledge-demo</artifactId>
    <version>1.0.0</version>
    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
</project>
"""

SAMPLE_MARKDOWN = """# User Service API Documentation

Prerequisites: Requires Java 17 and Maven 3.8.

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users` | Retrieve all active users |
| GET | `/api/v1/users/{id}` | Retrieve specific user by ID |
| POST | `/api/v1/users` | Create a new user profile |

### Legacy Endpoint
The system also provides:
`DELETE /api/v1/legacy/accounts/{id}` to purge obsolete accounts.

Users are returned sorted by registration date ascending.
"""

def test_java_parser():
    analyzer = JavaSourceAnalyzer()
    records = analyzer.parse_source_code(SAMPLE_JAVA_CODE, "UserController.java")

    assert len(records) == 4
    concepts = [r.concept_or_claim for r in records]
    assert "GET /api/v1/users" in concepts
    assert "GET /api/v1/users/{id}" in concepts
    assert "POST /api/v1/users" in concepts
    assert "DELETE /api/v1/users/{id}" in concepts

    # Check line numbers exist and are positive
    for r in records:
        assert r.line_number is not None and r.line_number > 0
        assert r.source_file == "UserController.java"

def test_maven_parser():
    analyzer = MavenPomAnalyzer()
    records = analyzer.parse_pom_content(SAMPLE_POM_XML, "pom.xml")

    version_records = [r for r in records if r.artifact_type == ArtifactType.CODE_JAVA_VERSION]
    assert len(version_records) >= 1
    assert version_records[0].concept_or_claim == "java_version:17"
    assert version_records[0].metadata["normalized_version"] == "17"

def test_markdown_parser():
    analyzer = MarkdownDocAnalyzer()
    records = analyzer.parse_markdown_content(SAMPLE_MARKDOWN, "docs/api.md")

    endpoints = [r for r in records if r.artifact_type == ArtifactType.DOC_ENDPOINT]
    concepts = [e.concept_or_claim for e in endpoints]

    assert "GET /api/v1/users" in concepts
    assert "GET /api/v1/users/{id}" in concepts
    assert "POST /api/v1/users" in concepts
    assert "DELETE /api/v1/legacy/accounts/{id}" in concepts

    versions = [r for r in records if r.artifact_type == ArtifactType.DOC_JAVA_VERSION]
    assert len(versions) == 1
    assert versions[0].concept_or_claim == "java_version:17"

    claims = [r for r in records if r.artifact_type == ArtifactType.DOC_BEHAVIORAL_CLAIM]
    assert len(claims) >= 1
