import json
import re
import ollama

# Change this to "qwen2.5:7b" or "qwen2.5:14b" for your subsequent benchmark runs
TARGET_MODEL = "qwen2.5:3b"
def extract_and_refine(text_chunk: str, truth_dict: dict, validator_func) -> dict:
    """Multi-step agent pipeline that returns a full execution trace."""
    # This dictionary will store the exact state at every step
    trace = {
        "agent_1_graph": None,
        "validator_errors": [],
        "agent_2_graph": None,
        "final_graph": None,
    }
    # AGENT 1: Extractor
    system_prompt = (
        "You are a deterministic data engineering agent executing a strict ontological mapping task. "
        "Extract the business context from the provided text into a highly structured JSON object.\n\n"
        "=== ONTOLOGICAL DEFINITIONS ===\n"
        "1. 'product': The specific primary system, platform, or application being developed.\n"
        "2. 'persona': The primary target user or role the system is built for. Ignore individuals who are merely making requests, commenting, or vetoing ideas.\n"
        "3. 'operating_context': The complete physical, environmental, or situational condition the persona is experiencing. Extract the entire continuous phrase describing the condition.\n"
        "4. 'stakeholder': A strict composite entity. ONLY populate this if both 'persona' and 'operating_context' exist in the text. You must format this exactly as: \"[Persona] operating in [operating_context]\".\n"
        "5. 'journeys': High-level business workflows or overarching operational goals.\n"
        "6. 'journey_steps': Granular, chronological execution actions that support a journey.\n"
        "7. 'needs': Non-negotiable operational objectives or business capabilities required.\n"
        "8. 'requirements': Specific technical components strictly mandated or approved. Ignore any technologies that are explicitly rejected, vetoed, or deprecated.\n\n"
        "=== JSON SCHEMA & FORMATTING RULES ===\n"
        "- Every extracted entity MUST be a nested JSON object containing exactly two keys: 'value' (the extracted string) and 'source_quote' (the exact, verbatim substring from the text that grounds it).\n"
        "- Singular fields (product, persona, operating_context, stakeholder) must be the nested object or `null` if missing.\n"
        "- List fields (journeys, journey_steps, needs, requirements) must be an array of nested objects, or an empty array `[]` if missing.\n"
        "- HUMAN ROUTING RULE: Leave fields `null` or `[]` if they are missing from the text. DO NOT generate an entry in the 'human_questions' array simply because data is absent. ONLY populate 'human_questions' if the text contains a direct conflict, unresolvable ambiguity, or explicit prompt from a human asking for clarification.\n"
        "- STRIP CONVERSATIONAL FILLER: Extract ONLY the exact core entity. Do not include introductory words, but do not truncate the core descriptive phrase itself.\n\n"
        "=== EXAMPLE OUTPUT FORMAT ===\n"
        "{\n"
        "  \"product\": {\"value\": \"Core Engine\", \"source_quote\": \"building the Core Engine\"},\n"
        "  \"persona\": {\"value\": \"Lead Tech\", \"source_quote\": \"targeting the Lead Tech\"},\n"
        "  \"operating_context\": {\"value\": \"remote sites during outages\", \"source_quote\": \"remote sites during outages\"},\n"
        "  \"stakeholder\": {\"value\": \"Lead Tech operating in remote sites during outages\", \"source_quote\": \"Lead Tech operating in remote sites during outages\"},\n"
        "  \"journeys\": [],\n"
        "  \"journey_steps\": [],\n"
        "  \"needs\": [{\"value\": \"fast sync\", \"source_quote\": \"need fast sync\"}],\n"
        "  \"requirements\": [],\n"
        "  \"human_questions\": []\n"
        "}\n\n"
        "=== ANTI-HALLUCINATION DIRECTIVE ===\n"
        "DO NOT INVENT, PARAPHRASE, OR INFER DATA. If an entity is not explicitly stated in the text, you must omit it (return null or []). Your exact quotes will be checked programmatically.\n\n"
        "=== OUTPUT FORMAT (CRITICAL) ===\n"
        "You must respond with raw, valid JSON only. DO NOT include markdown formatting (like ```json). "
        "DO NOT include any conversational filler before or after the JSON object. "
        "Your output must begin immediately with the '{' character and end with the '}' character."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract graph for:\n\n{text_chunk}"}
    ]

    try:
        # APPLIED FIX: temperature=0.1 and num_ctx=8192 to maximize Titan RTX overhead memory
        response = ollama.chat(model=TARGET_MODEL, messages=messages, options={"temperature": 0.0, "num_predict": 1024, "num_ctx": 8192})
        # BULLETPROOF PARSER: Find everything between the first { and last }
        raw_text = response['message']['content'].strip()
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        clean_text = match.group(0) if match else raw_text
        pred_graph = json.loads(clean_text)
        trace["agent_1_graph"] = pred_graph
    except Exception as e:
        raw_out = response.get('message', {}).get('content',
                                                  'No output received') if 'response' in locals() else 'Request failed'
        trace["agent_1_graph"] = {"error": str(e), "raw_output": raw_out}
        trace["final_graph"] = {"error": f"Agent 1 Failure: {str(e)}"}
        trace["validator_errors"] = ["Agent 1 JSON Parse Crash - Aborting"]
        return trace

    # ---------------------------------------------------------
    # THE GATE: Run Validator
    # ---------------------------------------------------------
    errors = validator_func(pred_graph, truth_dict, text_chunk)
    trace["validator_errors"] = errors

    if not errors:
        trace["final_graph"] = pred_graph  # Perfect extraction on first try
        return trace

    # ---------------------------------------------------------
    # AGENT 2: The Grounding Refiner & Human Router
    # ---------------------------------------------------------
    error_log = "\n".join(errors)
    refiner_prompt = (
        "VALIDATION FAILED. Your previous extraction was caught by the structural validator.\n"
        f"ERRORS:\n{error_log}\n\n"
        "MANDATORY CORRECTION INSTRUCTIONS:\n"
        "1. If a required field cannot be found verbatim in the text, DO NOT GUESS OR INVENT IT.\n"
        "2. Set that field to `null` (or `[]` for lists).\n"
        "3. YOU MUST ADD AN ENTRY TO THE 'human_questions' ARRAY. The entry must have 'missing_entity' set to the name of the missing field and 'question_for_human' set to a direct question asking the user for it. If you fail to populate 'human_questions', validation will fail again."
    )

    messages.append({"role": "assistant", "content": clean_text})
    messages.append({"role": "user", "content": refiner_prompt})

    try:
        # APPLIED FIX: temperature=0.1 and num_ctx=8192 here as well
        final_response = ollama.chat(model=TARGET_MODEL, messages=messages,
                                     options={"temperature": 0.0, "num_predict": 1024, "num_ctx": 8192})

        raw_text_2 = final_response['message']['content'].strip()
        match_2 = re.search(r'\{.*\}', raw_text_2, re.DOTALL)
        clean_text_2 = match_2.group(0) if match_2 else raw_text_2

        final_graph = json.loads(clean_text_2)
        trace["agent_2_graph"] = final_graph
        trace["final_graph"] = final_graph
        return trace
    except Exception as e:
        raw_out_2 = final_response.get('message', {}).get('content', '') if 'final_response' in locals() else ''
        trace["agent_2_graph"] = {"error": str(e), "raw_output": raw_out_2}
        trace["final_graph"] = pred_graph  # Fallback to Agent 1 graph on failure
        return trace