# Base Setup
## Setup virtual environment
```sh
python -m venv .venv --without-pip
source  .venv/bin/activate
```

## Install pip and other packages
```sh
curl -sS https://bootstrap.pypa.io/get-pip.py | python
pip install -r requirements.txt
```

## Add ./src as path for Development Setup
To import modules from under /src directory
```sh
touch .env
echo 'PYTHONPATH=./src' >> .env
```

## Setup src/ module To avoid `ModuleNotFoundError`
```sh
pip install -e .
```

## Ensure VS Code Can Run Using .venv Python Kernel
```sh
python -m ipykernel install --user --name=probes --display-name "Python (.venv: probes)"
```

## Run All Tests Using PyTest
```sh
pytest
```


---
# Key Commands
### Ensure .venv is activated
```sh
source .venv/bin/activate
```

### Create New Research
```sh
python -m research init \
  --title "SmolLM JSON Extraction Reliability" \
  --goal "json_valid_rate >= 0.90" \
  --baseline-label "Zero-Shot Prompt" \
  --metrics json_valid_rate=0.40 latency_ms=180
```

### View Research
Prints the GraphViz DOT format of the research graph.
```sh
python -m research graph  --rs rs001
```

### Running Experiment
Run your execution script by explicitly passing the target config path:
```sh
python -m runner --config configs/experiment.yml
```

### Record Experiment Results
```sh
python src/research.py record \
  --rs rs001 \
  --state s002 \
  --status failed \
  --lesson "Zero-shot model produces valid JSON structure initially but repeats output/hallucinates fields, causing string truncation and strict json.loads failure." \
  --metrics valid_json_rate=0.8 exact_match_accuracy=0.4 field_accuracy=0.6 latency_ms=1727.17
```


---
# Next Step
Learn how to [setup research](./RESEARCH.md) and [run experiements](./EXPERIMENTS.md).
