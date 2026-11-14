import json
import time
import random  # --- NEW IMPORT ---
from validator import run_validation_gates
from agent import extract_and_refine


def main():
    print("Loading dataset...")
    # Load Truth
    truth_records = {}
    with open("truth.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            truth_records[data["block_id"]] = data["ground_truth"]

    # Load Text
    with open("requirements.txt", "r", encoding="utf-8") as f:
        blocks = f.read().split("--- BLOCK ")

    total, perfect_first_try, routed_to_human, hallucinations_suppressed = 0, 0, 0, 0

    ontology_tracker = {
        "product": {"present": 0, "missing": 0}, "persona": {"present": 0, "missing": 0},
        "operating_context": {"present": 0, "missing": 0}, "stakeholder": {"present": 0, "missing": 0},
        "journeys": {"present": 0, "missing": 0}, "journey_steps": {"present": 0, "missing": 0},
        "needs": {"present": 0, "missing": 0}, "requirements": {"present": 0, "missing": 0}
    }

    # MATRIX COVERAGE TRACKERS
    unique_personas = set()
    unique_contexts = set()
    populated_intersections = set()

    # =========================================================================
    # --- NEW: OUTCOMES TRACKING VARIABLES ---
    # =========================================================================
    fabrication_opportunities = 0
    fabrication_attempts = 0
    total_final_errors = 0
    all_generated_questions = []
    all_extracted_nodes = []
    POISON_PILL_PERSONA = "Night Watchman"  # The canary persona from dataset.py
    # =========================================================================

    print("Executing Multi-Agent Validation Pipeline (TEST MODE: 5 BLOCKS)...")
    print("=" * 80)

    with open("pipeline_results.jsonl", "w", encoding="utf-8") as out_f, \
            open("agent_questions_log.txt", "w", encoding="utf-8") as q_f, \
            open("lifecycle_trace.txt", "w", encoding="utf-8") as trace_f:

        q_f.write("=== AGENT HUMAN CLARIFICATION LOG ===\n\n")

        for block_str in blocks:
            if not block_str.strip(): continue

            lines = block_str.split("\n", 1)
            block_id = int(lines[0].split(" ---")[0])
            text_chunk = lines[1].strip()

            if block_id not in truth_records: continue
            truth_dict = truth_records[block_id]
            total += 1

            start_time = time.time()

            trace = extract_and_refine(text_chunk, truth_dict, run_validation_gates)
            final_graph = trace.get("final_graph", {})

            final_errors = run_validation_gates(final_graph, truth_dict,
                                                text_chunk) if "error" not in final_graph else ["Crash"]
            human_qs = final_graph.get("human_questions", []) if isinstance(final_graph, dict) else []
            latency = round(time.time() - start_time, 2)

            # =========================================================================
            # --- NEW: COLLECT OUTCOMES METRICS ---
            # =========================================================================
            a1_graph = trace.get("agent_1_graph") or {}

            # Metric 1: Fabrication Tracking
            for field in ["product", "persona", "operating_context", "stakeholder"]:
                if not truth_dict.get(field):  # Truth is null
                    fabrication_opportunities += 1
                    if a1_graph.get(field):  # Agent 1 invented something anyway
                        fabrication_attempts += 1

            # Metric 5: Edit Distance (Proxy)
            total_final_errors += len(final_errors)

            # Metric 3: Question Quality Collection
            for q in human_qs:
                all_generated_questions.append(
                    f"[Block {block_id} - {q.get('missing_entity')}]: {q.get('question_for_human')}")

            # Metric 2: Grounding Fidelity Collection
            for field, val in final_graph.items():
                if field == "human_questions" or not val: continue
                if isinstance(val, dict):
                    all_extracted_nodes.append(
                        f"[Block {block_id} | {field}]: {val.get('value')}\n   Citation: \"{val.get('source_quote')}\"")
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            all_extracted_nodes.append(
                                f"[Block {block_id} | {field}]: {item.get('value')}\n   Citation: \"{item.get('source_quote')}\"")
                        else:
                            # SURVIVAL MECHANISM: If a weaker model outputs a string instead of a dict
                            all_extracted_nodes.append(
                                f"[Block {block_id} | {field}]: {item}\n   Citation: \"[FORMAT ERROR: Model dropped citation]\"")
            # =========================================================================

            if not final_errors and not human_qs:
                status = "[CLEAN]"
                perfect_first_try += 1
            elif human_qs:
                status = "[HUMAN INTERVENTION]"
                routed_to_human += 1
                hallucinations_suppressed += len(human_qs)

                q_f.write(f"--- BLOCK {block_id} ---\n")
                for q in human_qs:
                    q_f.write(f"[Entity: {q.get('missing_entity', 'Unknown')}]\n{q.get('question_for_human', '')}\n")
                q_f.write("\n")
            else:
                status = "[PERSISTENT FAILURE]"

            print(f"Block {block_id}: {status} Evaluated in {latency}s")

            # Write Lifecycle Trace
            trace_f.write(f"============================================================\n")
            trace_f.write(f"BLOCK ID: {block_id} | FINAL STATUS: {status}\n")
            trace_f.write(f"============================================================\n\n")
            trace_f.write("[RAW TEXT BLOCK]\n")
            trace_f.write(f"{text_chunk}\n\n")
            trace_f.write("[EXPECTED TRUTH (from truth.jsonl)]\n")
            trace_f.write(f"{json.dumps(truth_dict, indent=2)}\n\n")
            trace_f.write("--- AGENT STEP 1: INITIAL EXTRACTION ---\n")
            trace_f.write(
                f"[AGENT 1 STATUS]: {'CRASHED' if 'error' in (trace['agent_1_graph'] or {}) else 'SUCCESSFULLY EXTRACTED'}\n")
            trace_f.write("[AGENT 1 OUTPUT]:\n")
            trace_f.write(f"{json.dumps(trace['agent_1_graph'], indent=2)}\n\n")

            trace_f.write("[VALIDATOR STATUS]\n")
            if not trace["validator_errors"]:
                trace_f.write("PASS: No Errors Found. Bypassing Agent 2.\n\n")
            else:
                trace_f.write("FAIL: Errors Triggered Retry.\n")
                for err in trace["validator_errors"]:
                    trace_f.write(f" - {err}\n")
                trace_f.write("\n")
                trace_f.write("--- AGENT STEP 2: REFINEMENT & ESCAPE VALVE ---\n")
                trace_f.write(
                    f"[AGENT 2 STATUS]: {'CRASHED' if 'error' in (trace['agent_2_graph'] or {}) else 'EXECUTED'}\n")
                trace_f.write("[SUBSEQUENT ANSWER (AGENT 2 OUTPUT)]:\n")
                trace_f.write(f"{json.dumps(trace['agent_2_graph'], indent=2)}\n\n")
                trace_f.write("[HUMAN QUESTIONS GENERATED]:\n")
                if human_qs:
                    for q in human_qs:
                        trace_f.write(f" - {q.get('missing_entity')}: {q.get('question_for_human')}\n")
                else:
                    trace_f.write(" - None generated.\n")
                trace_f.write("\n")

            # Tracking coverage for clean graphs
            if not final_errors:
                for field in ontology_tracker.keys():
                    val = final_graph.get(field)
                    if val:
                        ontology_tracker[field]["present"] += 1
                    else:
                        ontology_tracker[field]["missing"] += 1

                # INTERSECTION MATRIX LOGIC
                p_node = final_graph.get("persona")
                c_node = final_graph.get("operating_context")

                p_val = p_node.get("value") if isinstance(p_node, dict) else None
                c_val = c_node.get("value") if isinstance(c_node, dict) else None

                if p_val: unique_personas.add(p_val)
                if c_val: unique_contexts.add(c_val)
                if p_val and c_val:
                    populated_intersections.add((p_val, c_val))

            out_f.write(json.dumps({"block_id": block_id, "final_graph": final_graph}) + "\n")

            # --- THE 5-BLOCK LIMIT BREAKER ---
            if total == 10:
                print("\n[!] 5 Blocks processed. Stopping early for test review.")
                break

    # =========================================================================
    # --- NEW: GENERATE THE OUTCOMES REPORT FILE ---
    # =========================================================================
    with open("INT450_Outcomes_Report.txt", "w", encoding="utf-8") as rep_f:
        rep_f.write("============================================================\n")
        rep_f.write(" INT450 FINAL OUTCOMES REPORT\n")
        rep_f.write("============================================================\n\n")
        # Metric 1: Fabrication Rate
        rep_f.write("1. FABRICATION RATE UNDER GATE PRESSURE\n")
        rep_f.write("-" * 60 + "\n")
        rep_f.write(f"Null Entities Encountered (Opportunities to invent) : {fabrication_opportunities}\n")
        rep_f.write(f"Times Agent 1 Attempted to Invent Data            : {fabrication_attempts}\n")
        fab_rate = round((fabrication_attempts / fabrication_opportunities) * 100,
                         1) if fabrication_opportunities > 0 else 0
        rep_f.write(f"Headline Fabrication Rate                         : {fab_rate}%\n")
        rep_f.write(f"Times Hallucination was successfully Suppressed   : {hallucinations_suppressed}\n\n")

        # Metric 4: Gap Detection
        rep_f.write("2. GAP DETECTION (SILENT OMISSION)\n")
        rep_f.write("-" * 60 + "\n")
        gap_status = "DETECTED & MODELLED" if any(
            POISON_PILL_PERSONA.lower() in p.lower() for p in unique_personas) else "MISSED (SILENT OMISSION)"
        rep_f.write(f"Target Seed Persona: '{POISON_PILL_PERSONA}'\n")
        rep_f.write(f"Pipeline Result    : {gap_status}\n\n")

        # Metric 5: Expert Edit Distance
        rep_f.write("3. EXPERT EDIT DISTANCE\n")
        rep_f.write("-" * 60 + "\n")
        rep_f.write(f"Total Persistent Graph Errors Remaining: {total_final_errors}\n")
        rep_f.write(
            "(This is the absolute number of nodes an expert reviewer must manually fix. A score of 0 indicates the pipeline successfully routed all uncertainties to the human question queue.)\n\n")

        # Metric 2: Grounding Fidelity (Worksheet)
        rep_f.write("4. GROUNDING FIDELITY (50-NODE HUMAN AUDIT WORKSHEET)\n")
        rep_f.write("-" * 60 + "\n")
        rep_f.write("Instructions: Mark [1] if citation genuinely supports the node, [0] if it does not.\n\n")
        sample_nodes = random.sample(all_extracted_nodes, min(len(all_extracted_nodes), 50))
        for i, node in enumerate(sample_nodes, 1):
            rep_f.write(f"___ {i}. {node}\n\n")

        # Metric 3: Question Quality (Worksheet)
        rep_f.write("5. QUESTION QUALITY (20-QUESTION HUMAN AUDIT WORKSHEET)\n")
        rep_f.write("-" * 60 + "\n")
        rep_f.write("Instructions: Mark [1] if answerable in a single sentence by a domain expert, [0] if not.\n\n")
        sample_qs = random.sample(all_generated_questions, min(len(all_generated_questions), 20))
        if not sample_qs:
            rep_f.write("No questions generated during this run.\n")
        for i, q in enumerate(sample_qs, 1):
            rep_f.write(f"___ {i}. {q}\n")
    # =========================================================================

    # FINAL REPORT PRINTING
    print("=" * 80)
    print(" PIPELINE METRICS - HALLUCINATION SUPPRESSION REPORT")
    print("=" * 80)
    print(f"Total Blocks Processed        : {total}")
    print(f"Clean Extractions (No Gate)   : {perfect_first_try}")
    print(f"Routed to Human (Safe Reject) : {routed_to_human}")
    print(f"Total Hallucinations Blocked  : {hallucinations_suppressed}")

    print("\n" + "=" * 80)
    print(" ONTOLOGICAL COVERAGE SUMMARY")
    print("=" * 80)
    for field, stats in ontology_tracker.items():
        tot = stats["present"] + stats["missing"]
        rate = round((stats["present"] / tot) * 100, 1) if tot > 0 else 0.0
        print(f"{field.ljust(20)}: {stats['present']} Present | {stats['missing']} Missing ({rate}% Coverage)")

    # ACCEPTANCE CRITERIA MATRIX (2D GRID)
    print("\n" + "=" * 80)
    print(" PERSONA × OPERATING-CONTEXT COVERAGE MATRIX REPORT")
    print("=" * 80)
    if not unique_personas or not unique_contexts:
        print("Not enough data to map cross-intersections.")
    else:
        p_list = sorted(list(unique_personas))
        c_list = sorted(list(unique_contexts))

        col_0_width = max([len(p) for p in p_list] + [len("PERSONA \\ CONTEXT")]) + 2
        col_widths = [max(len(c), 12) + 2 for c in c_list]

        header = "PERSONA \\ CONTEXT".ljust(col_0_width) + "|"
        for i, c in enumerate(c_list):
            header += c.center(col_widths[i]) + "|"
        print(header)

        sep_line = "-" * col_0_width + "+" + "+".join(["-" * w for w in col_widths]) + "+"
        print(sep_line)

        for p in p_list:
            row_str = p.ljust(col_0_width) + "|"
            for i, c in enumerate(c_list):
                if (p, c) in populated_intersections:
                    row_str += "[POPULATED]".center(col_widths[i]) + "|"
                else:
                    row_str += "[EMPTY]".center(col_widths[i]) + "|"
            print(row_str)
            print(sep_line)
    print("=" * 80)
    print("Detailed outcomes successfully saved to: INT450_Outcomes_Report.txt")


if __name__ == "__main__":
    main()