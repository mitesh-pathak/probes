import torch

from hello import hello_tensor


def test_hello_tensor():
    expected = torch.tensor([0, 1, 2, 3, 4])
    actual = hello_tensor()

    assert torch.equal(actual, expected)