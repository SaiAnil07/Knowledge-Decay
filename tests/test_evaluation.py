import os
import pytest
from pathlib import Path
from backend.app.evaluation.benchmark import BenchmarkEvaluator

def test_benchmark_sample_project():
    sample_dir = Path(__file__).parent.parent / "sample_java_project"
    assert sample_dir.exists(), "sample_java_project folder must exist"

    evaluator = BenchmarkEvaluator()

    # 1. Evaluate Rule-based mode
    metrics_rule = evaluator.evaluate(str(sample_dir), enable_semantic=False)
    assert metrics_rule.precision > 0.8
    assert metrics_rule.recall > 0.7
    assert metrics_rule.f1_score > 0.75

    # 2. Evaluate Hybrid Semantic mode
    metrics_hybrid = evaluator.evaluate(str(sample_dir), enable_semantic=True)
    assert metrics_hybrid.precision > 0.8
    assert metrics_hybrid.recall >= metrics_rule.recall
    assert metrics_hybrid.f1_score >= metrics_rule.f1_score

    # Print comparative results for transparency
    print(f"\nRule-based: Precision={metrics_rule.precision:.2f}, Recall={metrics_rule.recall:.2f}, F1={metrics_rule.f1_score:.2f}")
    print(f"Hybrid Semantic: Precision={metrics_hybrid.precision:.2f}, Recall={metrics_hybrid.recall:.2f}, F1={metrics_hybrid.f1_score:.2f}")
