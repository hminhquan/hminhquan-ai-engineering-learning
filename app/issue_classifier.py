"""Convert synthetic Jira issue text into a validated classification."""

from collections.abc import Callable
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

Action = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class IssueClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["Bug", "Feature", "Question", "Risk"]
    priority: Literal["P1", "P2", "P3"]
    next_actions: list[Action] = Field(min_length=1)


def classify_issue(
    issue_text: str,
    prompt: str,
    generate: Callable[[str, str], str],
) -> IssueClassification:
    """Retry an invalid response once and raise if both attempts fail."""
    if not issue_text.strip():
        raise ValueError("Issue text must not be blank.")

    for attempt in range(2):
        try:
            return IssueClassification.model_validate_json(generate(prompt, issue_text))
        except ValidationError:
            if attempt == 1:
                raise
            prompt += "\nThe previous response was invalid. Return only JSON matching the schema."
    raise AssertionError("Classification attempts exhausted")
