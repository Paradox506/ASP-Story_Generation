def summarize_results(results):
    total = len(results)
    completed = sum(1 for r in results if r.get("stage") == "complete")
    satisfiable = sum(
        1
        for r in results
        if r.get("stage") == "complete" and r.get("asp", {}).get("satisfiable", False)
    )
    timing_vals = [r.get("llm_timing", {}) for r in results if r.get("llm_timing")]
    prompt_tokens = [t.get("prompt_tokens") for t in timing_vals if t.get("prompt_tokens") is not None]
    completion_tokens = [t.get("completion_tokens") for t in timing_vals if t.get("completion_tokens") is not None]
    elapsed = [t.get("elapsed") for t in timing_vals if t.get("elapsed") is not None]

    def average(values):
        return sum(values) / len(values) if values else 0.0

    return {
        "total_runs": total,
        "completed_runs": completed,
        "sat_runs": satisfiable,
        "success_rate": satisfiable / total if total else 0.0,
        "avg_prompt_tokens": average(prompt_tokens),
        "avg_completion_tokens": average(completion_tokens),
        "avg_elapsed": average(elapsed),
    }

