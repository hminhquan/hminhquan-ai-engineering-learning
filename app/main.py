"""Week 2 meeting notes API."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from app.schemas import MeetingAnalysis, MeetingRequest
from app.services import llm

app = FastAPI(title="Meeting Notes API")


@app.exception_handler(RequestValidationError)
async def invalid_input(_request: Request, _error: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Invalid meeting request."})


@app.post(
    "/analyze-meeting",
    response_model=MeetingAnalysis,
    responses={
        422: {"description": "Invalid meeting request"},
        429: {"description": "Model provider rate limit"},
        502: {"description": "Model provider failure or invalid output"},
        503: {"description": "Missing model configuration"},
        504: {"description": "Model provider timeout"},
    },
)
def analyze_meeting(request: MeetingRequest) -> MeetingAnalysis:
    try:
        return llm.analyze_meeting(request.meeting_text)
    except APITimeoutError:
        raise HTTPException(504, "Meeting analysis timed out.") from None
    except RateLimitError:
        raise HTTPException(429, "Meeting analysis is rate limited.") from None
    except (ValidationError, llm.InvalidModelResponse):
        raise HTTPException(502, "Model returned an invalid meeting analysis.") from None
    except APIError:
        raise HTTPException(502, "Model service request failed.") from None
    except llm.MissingConfiguration:
        raise HTTPException(503, "Meeting analysis is not configured.") from None
