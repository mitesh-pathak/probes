import argparse
import json
import re
from pathlib import Path
import yaml

RESEARCH_DIR = Path("artifacts/dag_research")
RUNS_DIR = Path("artifacts/experiment_runs")


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


def cmd_record(args):
    """Records run results, updates node/edge statuses, and outputs a run artifact JSON."""
    target_file = RESEARCH_DIR / f"{args.rs}.yml"
    if not target_file.exists():
        raise FileNotFoundError(f"Research question file '{target_file}' not found.")

    with open(target_file, "r") as f:
        rs_data = yaml.safe_load(f)

    state_id = args.state
    if state_id not in rs_data.get("nodes", {}):
        raise KeyError(f"State '{state_id}' not found in '{args.rs}.yml'.")

    is_success = args.status.lower() == "success"
    node_status = "ACTIVE" if is_success else "PRUNED"
    edge_status = "SUCCESS" if is_success else "FAILED"
    metrics = parse_kv_pairs(args.metrics) if args.metrics else {}

    # 1. Generate run artifact JSON
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    state_num = int(re.search(r"\d+", state_id).group())
    exp_num = max(1, state_num - 1)
    run_id = f"{args.rs}_exp{exp_num:03d}_run001"
    artifact_filename = f"{run_id}_artifact.json"
    artifact_path = RUNS_DIR / artifact_filename

    artifact_data = {
        "run_id": run_id,
        "research_id": args.rs,
        "target_state": state_id,
        "status": "Success" if is_success else "Failed",
        "metrics": metrics,
        "lesson": args.lesson,
    }

    with open(artifact_path, "w") as f:
        json.dump(artifact_data, f, indent=2)

    # 2. Update Node
    node_info = rs_data["nodes"][state_id]
    node_info["status"] = node_status
    node_info["metrics"] = metrics
    node_info["lesson"] = args.lesson

    # 3. Update Edge
    for edge in rs_data.get("edges", []):
        if edge.get("to") == state_id:
            edge["status"] = edge_status
            edge["lesson"] = args.lesson
            edge["artifact"] = str(artifact_path)

    # 4. Advance current_state ONLY if successful
    if is_success:
        rs_data["current_state"] = state_id

    with open(target_file, "w") as f:
        yaml.dump(rs_data, f, sort_keys=False)

    print(f"✓ Recorded run result for '{state_id}' in '{args.rs}' ({node_status})")
    print(f"  Artifact saved to {artifact_path}")


def cmd_status(args):
    """Prints a summary of a research question's current state and history."""
    target_file = RESEARCH_DIR / f"{args.rs}.yml"
    if not target_file.exists():
        raise FileNotFoundError(f"Research question file '{target_file}' not found.")

    with open(target_file, "r") as f:
        rs_data = yaml.safe_load(f)

    rs_id = rs_data.get("id", args.rs)
    title = rs_data.get("title", "")
    goal = rs_data.get("goal", "")
    curr_state = rs_data.get("current_state", "")

    nodes = rs_data.get("nodes", {})
    edges = rs_data.get("edges", [])

    print(f"=== Research Question: {rs_id} ===")
    print(f"Title: {title}")
    print(f"Goal: {goal}")
    print(f"Current State: {curr_state}")
    print("---")

    print("Nodes:")
    for nid, ninfo in nodes.items():
        status = ninfo.get("status", "UNKNOWN")
        label = ninfo.get("label") or ninfo.get("hypothesis") or ""
        metrics = ninfo.get("metrics", {})
        lesson = ninfo.get("lesson", "")

        is_current = " (CURRENT)" if nid == curr_state else ""
        print(f"  * {nid} [{status}]{is_current}: {label}")
        if metrics:
            print(f"    Metrics: {metrics}")
        if lesson:
            print(f"    Lesson: {lesson}")

    print("---")
    print("Edges / Transitions:")
    for edge in edges:
        src = edge.get("from")
        dst = edge.get("to")
        estatus = edge.get("status", "PLANNED")
        delta = edge.get("delta", "")
        lesson = edge.get("lesson", "")
        print(f"  * {src} -> {dst} [{estatus}]: Delta='{delta}'")
        if lesson:
            print(f"    Lesson: {lesson}")


def cmd_graph(args):
    """Outputs the research DAG in Graphviz DOT format."""
    target_file = RESEARCH_DIR / f"{args.rs}.yml"
    if not target_file.exists():
        raise FileNotFoundError(f"Research question file '{target_file}' not found.")

    with open(target_file, "r") as f:
        rs_data = yaml.safe_load(f)

    nodes = rs_data.get("nodes", {})
    edges = rs_data.get("edges", [])

    lines = [
        f"digraph {args.rs} {{",
        "  rankdir=LR;",
        '  node [shape=box, fontname="Helvetica"];',
        '  edge [fontname="Helvetica"];',
        "",
    ]

    # Render Nodes
    for nid, ninfo in nodes.items():
        label = ninfo.get("label") or ninfo.get("hypothesis") or "Unnamed State"
        safe_label = f"{nid}\\n{label}".replace('"', '\\"')
        lines.append(f'  {nid} [label="{safe_label}"];')

    lines.append("")

    # Render Edges
    for edge in edges:
        src = edge.get("from")
        dst = edge.get("to")
        delta = edge.get("delta")
        run_id = Path(edge["artifact"]).name.replace("_artifact.json", "") if edge.get("artifact") else edge.get("delta", "")
        label = f'{run_id} ({delta})'
        lines.append(f'  {run_id} [shape=plaintext, fontname="Helvetica", label="{label}"];')
        lines.append(f'  {src} -> {run_id}')
        lines.append(f'  {run_id} -> {dst}')


    lines.append("}")

    print("\n".join(lines))


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

    # Command: record
    p_record = subparsers.add_parser("record", help="Record experiment run result")
    p_record.add_argument(
        "--rs", required=True, help="Research question ID (e.g. rs001)"
    )
    p_record.add_argument(
        "--state", required=True, help="Target state ID (e.g. s002)"
    )
    p_record.add_argument(
        "--status",
        choices=["success", "failed"],
        required=True,
        help="Run outcome status",
    )
    p_record.add_argument(
        "--lesson", required=True, help="Key learning/takeaway summary"
    )
    p_record.add_argument(
        "--metrics",
        nargs="*",
        help="Final run metrics e.g. latency_ms=480 f1_score=81.8",
    )
    p_record.set_defaults(func=cmd_record)

    # Command: status
    p_status = subparsers.add_parser("status", help="Show research state summary")
    p_status.add_argument(
        "--rs", required=True, help="Research question ID (e.g. rs001)"
    )
    p_status.set_defaults(func=cmd_status)

    # Command: graph
    p_graph = subparsers.add_parser("graph", help="Print simplified DAG structure")
    p_graph.add_argument(
        "--rs", required=True, help="Research question ID (e.g. rs001)"
    )
    p_graph.set_defaults(func=cmd_graph)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
