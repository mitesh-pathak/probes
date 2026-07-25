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
