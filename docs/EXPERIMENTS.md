# Experiment Execution & Operational Guide
> *The operational manual for creating, running, evaluating, and recording probes.*


## Overview
If [RESEARCH.md](./RESEARCH.md) defines **why** and **what** we explore, this guide defines **how** we execute. Every experiment must be reproducible, isolated, and cleanly mapped back to our context graph.


## 1. Creating an Experiment
Before writing code or running a script, every experiment requires a clear hypothesis and a single configuration delta defined in its config file.
```sh
python -m research new-exp \
  --rs "rs001" \
  --hypothesis "Zero-shot extraction with SmolLM will achieve >70% valid JSON formatting on simple text samples." \
  --delta "Zero-shot prompt template without in-context examples"
```

### Step-by-Step Creation
1. **Identify Parent State:** Check `current_state` in `context/research_questions/rs001.yml` (e.g., `s002`).
2. **Define Experiment Metadata & Delta:** Create or edit `configs/experiment.yml`. Fill in the `metadata` header block (`research_id`, `experiment_id`, `parent_state`, `hypothesis`, `variable_delta`).


## 2. Running an Experiment
Execution must be deterministic. The runner reads metadata and parameters strictly from `configs/experiment.yml`.

### Execution Rules
1. **Never Hardcode Parameters or Metadata:** All hyperparameters, hypotheses, and research IDs must live inside `configs/experiment.yml`.
2. **Auto-logging Metadata:** `src/runner.py` must automatically parse the `metadata` block from the config and attach it to the generated run artifact JSON in `./context/experiment_runs/`.
3. **Outputs are Disposable:** Raw generations and temporary logs land in `./outputs/` and are **never committed to Git**.

### Setting Up Config From Parent State
```sh
git checkout <PARENT_COMMIT_HASH> -- configs/
```

### Running via CLI
Run your execution script by explicitly passing the target config path:
```sh
python src/runner.py --config configs/experiment.yml
```


## 3. Evaluating Experiments
Evaluation converts raw model generations into quantitative evidence (metrics) and qualitative insights (error analysis).

### Qualitative Evaluation (Manual Error Analysis)
* Inspect failure cases in `./outputs/`.
* Record *why* the model failed (e.g., hallucination, context truncation, instruction drift) inside the experiment log.
* Treat this qualitative feedback as an input when formulating the next hypothesis.

### Quantitative Evaluation
Run automated scoring against the outputs generated in `./outputs/`:
```sh
python evals/evaluate.py --output outputs/rs001_exp001_run001.json
```

### Key Metric Dimensions to Log
* **Accuracy / Quality:** F1 score, Perplexity, Exact Match, or LLM-as-a-Judge score.
* **Efficiency:** Latency (ms/token), Time To First Token (TTFT), Peak VRAM usage (GB).
* **Cost:** Token consumption count (input vs. output tokens).
* **Custom Score:** Distance metric from your defined Goal State.


## 4. Recording Experiments & Generating Artifacts (Manual)
Every run must generate an immutable **Run Artifact** and update the local context file.

### Artifact Schema
Ensure your run logger outputs structured metadata to stdout and your tracking tool (e.g., Weights & Biases):

```json
{
  "run_id": "rs001_exp001_run001",
  "git_commit_hash": "7a8b9c2",
  "parent_commit_hash": "1d2e3f4",
  "config_delta": {"kv_cache_dtype": "int8"},
  "metrics": {"f1_score": 81.8, "latency_ms": 480},
  "status": "Success",
  "note": "Met performance criteria; latency reduced without accuracy drop.",
  "result_output": "outputs/rs001_exp001_run001.json"
}
```

### Storing Artifacts
Save the artifact JSON in `./context/experiment_runs/` following this exact naming convention: `rs001_exp001_run001_artifact.json`


## 5. Updating the State DAG
Once runs are complete, record the state transition directly in `context/research_questions/rs<id>.yml` (e.g., `rs001.yml`):

