import json
import re


def extract_first_json_block(text: str) -> str:
    """Extracts the first { ... } block from raw LLM text output using regex."""
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def evaluate(predictions: list[dict], required_keys: list[str]) -> dict:
    valid_syntax_count = 0
    exact_match_count = 0
    total_fields = 0
    correct_fields = 0
    details = []

    for pred in predictions:
        raw_text = pred.get("raw_output", "").strip()
        target = pred.get("target", {})

        # Extract first JSON block from potential chatter
        cleaned_json_str = extract_first_json_block(raw_text)

        is_valid_json = False
        is_exact_match = False

        try:
            parsed = json.loads(cleaned_json_str)
            is_valid_json = True
            valid_syntax_count += 1

            # Normalize values to lowercase strings for fair evaluation
            normalized_parsed = {
                k: str(v).lower().strip() for k, v in parsed.items() if k in required_keys
            }
            normalized_target = {
                k: str(v).lower().strip() for k, v in target.items()
            }

            if normalized_parsed == normalized_target:
                is_exact_match = True
                exact_match_count += 1

            for key, expected_val in normalized_target.items():
                total_fields += 1
                if normalized_parsed.get(key) == expected_val:
                    correct_fields += 1

        except (json.JSONDecodeError, TypeError, AttributeError):
            total_fields += len(target)

        details.append(
            {
                "input": pred.get("input"),
                "raw_output": raw_text,
                "cleaned_json": cleaned_json_str,
                "target": target,
                "is_valid_json": is_valid_json,
                "is_exact_match": is_exact_match,
            }
        )

    total_samples = max(len(predictions), 1)
    metrics = {
        "valid_json_rate": round(valid_syntax_count / total_samples, 3),
        "exact_match_accuracy": round(exact_match_count / total_samples, 3),
        "field_accuracy": round(correct_fields / max(total_fields, 1), 3),
    }

    return {"metrics": metrics, "details": details}
