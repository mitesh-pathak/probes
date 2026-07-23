# Probes
My Tinker Lab, My Experiments, My Probes on AI

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

---
# Project Structure
To Be Added

## Add ./src as path
To import modules from under /src directory
```sh
touch .env
echo 'PYTHONPATH=./src' >> .env
```

---
# Run Environment
## Ensure .venv is activated
```sh
source .venv/bin/activate
```

## Ensure VS Code Can Run Using .venv Python Kernel
```sh
python -m ipykernel install --user --name=probes --display-name "Python (.venv: probes)"
```

## Run Tests
```sh
PYTHONPATH=./src pytest
```

---
# Python Files Convention
We will use `# %%` create cells similar to jupyter notebook in python file.
To execute a cell use `Shift + Enter`.

## Code Cell
```python
# %%
# # Load Libraries

import numpy as np
import pandas as pd

# %%
# # Load Data

df = pd.read_csv("data/data.csv")
df.head()
```

## Text / Markdown / Comments Cell
```python
# %%
# # Feature Engineering
#
# We normalize the features because
# KMeans is distance based.
#
# Formula:
#
#     z = (x - mean) / std
#
```