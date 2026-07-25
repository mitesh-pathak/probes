import argparse
import importlib
import json
import time
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import yaml

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_jsonl(path: str) -> list[dict]:
    """Loads a JSONL dataset file into a list of dicts."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_experiment(config_path: str):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    meta = config["metadata"]
    model_cfg = config["model"]
    task_cfg = config["task"]
    eval_cfg = config["eval"]

    run_id = f"{meta['research_id']}_{meta['experiment_id']}_run001"
    print(f"🚀 Running Experiment: {run_id}")
    print(f"   Model   : {model_cfg['name_or_path']}")
    print(f"   Dataset : {task_cfg['dataset_path']}")

    # 1. Load Dataset from JSONL
    dataset = load_jsonl(task_cfg["dataset_path"])

    # 2. Load Model & Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["name_or_path"])
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model = AutoModelForCausalLM.from_pretrained(model_cfg["name_or_path"]).to(device)

    # 3. Inference Loop
    predictions = []
    total_latency_ms = 0.0

    for item in dataset:
        text_input = item["input"]
        target = item["target"]

        prompt = task_cfg["prompt_template"].format(text=text_input)
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        start = time.perf_counter()
        outputs = model.generate(
            **inputs,
            max_new_tokens=model_cfg.get("max_new_tokens", 60),
            do_sample=model_cfg.get("do_sample", False),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        total_latency_ms += elapsed_ms

        raw_text = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True
        ).strip()

        predictions.append(
            {
                "input": text_input,
                "target": target,
                "raw_output": raw_text,
                "latency_ms": round(elapsed_ms, 2),
            }
        )

    avg_latency = round(total_latency_ms / max(len(predictions), 1), 2)

    # 4. Import Evaluator Dynamically
    eval_module = importlib.import_module(eval_cfg["module"])
    eval_kwargs = {k: v for k, v in eval_cfg.items() if k != "module"}
    eval_result = eval_module.evaluate(predictions, **eval_kwargs)

    final_metrics = eval_result["metrics"]
    final_metrics["latency_ms"] = avg_latency

    # 5. Output Run Artifact
    output_artifact = {
        "run_id": run_id,
        "metadata": meta,
        "metrics": final_metrics,
        "predictions": eval_result["details"],
    }

    output_path = OUTPUTS_DIR / f"{run_id}.json"
    with open(output_path, "w") as f:
        json.dump(output_artifact, f, indent=2)

    print("\n" + "=" * 40)
    print("RESULTS SUMMARY:")
    for metric_name, val in final_metrics.items():
        print(f"  {metric_name:<20}: {val}")
    print("=" * 40)
    print(f"✓ Output saved to {output_path}\n")

    return final_metrics, str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yml")
    args = parser.parse_args()
    run_experiment(args.config)
