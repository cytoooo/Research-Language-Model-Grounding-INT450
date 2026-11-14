import random
import time
import json
def generate_dataset(text_filename="requirements.txt",truth_filename="truth.jsonl"):
    # Products (10 possible products in total)
    products = [
        "Unified Operations Platform", "Distributed Telemetry Mesh", "Enterprise Resource Oracle",
        "Logistics Command Center", "Edge Intelligence Gateway", "Cloud Native Data Lakehouse",
        "Zero-Trust Identity Vault", "Algorithmic Fraud Engine", "Automated Billing Orchestrator", "IoT Fleet Manager"
    ]
    # Personas (225 possible personas in total)
    persona_prefixes = ["Lead", "Senior", "Field", "Remote", "Tactical", "Compliance", "Junior", "Principal", "Chief",
                        "Interim", "Contract", "Staff", "Associate", "Global", "Regional"]
    persona_bases = ["Inspector", "Analyst", "Coordinator", "Auditor", "Technician", "Engineer", "Architect", "Manager",
                     "Director", "Specialist", "Consultant", "Operator", "Administrator", "Developer", "Scientist"]

    # Operating Contexts (225 possible operating contexts in total)
    context_environments = [
        "low-connectivity zones", "high-stress real-time environments", "air-gapped secure facilities",
        "asynchronous global timezones", "offshore drilling platforms", "underground transit networks",
        "sterile laboratory cleanrooms", "high-frequency trading floors", "disaster recovery sites",
        "remote satellite uplinks", "public cellular networks", "hostile electronic warfare zones",
        "automated robotic warehouses", "crowded urban centers", "deep-space communication relays"
    ]
    context_conditions = [
        "during peak load", "while operating offline", "under strict SLA deadlines", "with fragmented legacy data",
        "experiencing severe packet loss", "under active cyber attack", "during a hardware brownout",
        "with active active failover enabled", "while running on backup battery", "during an active compliance audit",
        "with restricted read-only permissions", "while onboarding new personnel",
        "during end-of-quarter reconciliation",
        "with corrupted cache memory", "during a zero-day vulnerability patch"
    ]

    # Journeys (10 possible journeys in total)
    journeys = [
        "Daily Equipment Audit", "Incident Triage", "Regulatory Compliance", "Asset Deployment",
        "Security Breach Response", "Data Lake Ingestion", "User Access Provisioning",
        "System Firmware Upgrade", "Financial Reconciliation", "Network Topology Discovery"
    ]

    # Journey Steps (list of steps for each journey)
    journey_steps_map = {
        "Daily Equipment Audit": ["Initiate diagnostic scan", "Log offline condition report",
                                  "Validate cryptographic checksums", "Sync report to master server"],
        "Incident Triage": ["Capture anomaly telemetry", "Assign severity triage tag", "Quarantine affected subnets",
                            "Broadcast alert to stakeholders"],
        "Regulatory Compliance": ["Pull historical logs", "Verify digital signatures", "Redact PII fields",
                                  "Generate compliance certificate", "Archive to cold storage"],
        "Asset Deployment": ["Provision digital twin", "Calibrate baseline metrics", "Handshake with edge gateway",
                             "Transition to active state"],
        "Security Breach Response": ["Identify intrusion vector", "Revoke compromised tokens",
                                     "Isolate network segment", "Deploy forensic logging agent"],
        "Data Lake Ingestion": ["Extract raw telemetry", "Normalize schema schemas", "Hash sensitive attributes",
                                "Load to columnar storage"],
        "User Access Provisioning": ["Verify identity claim", "Assign RBAC policies", "Generate ephemeral keys",
                                     "Log provisioning event"],
        "System Firmware Upgrade": ["Download signed binary", "Verify SHA-256 hash", "Flash primary partition",
                                    "Reboot and run diagnostics"],
        "Financial Reconciliation": ["Aggregate daily transactions", "Flag anomalous ledger entries",
                                     "Balance cross-border currencies", "Commit to immutable ledger"],
        "Network Topology Discovery": ["Ping local subnets", "Map open TCP ports", "Resolve DNS hostnames",
                                       "Generate graph visualization"]
    }

    # Needs (20 possible needs in total)
    needs = [
        "automated data synchronization", "offline-first operational capabilities", "predictive anomaly detection",
        "end-to-end cryptographic audit trails", "semantic search capabilities", "real-time geospatial tracking",
        "granular role-based access control (RBAC)", "dynamic load balancing", "sub-millisecond latency messaging",
        "idempotent transaction processing", "immutable event sourcing", "federated identity resolution",
        "multi-region active-active replication", "heuristic malware detection", "automated failover routing",
        "biometric session validation", "ephemeral secret rotation", "deterministic state recovery",
        "asynchronous webhook delivery", "distributed tracing visibility"
    ]

    # Requirements (30 possible requirements in total)
    requirements = [
        "Local SQLite database", "Kafka message broker", "RBAC microservice", "AES-256 encrypted tunnel",
        "GraphQL batch endpoint", "gRPC bi-directional streaming", "InfluxDB time-series database",
        "Jaeger distributed tracing", "Redis memory cache", "PostgreSQL relational database",
        "Elasticsearch indexer", "RabbitMQ queue", "Prometheus metrics scraper", "Kubernetes orchestration",
        "Docker containerization", "OAuth2 authorization server", "SAML SSO integration",
        "HashiCorp Vault secret manager", "Terraform infrastructure as code", "AWS S3 object storage",
        "Cloudflare WAF", "Nginx reverse proxy", "MongoDB document store", "Cassandra wide-column store",
        "Apache Spark processing engine", "Snowflake data warehouse", "Datadog APM monitor",
        "Twilio SMS gateway", "Stripe payment API", "SendGrid email SMTP"
    ]

    #noise induction
    false_requirements = [
        "legacy SOAP XML API", "on-premise Microsoft Access DB", "unencrypted FTP server",
        "jQuery frontend UI", "blockchain smart contracts", "Flash media player",
        "Windows 95 compatibility mode", "physical punch cards", "unhashed plaintext passwords",
        "monolithic PHP backend", "manual Excel spreadsheet routing", "consumer-grade Wi-Fi routers",
        "unlicensed pirated software", "deprecated AngularJS framework", "paper-based audit trails"
    ]

    discussions = [
        "The VP of Marketing demanded we build this using {distractor}, but engineering vetoed it.",
        "Sales promised the client a {distractor}, but we are absolutely not doing that.",
        "I heard a rumor we are switching to {distractor} to save money. Ignore that, it's a security nightmare.",
        "The CEO wants a flashy {distractor}, but this is a backend ticket. Disregard.",
        "A junior developer tried to implement {distractor} last sprint and broke the build. Never again.",
        "Legal asked if we could rely on {distractor}. The architecture board formally rejected the proposal.",
        "Client services opened a Jira ticket requesting {distractor}. I have closed it as 'Won't Do'."
    ]

    complaints = [
        "The Database Administrators are currently locked out of the production cluster due to a VPN failure.",
        "Site Reliability Engineers are fighting a massive memory leak in the European data center right now.",
        "The Legal Team mandated a freeze on the AWS staging environment until the compliance audit finishes.",
        "QA Testers corrupted the offline sandbox server, so development velocity will be zero until tomorrow.",
        "Third-party contractors accidentally disconnected the legacy backup mainframe in the basement.",
        "The pipeline is down because Junior SysAdmins crashed the cloud computing instance this morning.",
        "Compliance Officers are currently auditing the high-latency satellite network, so expect massive delays.",
        "Outsourced support staff cannot access the on-premise legacy servers due to a temporary firewall bug.",
        "Cloud Architects are migrating the disaster recovery site today, making the whole network highly unstable.",
        "The Information Security Team flagged the edge computing nodes for critical vulnerabilities overnight."
    ]
    POISON_PILL_BLOCK = 150
    POISON_PILL_PERSONA = "Night Watchman"
    POISON_PILL_CONTEXT = "abandoned basement server room"
    def build_ground_truth(current_block_id): # <-- FIXED: Added parameter
        truth = {}
        # 1. Product (80% chance)
        if random.random() > 0.2:
            truth["product"] = random.choice(products)
        else:
            truth["product"] = None

        # --- GAP DETECTION INJECTION ---
        if current_block_id == POISON_PILL_BLOCK:
            truth["persona"] = POISON_PILL_PERSONA
            truth["operating_context"] = POISON_PILL_CONTEXT
            truth["stakeholder"] = f"{POISON_PILL_PERSONA} operating in {POISON_PILL_CONTEXT}"
        else:
            # 2. Persona (70% chance)
            if random.random() > 0.3:
                truth["persona"] = f"{random.choice(persona_prefixes)} {random.choice(persona_bases)}"
            else:
                truth["persona"] = None

            # 3. Operating Context (70% chance)  <-- FIXED: Indented inside the else block
            if random.random() > 0.3:
                truth["operating_context"] = f"{random.choice(context_environments)} {random.choice(context_conditions)}"
            else:
                truth["operating_context"] = None

            # 4. Stakeholder (Derived from Persona + Context) <-- FIXED: Indented inside the else block
            if truth["persona"] and truth["operating_context"]:
                truth["stakeholder"] = f"{truth['persona']} operating in {truth['operating_context']}"
            else:
                truth["stakeholder"] = None

        # 5 & 6 Journeys and Journey Steps (60% chance)
        if random.random() > 0.4:
            selected_journeys = random.sample(journeys, k=random.randint(1, 2))
            truth["journeys"] = selected_journeys
            steps = []
            for j in selected_journeys:
                steps.extend(journey_steps_map[j])
            truth["journey_steps"] = steps
        else:
            truth["journeys"] = []
            truth["journey_steps"] = []

        # 7. Needs (80% chance)
        if random.random() > 0.2:
            truth["needs"] = random.sample(needs, k=random.randint(2, 4))
        else:
            truth["needs"] = []

        # 8. Requirements (90% chance)
        if random.random() > 0.1:
            truth["requirements"] = random.sample(requirements, k=random.randint(2, 5))
        else:
            truth["requirements"] = []

        return truth

    def generate_partial_text(truth, current_block_id):  # <-- FIXED: Added parameter
        text = ""
        # Product
        if truth["product"]:
            text += f"System architecture memo\nRegarding the development of the {truth['product']}.\n\n"
        else:
            text += f"General architecture memo\nRegarding the upcoming sprint deliverables.\n\n"

        noise_1 = random.choice(complaints)

        # --- FIXED: Added the Canary Injection Text ---
        if current_block_id == POISON_PILL_BLOCK:
            text += f"Just a quick side note before I forget, I had a brief chat with the {truth['stakeholder']}. Anyway, moving on to the main updates...\n"
            text += f"{noise_1}\n\n"

        # Standard Text Logic
        elif truth["stakeholder"]:  # <-- FIXED: Changed to elif
            # If we have the full Stakeholder, we write the complete sentence.
            text += f"User research update - \nwe finally got off a call with the {truth['stakeholder']}. "
            text += f"{noise_1}\n\n"
        elif truth["persona"]:
            # If we only have Persona, we mention them but explicitly state context is missing.
            text += f"This build is targeting the {truth['persona']}. We do not have data on their physical operating environment yet. "
            text += f"{noise_1}\n\n"
        elif truth["operating_context"]:
            # If we only have Context, we mention it but state the role is missing.
            text += f"This system operates {truth['operating_context']}. The specific user roles have not been finalized. "
            text += f"{noise_1}\n\n"

        # Needs
        if truth["needs"]:
            noise_2 = random.choice(false_requirements)
            text += f"Based on the latest data, the non-negotiable operational needs are: {', '.join(truth['needs'])}.\n"
            text += f"There was some debate about adding {noise_2}, but we are formally rejecting that idea.\n\n"

        # Journeys & Steps
        if truth["journeys"]:
            text += f"We mapped the following workflows: {', '.join(truth['journeys'])}. "
            text += f"The exact step-by-step chronological execution involves: {' -> '.join(truth['journey_steps'])}.\n\n"

        # Requirements
        if truth["requirements"]:
            template = random.choice(discussions)
            distractor = random.choice(false_requirements)
            noise_3 = template.format(distractor=distractor)
            text += f"{noise_3} Disregard previous emails. The engineering team has mandated the following technical components:\n"
            for req in truth["requirements"]:
                if truth["needs"]:
                    linked_need = random.choice(truth["needs"])
                    text += f"To satisfy the need for {linked_need}, we must implement {req}. "
                elif truth["journey_steps"]:
                    linked_step = random.choice(truth["journey_steps"])
                    text += f"To support the step '{linked_step}', engineering is deploying {req}. "
                else:
                    text += f"We are formally requiring the deployment of {req}. "

        return text

    start_time = time.time()
    word_count = 0
    block_id = 1
    target_blocks=500

    with open(text_filename, "w", encoding="utf-8") as f_text, open(truth_filename, "w", encoding="utf-8") as f_truth:
        while block_id <= target_blocks: # <-- Changed < to <= to get exactly 500 blocks
            truth_data = build_ground_truth(block_id) # <-- FIXED: Passed block_id
            text_block = generate_partial_text(truth_data, block_id) # <-- FIXED: Passed block_id
            combined_block = f"--- BLOCK {block_id} ---\n{text_block}\n\n\n"
            f_text.write(combined_block)
            f_truth.write(json.dumps({"block_id": block_id, "ground_truth": truth_data}) + "\n")
            word_count += len(combined_block.split())
            block_id += 1

    elapsed_time = time.time() - start_time
    print(f"Dataset Built: {word_count:,} words in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    generate_dataset()