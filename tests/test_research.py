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


def test_new_exp_stages_candidate_node_and_edge(test_env):
    tmp_path, env = test_env

    # 1. Arrange: Initialize rs001
    subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "init",
            "--title",
            "Latency Research",
            "--goal",
            "Latency < 400ms",
        ],
        check=True,
        env=env,
    )

    # 2. Act: Stage a new experiment (new-exp)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "new-exp",
            "--rs",
            "rs001",
            "--hypothesis",
            "Quantization to INT8 will reduce latency by 40% without losing accuracy",
            "--delta",
            "Apply INT8 post-training quantization",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # 3. Assert CLI success
    assert result.returncode == 0, f"CLI Failed with stderr:\n{result.stderr}"

    # 4. Assert updated YAML content
    target_file = tmp_path / "context" / "research_questions" / "rs001.yml"
    with open(target_file) as f:
        data = yaml.safe_load(f)

    # State checks
    assert data["current_state"] == "s001"  # Still on baseline until recorded
    assert "s002" in data["nodes"]

    new_node = data["nodes"]["s002"]
    assert new_node["status"] == "PLANNED"
    assert new_node["hypothesis"] == "Quantization to INT8 will reduce latency by 40% without losing accuracy"
    assert new_node["delta"] == "Apply INT8 post-training quantization"

    # Edge checks
    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["from"] == "s001"
    assert edge["to"] == "s002"
    assert edge["delta"] == "Apply INT8 post-training quantization"

def test_record_successful_experiment_updates_dag_and_creates_artifact(test_env):
    tmp_path, env = test_env

    # 1. Arrange: Init rs001 and stage s002
    subprocess.run(
        [sys.executable, "-m", "research", "init", "--title", "Latency", "--goal", "Goal"],
        check=True,
        env=env,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "new-exp",
            "--rs",
            "rs001",
            "--hypothesis",
            "INT8 KV Cache reduces latency",
            "--delta",
            "Apply INT8",
        ],
        check=True,
        env=env,
    )

    # 2. Act: Record successful run for s002
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "record",
            "--rs",
            "rs001",
            "--state",
            "s002",
            "--status",
            "success",
            "--lesson",
            "Group size 64 preserves attention precision",
            "--metrics",
            "latency_ms=480",
            "f1_score=81.8",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"CLI Failed with stderr:\n{result.stderr}"

    # 3. Assert YAML update
    rs_file = tmp_path / "context" / "research_questions" / "rs001.yml"
    with open(rs_file) as f:
        data = yaml.safe_load(f)

    assert data["current_state"] == "s002"
    assert data["nodes"]["s002"]["status"] == "ACTIVE"
    assert data["nodes"]["s002"]["metrics"] == {"latency_ms": 480, "f1_score": 81.8}

    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["status"] == "SUCCESS"
    assert edge["lesson"] == "Group size 64 preserves attention precision"

    # 4. Assert artifact creation
    artifact_path = tmp_path / "context" / "experiment_runs" / "rs001_exp001_run001_artifact.json"
    assert artifact_path.exists()


def test_record_failed_experiment_prunes_node_and_keeps_current_state(test_env):
    tmp_path, env = test_env

    # 1. Arrange: Init and stage
    subprocess.run(
        [sys.executable, "-m", "research", "init", "--title", "Latency", "--goal", "Goal"],
        check=True,
        env=env,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "new-exp",
            "--rs",
            "rs001",
            "--hypothesis",
            "INT4 KV Cache",
            "--delta",
            "Apply INT4",
        ],
        check=True,
        env=env,
    )

    # 2. Act: Record failed run for s002
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research",
            "record",
            "--rs",
            "rs001",
            "--state",
            "s002",
            "--status",
            "failed",
            "--lesson",
            "Severe accuracy drop below 80%",
            "--metrics",
            "latency_ms=310",
            "f1_score=71.2",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"CLI Failed with stderr:\n{result.stderr}"

    # 3. Assert current_state remains anchored at s001
    rs_file = tmp_path / "context" / "research_questions" / "rs001.yml"
    with open(rs_file) as f:
        data = yaml.safe_load(f)

    assert data["current_state"] == "s001"
    assert data["nodes"]["s002"]["status"] == "PRUNED"
    assert data["edges"][0]["status"] == "FAILED"
