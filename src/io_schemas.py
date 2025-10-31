from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class AnalysisQuery(BaseModel):
    task: str = Field(description="User question or instruction")
    time_window_days: Optional[int] = Field(default=None)


class EvidenceTable(BaseModel):
    name: str
    description: str
    rows: List[dict]


class Insight(BaseModel):
    title: str
    metric_delta: dict
    segment_filters: dict
    evidence_refs: List[str]
    confidence: float


class Recommendation(BaseModel):
    action: str
    impact_hypothesis: str
    risk: str


class CreativeIdea(BaseModel):
    hook: str
    body: str
    cta: str


class Evaluation(BaseModel):
    correctness: float
    specificity: float
    actionability: float
    alignment: float
    comments: str

