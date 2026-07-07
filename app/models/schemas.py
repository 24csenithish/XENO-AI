# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class ModelRole(str, Enum):
    GENERAL = "general"
    CODING = "coding"
    REASONING = "reasoning"
    FAST = "fast"
    VISION = "vision"

class RoutingResult(BaseModel):
    role: ModelRole
    confidence: float
    reason: str

class ModelHealthInfo(BaseModel):
    role: ModelRole
    model_name: str
    status: str  # e.g. "AVAILABLE", "MISSING", "UNKNOWN"
