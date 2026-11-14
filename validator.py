def run_validation_gates(pred_graph: dict, truth_dict: dict, raw_text: str) -> list[str]:
    """Runs the Oracle Truth Gate and Text Grounding Gate. Checks for BOTH hallucinations and missing data."""
    errors = []

    # 1. Validate Singular Fields
    for field in ["product", "persona", "operating_context", "stakeholder"]:
        node = pred_graph.get(field)
        truth_val = truth_dict.get(field)

        # Did the LLM completely miss a field that exists in the truth?
        if truth_val is not None and (not node or not isinstance(node, dict)):
            errors.append(f"[{field}] MISSING ENTITY: The text contains '{truth_val}', but you missed it.")
            continue

        if node and isinstance(node, dict):
            val = node.get("value")
            quote = node.get("source_quote")

            # Gate 1: Truth Match
            if val != truth_val:
                errors.append(
                    f"[{field}] TRUTH REJECTION: You extracted '{val}', but this is mathematically incorrect.")

            # Gate 2: Grounding Match
            if quote:
                # Normalize spaces/newlines to a single space for fair comparison
                clean_quote = " ".join(quote.split())
                clean_text = " ".join(raw_text.split())

                if clean_quote not in clean_text:
                    errors.append(
                        f"[{field}] GROUNDING REJECTION: Your citation '{quote}' does not exist verbatim in the text.")

    # 2. Validate List Fields
    for field in ["journeys", "journey_steps", "needs", "requirements"]:
        nodes = pred_graph.get(field, [])
        truth_list = truth_dict.get(field, [])

        extracted_vals = []
        if isinstance(nodes, list):
            extracted_vals = [n.get("value") for n in nodes if isinstance(n, dict)]

        # Check for MISSING items (False Negatives)
        for t_val in truth_list:
            if t_val not in extracted_vals:
                errors.append(f"[{field}] MISSING ENTITY: You failed to extract the required item '{t_val}'.")

        # Check for HALLUCINATIONS / BAD QUOTES (False Positives)
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    val = node.get("value")
                    quote = node.get("source_quote")

                    if val not in truth_list:
                        errors.append(f"[{field}] TRUTH REJECTION: The item '{val}' is a hallucination or distractor.")

                    # APPLIED FIX: Same normalization logic for lists
                    if quote:
                        clean_quote = " ".join(quote.split())
                        clean_text = " ".join(raw_text.split())

                        if clean_quote not in clean_text:
                            errors.append(
                                f"[{field}] GROUNDING REJECTION: Your citation '{quote}' does not exist verbatim in the text.")

    return errors