* **If Successful:**
  - Add the new state node to `nodes` (e.g., `s002`) and set `current_state` to it.
  - Add an edge with `status: SUCCESS`, link the artifact JSON, and summarize the key `lesson`.
  - Update `configs/baseline.yml` with the newly proven parameters.

* **If Failed / Dead End:**
  - Add the failed state node to `nodes` (e.g., `s003`) with `status: PRUNED`.
  - Add an edge with `status: FAILED` and log the `lesson` (why it failed).
  - Keep `current_state` anchored at the active parent node and select the next hypothesis.

### Using Command line
```sh
PYTHONPATH=./src python -m research record \
  --rs rs001 \
  --state s002 \
  --status success \
  --lesson "Zero-shot extraction achieved valid JSON, but required strict 'ONLY valid JSON' instruction in prompt." \
  --metrics valid_rate=0.80 latency_ms=145.2
```

### Sample Research State File
Example: `context/research_questions/rs001.yml`

```yaml
id: rs001
title: "Reducing Inference Latency in Long-Context RAG"
goal: "Latency < 400ms with F1 >= 80.0%"
current_state: s002

nodes:
  s001:
    label: "Baseline: Zero-Shot Llama-3-8B"
    metrics: { latency_ms: 650, f1_score: 82.5 }
    status: ACTIVE

  s002:
    label: "INT8 KV Cache"
    metrics: { latency_ms: 480, f1_score: 81.8 }
    status: ACTIVE

  s003:
    label: "INT4 KV Cache"
    metrics: { latency_ms: 310, f1_score: 71.2 }
    status: PRUNED

edges:
  - source: s001
    target: s002
    status: SUCCESS
    run_id: rs001_exp001_run001
    artifact: context/experiment_runs/rs001_exp001_run001_artifact.json
    hypothesis: "Quantizing KV cache to INT8 reduces latency by >20% with <1% F1 loss."
    lesson: "Group size 64 preserves attention precision while reducing bandwidth pressure."

  - source: s001
    target: s003
    status: FAILED
    run_id: rs001_exp001_run002
    artifact: context/experiment_runs/rs001_exp001_run002_artifact.json
    hypothesis: "Quantizing KV cache to INT4 further reduces latency without accuracy drop."
    lesson: "Severe accuracy drop (F1 71.2% < 80%). Precision loss causes hallucinations in long context."
```
**NOTE**: Valid status are [PLANNED / ACTIVE / PRUNED] for nodes and [SUCCESS / FAILED] for edges


## Loading Graph

### Command line
```sh
PYTHONPATH=./src python -m research graph  --rs rs001
```

### Python Program
```python
import yaml, networkx as nx

# Load graph in 2 lines
with open("context/research_questions/rs001.yml") as f:
    data = yaml.safe_load(f)

# Convert to NetworkX DAG automatically
G = nx.DiGraph()
for edge in data["edges"]:
    G.add_edge(edge["source"], edge["target"], status=edge["status"], lesson=edge["lesson"])
```


## Tools
| Layer | Tool | Purpose |
|---|---|---|
| **Tracking & Logging** | Weights & Biases | Remote artifact, metrics, and hyperparameter tracking. |
| **Config Management** | PyYAML | Hierarchical YAML configuration loading. |
| **Evaluation** | Inspect AI | Open-source framework for evaluating LLM capabilities & safety. |
| **Deep Learning Engine** | PyTorch | Model execution and tensor operations. |
| **Model & Fine-Tuning** | Hugging Face (`transformers`, `accelerate`, `peft`, `trl`, `bitsandbytes`) | Model loading, PEFT/LoRA fine-tuning, quantization, and RLHF. |
| **LLM Gateway** | LiteLLM | Unified interface to call 100+ LLMs using OpenAI format. |
| **Vector Storage** | Pgvector (Postgres) | Embedding storage and vector similarity search for RAG. |
