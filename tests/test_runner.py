import json
from unittest.mock import MagicMock, patch
import pytest
import yaml

import runner
from runner import load_jsonl, run_experiment


# ============================================================================
# Unit Tests for load_jsonl
# ============================================================================

def test_load_jsonl_valid(tmp_path):
    """Loads valid JSONL records correctly."""
    dataset_file = tmp_path / "test_data.jsonl"
    content = (
        '{"input": "Hello", "target": {"name": "Alice"}}\n'
        '{"input": "World", "target": {"name": "Bob"}}\n'
    )
    dataset_file.write_text(content, encoding="utf-8")

    records = load_jsonl(str(dataset_file))

    assert len(records) == 2
    assert records[0] == {"input": "Hello", "target": {"name": "Alice"}}
    assert records[1] == {"input": "World", "target": {"name": "Bob"}}


def test_load_jsonl_ignores_empty_lines(tmp_path):
    """Skips blank or whitespace-only lines in JSONL files."""
    dataset_file = tmp_path / "test_data.jsonl"
    content = (
        '{"input": "Sample", "target": {}}\n'
        '\n'
        '   \n'
        '{"input": "Sample 2", "target": {}}\n'
    )
    dataset_file.write_text(content, encoding="utf-8")

    records = load_jsonl(str(dataset_file))

    assert len(records) == 2


# ============================================================================
# Mocked Test for run_experiment
# ============================================================================

def test_run_experiment_end_to_end(tmp_path, monkeypatch):
    """Verifies that run_experiment loads data, runs inference, invokes eval, and saves artifact."""
    # 1. Setup Mock Dataset & Config Files
    dataset_file = tmp_path / "dataset.jsonl"
    dataset_file.write_text(
        '{"input": "Sarah is 34.", "target": {"name": "Sarah", "age": 34}}\n',
        encoding="utf-8",
    )

    config_data = {
        "metadata": {
            "research_id": "rs001",
            "experiment_id": "exp_test",
            "parent_state": "s001",
        },
        "model": {
            "name_or_path": "dummy-model",
            "max_new_tokens": 10,
            "do_sample": False,
        },
        "task": {
            "dataset_path": str(dataset_file),
            "prompt_template": "Text: {text}",
        },
        "eval": {
            "module": "dummy_eval",
            "required_keys": ["name", "age"],
        },
    }

    config_file = tmp_path / "test_config.yml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    # Redirect OUTPUTS_DIR to tmp_path
    monkeypatch.setattr(runner, "OUTPUTS_DIR", tmp_path)

    # 2. Patch runner dependencies using context managers
    with patch.object(runner, "AutoTokenizer") as mock_tokenizer_cls, \
         patch.object(runner, "AutoModelForCausalLM") as mock_model_cls, \
         patch.object(runner, "importlib") as mock_importlib:

        # Setup Tokenizer Mock
        mock_tokenizer = MagicMock()
        mock_inputs = MagicMock()
        mock_inputs.input_ids.shape = [1, 5]
        mock_inputs.to.return_value = mock_inputs
        mock_tokenizer.return_value = mock_inputs
        mock_tokenizer.decode.return_value = '{"name": "Sarah", "age": 34}'
        mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer

        # Setup Model Mock
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_model.generate.return_value = [[1, 2, 3, 4, 5, 6, 7]]
        mock_model_cls.from_pretrained.return_value = mock_model

        # Setup Dynamic Eval Module Mock
        mock_eval_module = MagicMock()
        mock_eval_module.evaluate.return_value = {
            "metrics": {"valid_json_rate": 1.0, "exact_match_accuracy": 1.0},
            "details": [
                {
                    "input": "Sarah is 34.",
                    "target": {"name": "Sarah", "age": 34},
                    "raw_output": '{"name": "Sarah", "age": 34}',
                    "is_valid_json": True,
                    "is_exact_match": True,
                }
            ],
        }
        mock_importlib.import_module.return_value = mock_eval_module

        # 3. Execute Experiment
        metrics, output_path = run_experiment(str(config_file))

        # 4. Assertions
        assert "latency_ms" in metrics
        assert metrics["valid_json_rate"] == 1.0
        assert output_path.endswith("rs001_exp_test_run001.json")

        # Verify Output JSON Artifact Was Written
        with open(output_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)

        assert artifact["run_id"] == "rs001_exp_test_run001"
        assert artifact["metrics"]["valid_json_rate"] == 1.0
        assert len(artifact["predictions"]) == 1
