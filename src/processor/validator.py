from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    AUTOMATION = "автоматизація"
    INTEGRATION = "інтеграція"
    REPORT_ANALYTICS = "звіт/аналітика"
    BUG_SUPPORT = "баг/підтримка"
    QUESTION = "питання/консультація"
    OUT_OF_SCOPE = "поза скоупом"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestAnalysis(BaseModel):
    category: Category
    target_department: Optional[str] = Field(
        default=None,
        description="Requesting department or null if unclear",
    )
    priority: Priority
    short_summary: str = Field(
        max_length=150,
        description="One-sentence summary of the request in Ukrainian",
    )
    requested_actions: list[str] = Field(
        default_factory=list,
        description="List of concrete actions asked for",
    )
    needs_clarification: bool = Field(
        description="True if request is too vague to act on without follow-up",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Model self-reported confidence in classification (0–1)",
    )
