# %%
# # Markdown / Comment Cell Example
#

# %%
# Code Cell 1
import torch

# %%
# Code Cell 1
def hello_tensor() -> torch.Tensor:
    """Return a simple tensor to verify PyTorch is working."""
    return torch.arange(5)

# %%
# Run only if main
if __name__ == '__main__':
    print("Hello World!")