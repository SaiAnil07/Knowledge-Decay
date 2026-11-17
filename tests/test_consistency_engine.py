import pytest
from backend.app.parsers.java_parser import JavaSourceAnalyzer
from backend.app.parsers.maven_parser import MavenPomAnalyzer
from backend.app.parsers.markdown_parser import MarkdownDocAnalyzer
from backend.app.engine.consistency_engine import ConsistencyEngine
from backend.app.knowledge.representation import Classification, CertaintyLevel

def test_consistency_engine_end_to_end():
    # 1. Java Code with matching, mismatched, and missing endpoints
    java_code = """package com.example.demo;
    import org.springframework.web.bind.annotation.*;
    import java.util.List;

    @RestController
    @RequestMapping("/api/v1")
    public class SampleController {

        // Matching endpoint: GET /api/v1/users
        @GetMapping("/users")
        public List<String> getUsers() { return List.of(); }

        // Mismatched endpoint: Code has POST /api/v1/orders, but doc will claim GET
        @PostMapping("/orders")
        public String createOrder(@RequestBody String body) { return "ok"; }

        // Missing from doc: Code has POST /api/v1/payments/process, but doc doesn't mention it
        @PostMapping("/payments/process")
        public String processPayment() { return "paid"; }
    }
    """

    # 2. Maven POM with Java 17
    pom_xml = """<project>
        <properties>
            <java.version>17</java.version>
        </properties>
    </project>"""

    # 3. Markdown Doc with matching endpoint, mismatched method, phantom endpoint, and mismatched Java 11
    markdown_doc = """# API Documentation
    Prerequisites: Requires Java 11.

    ## Endpoints
    - GET /api/v1/users
    - GET /api/v1/orders
    - DELETE /api/v1/legacy/accounts/{id}

    Users are returned sorted by registration date ascending.
    """

    # Parse all
    java_analyzer = JavaSourceAnalyzer()
    maven_analyzer = MavenPomAnalyzer()
    doc_analyzer = MarkdownDocAnalyzer()

    records = []
    records.extend(java_analyzer.parse_source_code(java_code, "SampleController.java"))
    records.extend(maven_analyzer.parse_pom_content(pom_xml, "pom.xml"))
    records.extend(doc_analyzer.parse_markdown_content(markdown_doc, "README.md"))

    # Analyze
    engine = ConsistencyEngine(enable_semantic=True)
    findings = engine.analyze(records)

    # Validate classifications
    classifications = {f.classification for f in findings}
    assert Classification.CONSISTENT in classifications
    assert Classification.CONTRADICTORY in classifications
    assert Classification.POTENTIALLY_OUTDATED in classifications
    assert Classification.MISSING in classifications

    # Check Java version mismatch
    ver_finding = next(f for f in findings if "Java Version Contradiction" in f.title)
    assert ver_finding.classification == Classification.CONTRADICTORY
    assert ver_finding.certainty == CertaintyLevel.DEFINITIVE_MISMATCH
    assert "pom.xml requires Java 17" in ver_finding.title

    # Check HTTP method mismatch
    method_finding = next(f for f in findings if "HTTP Method Contradiction" in f.title)
    assert method_finding.classification == Classification.CONTRADICTORY
    assert method_finding.certainty == CertaintyLevel.DEFINITIVE_MISMATCH
    assert "/api/v1/orders" in method_finding.title

    # Check phantom endpoint
    phantom_finding = next(f for f in findings if "Potentially Removed Endpoint" in f.title)
    assert phantom_finding.classification == Classification.POTENTIALLY_OUTDATED
    assert "/api/v1/legacy/accounts" in phantom_finding.title

    # Check missing endpoint
    missing_finding = next(f for f in findings if "Undocumented API Endpoint in Code" in f.title)
    assert missing_finding.classification == Classification.MISSING
    assert "/api/v1/payments/process" in missing_finding.title

    # Check consistent endpoint
    consistent_finding = next(f for f in findings if "Endpoint Consistent" in f.title)
    assert consistent_finding.classification == Classification.CONSISTENT
    assert "/api/v1/users" in consistent_finding.title
