"""Run all labeled cases through the API and save predictions for review."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "data/evaluation/meeting_notes_gold.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8002")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/week-02/predictions.json")
    args = parser.parse_args()
    cases = json.loads(GOLD.read_text(encoding="utf-8"))

    with httpx.Client(base_url=args.url, timeout=40) as client, ThreadPoolExecutor(max_workers=3) as pool:
        def evaluate(case):
            response = client.post("/analyze-meeting", json={"meeting_text": case["input"]})
            print(f"{case['id']}: HTTP {response.status_code}", flush=True)
            return {"id": case["id"], "status": response.status_code, "result": response.json()}

        results = list(pool.map(evaluate, cases))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output:
        json.dump(results, output, indent=2, ensure_ascii=False)
        output.write("\n")
    if any(row["status"] != 200 for row in results):
        raise SystemExit("One or more cases failed. See the saved predictions.")


if __name__ == "__main__":
    main()
