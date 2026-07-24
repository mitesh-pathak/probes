import argparse
import re
from pathlib import Path
import yaml

RESEARCH_DIR = Path("context/research_questions")


def parse_kv_pairs(pairs_list: list) -> dict:
    """Parses ['key1=val1', 'key2=val2'] into a dictionary with typed values."""
    res = {}
    if not pairs_list:
        return res
    for item in pairs_list:
        if "=" in item:
            k, v = item.split("=", 1)
            k, v = k.strip(), v.strip()
            if v.isdigit():
                res[k] = int(v)
            else:
                try:
                    res[k] = float(v)
                except ValueError:
                    if v.lower() in ["true", "false"]:
                        res[k] = v.lower() == "true"
                    else:
                        res[k] = v
    return res


def get_next_id(prefix: str, existing_ids: list) -> str:
    """Extracts max ID index for a prefix (e.g. 'rs001' or 's001') and returns next (e.g. 'rs002' or 's002')."""
    indices = []
    pattern = re.compile(rf"{prefix}(\d+)")
    for item in existing_ids:
        match = pattern.search(item)
        if match:
            indices.append(int(match.group(1)))
    next_num = max(indices, default=0) + 1
    return f"{prefix}{next_num:03d}"


def cmd_init(args):
    """Initializes a new research question YAML file."""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    existing_files = [f.stem for f in RESEARCH_DIR.glob("rs*.yml")]
    rs_id = get_next_id("rs", existing_files)

    metrics = parse_kv_pairs(args.metrics) if args.metrics else {}

    rs_data = {
        "id": rs_id,
        "title": args.title,
        "goal": args.goal,
        "current_state": "s001",
        "nodes": {
            "s001": {
                "label": args.baseline_label,
                "metrics": metrics,
                "status": "ACTIVE",
            }
        },
        "edges": [],
    }

    out_file = RESEARCH_DIR / f"{rs_id}.yml"
    with open(out_file, "w") as f:
        yaml.dump(rs_data, f, sort_keys=False)

    print(f"✓ Initialized research question '{rs_id}' at {out_file}")


def cmd_new_exp(args):
    """Stages a new candidate experiment node and edge."""
    target_file = RESEARCH_DIR / f"{args.rs}.yml"
    if not target_file.exists():
        raise FileNotFoundError(f"Research question file '{target_file}' not found.")

    with open(target_file, "r") as f:
        rs_data = yaml.safe_load(f)

    current_state = rs_data["current_state"]
    next_state_id = get_next_id("s", list(rs_data.get("nodes", {}).keys()))

    rs_data.setdefault("nodes", {})[next_state_id] = {
        "status": "PLANNED",
        "hypothesis": args.hypothesis,
        "delta": args.delta,
    }

    rs_data.setdefault("edges", []).append(
        {
            "from": current_state,
            "to": next_state_id,
            "delta": args.delta,
        }
    )

    with open(target_file, "w") as f:
        yaml.dump(rs_data, f, sort_keys=False)

    print(f"✓ Staged experiment '{next_state_id}' for research question '{args.rs}'")


def main():
    parser = argparse.ArgumentParser(description="Research Execution CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: init
    p_init = subparsers.add_parser("init", help="Start a new research question")
    p_init.add_argument("--title", required=True, help="Title of research question")
    p_init.add_argument("--goal", required=True, help="Goal condition string")
    p_init.add_argument(
        "--baseline-label", default="Baseline Model", help="Baseline label"
    )
    p_init.add_argument(
        "--metrics",
        nargs="*",
        help="Initial metrics e.g. latency_ms=650 f1_score=82.5",
    )
    p_init.set_defaults(func=cmd_init)

    # Command: new-exp
    p_new_exp = subparsers.add_parser("new-exp", help="Stage a new experiment node")
    p_new_exp.add_argument(
        "--rs", required=True, help="Research question ID (e.g. rs001)"
    )
    p_new_exp.add_argument(
        "--hypothesis", required=True, help="Hypothesis being tested"
    )
    p_new_exp.add_argument(
        "--delta", required=True, help="Description of change/delta"
    )
    p_new_exp.set_defaults(func=cmd_new_exp)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
