# Probes
My Tinker Lab, My Experiments, My Probes on AI

---
# Project Structure
Follow these directories for
* [Source Files & Conventions](./src/)
* [Tests (Pytest)](./tests/)
* [Experiments](./src/experiments/)
* [Utilities](./src/utils/)

---
# Base Setup
## Setup virtual environment
```sh
python3 -m venv .venv --without-pip 
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

## Ensure VS Code Can Run Using .venv Python Kernel
```sh
python -m ipykernel install --user --name=probes --display-name "Python (.venv: probes)"
```

## Note On Run Any Files
Include PYTHONPATH=./src to ensure the models are loaded and avoid `ModuleNotFoundError`.
```sh
export PYTHONPATH=./src
```