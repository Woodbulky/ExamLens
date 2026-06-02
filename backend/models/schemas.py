"""
Pydantic schemas for ExamLens API request/response models.
These will be populated in later phases as endpoints are built.
"""

from pydantic import BaseModel
from typing import Optional


class HealthCheckResponse(BaseModel):
    """Response for the health check endpoint."""
    status: str
