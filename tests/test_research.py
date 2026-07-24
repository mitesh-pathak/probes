import os
import sys
import subprocess
import yaml
import pytest
from pathlib import Path

# Locate project root and src directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Sets up a temporary working directory for tests."""
    research_dir = tmp_path / "context" / "research_questions"
    research_dir.mkdir(parents=True)

    # Change working directory to tmp_path during test
    monkeypatch.chdir(tmp_path)

    # Prepare environment with PYTHONPATH pointing to src and root
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{PROJECT_ROOT}:{existing_pythonpath}"
    return tmp_path, env


def test_init_creates_rs001_when_no_prior_questions_exist(test_env):
    tmp_path, env = test_env

    # Act
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "init",
            "--title",
            "Reducing Inference Latency",
            "--goal",
            "Latency < 400ms",
            "--baseline-label",
            "Baseline Llama",
            "--metrics",
            "latency_ms=650",
            "f1_score=82.5",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # Assert CLI succeeded
    assert result.returncode == 0, f"CLI Failed with stderr:\n{result.stderr}"

    # Assert file creation
    target_file = tmp_path / "context" / "research_questions" / "rs001.yml"
    assert target_file.exists()

    # Assert YAML structure
    with open(target_file) as f:
        data = yaml.safe_load(f)

    assert data["id"] == "rs001"
    assert data["title"] == "Reducing Inference Latency"
    assert data["goal"] == "Latency < 400ms"
    assert data["current_state"] == "s001"
    assert "s001" in data["nodes"]
    assert data["nodes"]["s001"]["label"] == "Baseline Llama"
    assert data["nodes"]["s001"]["metrics"] == {"latency_ms": 650, "f1_score": 82.5}
    assert data["edges"] == []


def test_init_auto_increments_rs_id(test_env):
    tmp_path, env = test_env

    # Arrange: existing rs001.yml
    existing_file = tmp_path / "context" / "research_questions" / "rs001.yml"
    existing_file.write_text("id: rs001\n")

    # Act
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "init",
            "--title",
            "Second Question",
            "--goal",
            "Goal 2",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # Assert
    assert result.returncode == 0, f"CLI Failed with stderr:\n{result.stderr}"
    target_file = tmp_path / "context" / "research_questions" / "rs002.yml"
    assert target_file.exists()