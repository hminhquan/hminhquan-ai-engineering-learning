"""Classify one synthetic issue or evaluate one prompt on the gold set."""

import argparse
import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from app.issue_classifier import IssueClassification, classify_issue

ROOT = Path(__file__).resolve().parents[2]
VERSIONS = ("V1", "V2", "V3")
GOLD_PATH = ROOT / "data/evaluation/issue_classification_gold.json"
PROMPT_DIR = ROOT / "assignments/week-01/prompts"
EVIDENCE_DIR = ROOT / "evidence/week-01"


def load_prompts() -> dict[str, str]:
    schema = json.dumps(IssueClassification.model_json_schema())
    prompts = {}
    for version in VERSIONS:
        path = PROMPT_DIR / f"prompt-{version.lower()}.md"
        body = path.read_text(encoding="utf-8").strip()
        prompts[version] = f"{body}\n\nJSON schema:\n{schema}"
    return prompts


def evaluate(output_path, model, prompts, generate):
    cases = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    fields = (
        "prompt_version", "model", "issue_id", "expected_category", "expected_priority",
        "predicted_category", "predicted_priority", "next_actions", "schema_valid", "error",
    )
    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for version, prompt in prompts.items():
            category_hits = priority_hits = valid_outputs = 0
            p1_misses = []
            for case in cases:
                row = {
                    "prompt_version": version,
                    "model": model,
                    "issue_id": case["issue_id"],
                    "expected_category": case["category"],
                    "expected_priority": case["priority"],
                    "schema_valid": False,
                }
                try:
                    result = classify_issue(case["text"], prompt, generate)
                except (ValidationError, OpenAIError) as error:
                    row["error"] = type(error).__name__
                else:
                    valid_outputs += 1
                    row.update(
                        predicted_category=result.category,
                        predicted_priority=result.priority,
                        next_actions=json.dumps(result.next_actions, ensure_ascii=False),
                        schema_valid=True,
                    )

                category_hits += row.get("predicted_category") == case["category"]
                priority_hits += row.get("predicted_priority") == case["priority"]
                if case["priority"] == "P1" and row.get("predicted_priority") != "P1":
                    p1_misses.append(case["issue_id"])
                writer.writerow(row)

            total = len(cases)
            print(
                f"{version}: category {category_hits}/{total}, priority {priority_hits}/{total}, "
                f"valid JSON {valid_outputs}/{total}, P1 misses {', '.join(p1_misses) or 'none'}"
            )


def main(fixed_version: str | None = None) -> None:
    load_dotenv(ROOT / ".env.local")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL"), help="Override OPENAI_MODEL")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--text", help="One synthetic Jira issue")
    mode.add_argument(
        "--eval", nargs="?", const=True, type=Path, metavar="CSV",
        help="Write the selected prompt's CSV in evidence/week-01, or pass a custom path",
    )
    if fixed_version is None:
        parser.add_argument(
            "--version", choices=VERSIONS,
            help="Choose one prompt (required for --eval, defaults to V3 for --text)",
        )
    args = parser.parse_args()
    version = fixed_version or args.version
    if args.eval and version is None:
        parser.error("--eval requires one --version (V1, V2, or V3).")
    version = version or "V3"
    if not args.model:
        parser.error("Set OPENAI_MODEL in .env.local or pass --model.")
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("Set OPENAI_API_KEY in .env.local or the shell environment.")

    prompts = load_prompts()
    client = OpenAI(timeout=30.0)

    def generate(prompt: str, issue_text: str) -> str:
        response = client.responses.create(
            model=args.model,
            instructions=prompt,
            input=issue_text,
        )
        return response.output_text

    if args.eval:
        if args.eval is True:
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            output = EVIDENCE_DIR / f"eval-{version.lower()}.csv"
        else:
            output = args.eval
        evaluate(output, args.model, {version: prompts[version]}, generate)
    else:
        result = classify_issue(args.text, prompts[version], generate)
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
