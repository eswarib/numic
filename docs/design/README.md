# NUMIC design documents

Standalone HTML design documents. Open them in a browser; no server needed.

| Document | Version | Contents |
|---|---|---|
| [NUMIC_overview_understanding.html](NUMIC_overview_understanding.html) | 3 (6 Oct 2026) | What NUMIC is, the PHVD clinical gap, NumicFlow scoring with an in-browser v1 calculator, what's built, status, the clinical demo and hosting options for numic.uk |
| [NUMIC_rule_sets_design.html](NUMIC_rule_sets_design.html) | 6 (5 Oct 2026) | Age-based rule sets `numic_flow_levene` and `numic_flow_brouwer`, inputs, files to change, impact, combining the layers (options A–D), configuration parameters, admin rule editor, clinician decision capture, learning loop, open decisions |
| [NUMIC_architecture.html](NUMIC_architecture.html) | 2 (6 Oct 2026) | Component map, principles, components, key flows, deployments, technology, build order, open architecture decisions |
| [requirements/index.html](requirements/index.html) | 2 (6 Oct 2026) | Requirements for each of the 18 components: scope, functional and non-functional requirements with acceptance criteria, dependencies, open questions |
| [NUMIC_clinical_demo.html](NUMIC_clinical_demo.html) | 1 (7 Oct 2026) | The clinical demo: what visitors can do, how it works, demo API, settings, PostgreSQL tables and lifecycle, Railway configuration, deployment steps, post-deploy checks, limitations, launch list |

Each document carries its own version line and change history. Version numbers match the published claude.ai pages:

- Overview: https://claude.ai/artifact/3yHErd6HMnFY68VGUBQp7p
- Rule sets: https://claude.ai/artifact/ArcGD8dEWsgxJAF39K7kNE
- Architecture: https://claude.ai/artifact/34JQXYcqMMMQ8mr4qJPCAa
- Requirements: https://claude.ai/artifact/EhgMAayQAgWQmsbXFrhcFm
- Clinical demo: https://claude.ai/artifact/QorqenaW8AE1JKbna1vLcy

Requirement IDs (`CODE-F01`, `CODE-N01`) are stable so tests, tickets and the clinical safety hazard log can refer to them.

These are design documents for discussion. They are not regulatory or clinical guidance.
