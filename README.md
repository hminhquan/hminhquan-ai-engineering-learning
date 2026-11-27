# AI Engineering Fast-Track V12 – Member Starter Kit

Companion to `TMA_AI_Engineering_Fast_Track_Member_Package_v12_Self_Learning_Ready.pptx`.
This kit provides **real synthetic fixtures and reusable local tools**; it intentionally does **not** include completed assignment solutions.

## Quick start (macOS / Linux / Windows PowerShell equivalent)
1. Install **Python 3.11+**, Git and Docker; use an isolated training environment.
2. `python -m venv .venv` then activate the environment.
3. `pip install -r requirements.txt`.
4. `python scripts/smoke_test.py` — expected output ends with **PASS**.
5. `pytest -q tests/test_mock_jira.py` — expected **3 passed**.
6. `uvicorn app.mock_jira:app --reload --port 8001`; visit `http://127.0.0.1:8001/docs`.
7. Example read-only call: `curl -H 'X-Allowed-Project: ALPHA' http://127.0.0.1:8001/projects/ALPHA/sprints/12/issues`.
8. For W3, run `docker compose up -d db` and use pgvector. Your implementation should add the ingestion pipeline.

### Resource map
- `data/documents/`: 15 synthetic documents plus manifest (5 requirements, 5 technical, 5 PM)
- `data/jira/issues.json`: 30 sample issue records for Projects ALPHA/BETA/GAMMA
- `data/evaluation/`: 20 labeled issue cases, 20 retrieval queries, 30 RAG cases, 20 agent scenarios, 10 security cases
- `app/mock_jira.py`: working read-only mock Jira API for W5 onward
- `scripts/evaluate_issue_classifier.py`: scoring harness; supply CSV with headers `issue_id,predicted_category,predicted_priority`
- `evidence/weekly_pr_template.md`: required PR/evidence structure
- `assignments/`: weekly handoff instructions; slide deck contains full requirements and PASS criteria

## Safety and limitations
- **TRAINING FIXTURES ONLY.** Do not copy real customer data into model APIs without written approval.
- Mock authorization via `X-Allowed-Project` is **not suitable for production**. Replace with identity, authentication and server-side authorization in W7.
- LLM responses are nondeterministic; test using consistent model configuration, recorded prompt versions and human-reviewed evaluations.
- Hidden mentor assessment fixtures must remain **separate from this member-facing kit**.
- The `requirements.txt` pins broad compatible release families; AI Lead should lock tested versions before program rollout.
- No company-specific Git URL, API credentials, staging URLs or mentor contacts are invented. AI Lead must fill those in during kickoff.

## Week 2 meeting notes API

From the repository root, create a virtual environment and install the dependencies.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Set `OPENAI_API_KEY` and `OPENAI_MODEL` in the ignored `.env.local` file. The evaluation uses `gpt-6-luna`. Start the API from the repository root.

```bash
.venv/bin/python -m uvicorn app.main:app --port 8002 --env-file .env.local
```

Open [Swagger UI](http://127.0.0.1:8002/docs) or send a request from a second terminal.

```bash
curl -sS http://127.0.0.1:8002/analyze-meeting \
  -H 'Content-Type: application/json' \
  -d '{"meeting_text":"The team agreed to update the onboarding guide. Linh will draft the update. No deadline was agreed."}'
```

The response has a summary, a list of decisions and a list of actions. Each action has an owner, task and due date. Missing owners or deadlines are returned as JSON `null`.

```json
{
  "summary": "The team agreed to update the onboarding guide.",
  "decisions": ["Update the onboarding guide."],
  "actions": [
    {"owner": "Linh", "action": "Draft the update", "due_date": null}
  ]
}
```

Run the API tests and capture live predictions for the 20 labeled synthetic cases.

```bash
.venv/bin/python -m pytest -q tests/test_meeting_api.py
.venv/bin/python scripts/week-02/evaluate_meetings.py
```

The evaluation script writes `evidence/week-02/predictions.json`. Use a separate output path with `--output` to keep an existing run.
