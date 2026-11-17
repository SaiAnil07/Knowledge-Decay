import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, index=True)
    repo_path = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="COMPLETED")
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    scan_duration_ms = Column(Float, default=0.0)
    counts_consistent = Column(Integer, default=0)
    counts_contradictory = Column(Integer, default=0)
    counts_outdated = Column(Integer, default=0)
    counts_missing = Column(Integer, default=0)
    counts_uncertain = Column(Integer, default=0)

    # Relationships
    findings = relationship("FindingModel", back_populates="analysis_run", cascade="all, delete-orphan")
    files = relationship("DiscoveredFileModel", back_populates="analysis_run", cascade="all, delete-orphan")

class FindingModel(Base):
    __tablename__ = "findings"

    id = Column(String(128), primary_key=True, index=True)
    analysis_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False)
    classification = Column(String(50), nullable=False)
    certainty = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    explanation = Column(Text, nullable=False)

    doc_file = Column(String(500), nullable=True)
    doc_line = Column(Integer, nullable=True)
    doc_claim = Column(Text, nullable=True)
    doc_snippet = Column(Text, nullable=True)

    code_file = Column(String(500), nullable=True)
    code_line = Column(Integer, nullable=True)
    code_evidence = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)

    detection_method = Column(String(100), nullable=False)
    suggested_action = Column(Text, nullable=False)
    meta_json = Column(Text, default="{}")

    analysis_run = relationship("AnalysisRun", back_populates="findings")

class DiscoveredFileModel(Base):
    __tablename__ = "discovered_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False)
    relative_path = Column(String(500), nullable=False)
    absolute_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    size_bytes = Column(Integer, default=0)
    line_count = Column(Integer, default=0)

    analysis_run = relationship("AnalysisRun", back_populates="files")
