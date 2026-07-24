# Probes
> *My Tinker Lab, My Experiments, My Probes on AI.*


## Modus Operandi
> *"Everything should be made as simple as possible, but not simpler."*


## Core Hierarchy
* **Research:** A pointed, goal-based investigation driven by a primary research question.
* **Experiment:** A testable hypothesis designed to gather evidence for or against a research question.
* **Run:** A single execution of an experiment where `one variable` in the configuration is modified and tested.

Each successful or failed run generates an **Artifact** pushed to an experiment database (e.g., Weights & Biases) and recorded back into `./context/` to advance or prune the Directed Acyclic Graph (DAG).

```text
Artifact = {Run ID, Git Commit Hash, Parent Commit Hash, Metrics, Result Output}
```

Read more about the research hierarchy and DAG in [docs/RESEARCH.md](./docs/RESEARCH.md)


## Project Structure
| Directory | Purpose |
|---|---|
| [`configs/`](./configs/) | Configuration files for baselines and experiment runs. |
| [`context/`](./context/) | Accumulated knowledge graph (research questions and experiment logs). |
| [`dataset/`](./dataset/) | Datasets and benchmarks accumulated across research runs. |
| [`docs/`](./docs/) | Process guides and manuals ([`RESEARCH.md`](./docs/RESEARCH.md), [`EXPERIMENTS.md`](./docs/EXPERIMENTS.md), [`CODING.md`](./docs/CODING.md), [`SETUP.md`](./docs/SETUP.md)). |
| [`evals/`](./evals/) | Automated evaluation suites and scoring rubrics. |
| [`outputs/`](./outputs/) | Temporary run outputs (raw generations, logs). **Not committed to Git.** |
| [`src/`](./src/) | Reusable source code to execute experiments. |
| [`tests/`](./tests/) | Software unit tests for `src/`. |


## Getting Started
To set up your local environment and run your first probe, refer to **[`docs/SETUP.md`](./docs/SETUP.md)**.
