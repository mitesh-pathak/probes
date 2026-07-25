import pytest
from utils.evals import extract_first_json_block, evaluate


# ============================================================================
# Unit Tests for extract_first_json_block
# ============================================================================

def test_extract_first_json_block_clean():
    """Extracts valid JSON when input contains no surrounding text."""
    text = '{"name": "Alice", "age": 30}'
    assert extract_first_json_block(text) == '{"name": "Alice", "age": 30}'


def test_extract_first_json_block_with_surrounding_chatter():
    """Extracts JSON block when surrounded by LLM preamble and trailing text."""
    text = 'Here is your JSON:\n{\n  "name": "Bob",\n  "age": 25\n}\nHope this helps!'
    expected = '{\n  "name": "Bob",\n  "age": 25\n}'
    assert extract_first_json_block(text) == expected


def test_extract_first_json_block_multiple_blocks():
    """Extracts only the first JSON block when model repeats itself."""
    text = '{"name": "Marcus", "age": 22}\n\nJSON:\n{"name": "Marcus", "age": 22}'
    assert extract_first_json_block(text) == '{"name": "Marcus", "age": 22}'


def test_extract_first_json_block_no_braces():
    """Returns original text intact when no curly braces are present."""
    text = "Sorry, I cannot extract person details from this text."
    assert extract_first_json_block(text) == text


# ============================================================================
# Unit Tests for evaluate
# ============================================================================

def test_evaluate_perfect_match():
    """Returns 1.0 across all metrics when output matches target (casing normalized)."""
    predictions = [
        {
            "input": "Sarah Jenkins is a 34-year-old bio-engineer.",
            "raw_output": '{\n  "name": "Sarah Jenkins",\n  "age": 34,\n  "profession": "Bio-Engineer"\n}',
            "target": {"name": "Sarah Jenkins", "age": 34, "profession": "bio-engineer"},
        }
    ]
    required_keys = ["name", "age", "profession"]

    result = evaluate(predictions, required_keys)

    assert result["metrics"]["valid_json_rate"] == 1.0
    assert result["metrics"]["exact_match_accuracy"] == 1.0
    assert result["metrics"]["field_accuracy"] == 1.0
    assert len(result["details"]) == 1
    assert result["details"][0]["is_valid_json"] is True
    assert result["details"][0]["is_exact_match"] is True


def test_evaluate_invalid_json():
    """Handles truncated or malformed JSON gracefully with zero scores."""
    predictions = [
        {
            "input": "Marcus, 22, works as a barista.",
            "raw_output": '{"name": "Marcus", "age": 22, "profession":',  # Truncated
            "target": {"name": "Marcus", "age": 22, "profession": "barista"},
        }
    ]
    required_keys = ["name", "age", "profession"]

    result = evaluate(predictions, required_keys)

    assert result["metrics"]["valid_json_rate"] == 0.0
    assert result["metrics"]["exact_match_accuracy"] == 0.0
    assert result["metrics"]["field_accuracy"] == 0.0
    assert result["details"][0]["is_valid_json"] is False


def test_evaluate_partial_field_accuracy():
    """Correctly calculates field accuracy when only some keys match target."""
    predictions = [
        {
            "input": "Dr. Elena Rostova (age 51) was appointed head of cardiology.",
            "raw_output": '{\n  "name": "Dr. Elena Rostova",\n  "age": 51,\n  "profession": "cardiology"\n}',
            "target": {
                "name": "Elena Rostova",  # Miss: "Dr." prefix
                "age": 51,  # Match
                "profession": "head of cardiology",  # Miss
            },
        }
    ]
    required_keys = ["name", "age", "profession"]

    result = evaluate(predictions, required_keys)

    assert result["metrics"]["valid_json_rate"] == 1.0
    assert result["metrics"]["exact_match_accuracy"] == 0.0
    # 1 out of 3 fields correct ("age") -> ~0.333
    assert result["metrics"]["field_accuracy"] == pytest.approx(0.333, abs=0.01)


def test_evaluate_empty_predictions():
    """Handles empty prediction list without raising ZeroDivisionError."""
    result = evaluate([], required_keys=["name", "age"])

    assert result["metrics"]["valid_json_rate"] == 0.0
    assert result["metrics"]["exact_match_accuracy"] == 0.0
    assert result["metrics"]["field_accuracy"] == 0.0
    assert result["details"] == []
