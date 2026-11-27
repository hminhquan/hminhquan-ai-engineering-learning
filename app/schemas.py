"""Request and response contracts for meeting analysis."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class MeetingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meeting_text: NonBlankText


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: NonBlankText | None
    action: NonBlankText
    due_date: date | None


class MeetingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: NonBlankText
    decisions: list[NonBlankText]
    actions: list[ActionItem]
