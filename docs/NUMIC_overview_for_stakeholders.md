# NUMIC — Overview for stakeholders  
### Clinical decision support for post‑haemorrhagic ventricular dilation (PHVD) risk

**Audience:** Clinical, regulatory, and quality leadership (e.g. medical device QMS)  
**Purpose:** Single-page summary of intent, design, and responsible next steps — not a regulatory submission.

---

## 1. Executive summary

**NUMIC** is a software concept for **structured assessment and communication of risk** in infants with **post‑haemorrhagic ventricular dilation (PHVD)** after intraventricular haemorrhage. It combines:

- **Standard cUS measurements** used in practice and trials (ventricular index, anterior horn width, thalamo‑occipital distance),
- **Explicit, versioned scoring rules** aligned with published thresholds and trial logic (e.g. ELVIS‑era framing),
- **Temporal (“progression”) information** — how fast ventricular size is changing between scans — which the literature highlights as prognostically important but often **not quantified in a single, actionable score**.

The goal is **decision support**: to make **size + trajectory + key clinical context** visible in one place, with **transparent sub‑scores** and **tiered suggested actions** (e.g. surveillance vs escalation), so neonatal teams can align discussion and documentation — **not** to replace clinical judgment or to make an autonomous diagnosis.

---

## 2. Clinical problem

PHVD after IVH is associated with important morbidity. Management depends on **how dilated the ventricles are**, **how quickly dilation progresses**, and **clinical evolution**. Teams already use serial cranial ultrasound (cUS) and published cut‑offs; however:

- Progression is often **described qualitatively** (“a bit bigger”) rather than **summarised in a consistent, auditable way**.
- There is **no single, widely adopted composite** that combines **absolute size**, **rate of change**, and **late clinical signs** for handover and quality review.

NUMIC is intended to **support** that gap: a **structured, reproducible summary** that still maps back to familiar metrics.

---

## 3. What we are building (product intent)

| Layer | Role |
|--------|------|
| **Measurement capture** | Accept VI, AHW, TOD (and related fields) from **PACS/overlay pipelines**, **image‑derived tools**, **manual/GUI entry**, or **bulk import** — with **patient identity**, **date/time of study**, **who measured**, and **clinical notes** where available. |
| **NumicFlow scoring** | **Static** score from current size vs thresholds; **progression** score from change vs a prior timepoint; **clinical modifier** from structured concern level (e.g. fontanel / systemic signs), with rules **versioned** (e.g. `numic_flow_v1`) so outputs remain interpretable when policies evolve. |
| **Risk tier** | Map total score to **low / moderate / high** bands with **plain‑language suggested actions** (aligned to published pathways — scan frequency, escalation, neurosurgical awareness). |
| **Presentation** | Eventually: **clinician‑facing UI** (not raw API JSON) — patient context, numbers, trajectory plot, score breakdown, rule version, and export for records. |

A **demo API** exists to show **end‑to‑end behaviour** for prototyping; the **clinical product** would be a regulated front‑end and deployment model, not the demo route alone.

---

## 4. Methodology (NumicFlow — high level)

**Static layer (0–6)**  
Per‑metric bands for VI (with percentile / nomogram logic as implemented), AHW, and TOD, consistent with the evidence base we are coding against.

**Progression layer (0–6)**  
Quantified change in VI, AHW, TOD between **current and prior** measurements over time (worsening‑direction logic as specified in our rule set).

**Clinical modifier (0–2)**  
Structured input for **late but important** clinical concern (none / mild / clear), from bedside observation or file — not a full neonatal exam replacement.

**Total**  
Weighted sum → **NumicFlow score (0–14)** → **risk tier** with **action bands**.

All thresholds live in **named, versioned rule bundles** so that governance can approve changes and old results remain attributable to a **specific rule version**.

---

## 5. Technical system (non‑technical summary)

- **Backend:** API‑first service (e.g. FastAPI) separating **measurement ingestion**, **scoring**, and (later) **persistence**.
- **Data model:** Patient/study context + measurements + optional progression and reports — designed for **audit** (who, when, which rule version).
- **Inputs:** Designed for **hospital reality**: DICOM/PACS metadata, spreadsheet import, manual entry from a measurement GUI, future ML‑based image extraction (currently stubbed where models are not yet integrated).

Engineering detail is available separately; this document focuses on **intent and governance**.

---

## 6. Quality, safety, and regulatory posture (discussion points)

The following are **topics for informed conversation with QMS / clinical governance**, not conclusions:

- **Intended use:** Decision support / workflow aid vs diagnostic device claims — must be nailed down with **intended user**, **indication**, and **contraindications** in a formal definition.
- **Clinical validation:** Agreement on **performance study design**, reference standard, and neonatology sign‑off before any deployment near patients.
- **Risk management:** ISO 14971‑style hazards (wrong input, wrong rule version, UI misread, missed escalation) and mitigations (human‑in‑the‑loop, versioning, logging).
- **Software lifecycle:** IEC 62304 class, configuration management, release records, and **SBOM** / cybersecurity expectations for a connected product.
- **Data protection:** UK GDPR / NHS DSPT‑style considerations if patient identifiers are processed.
- **Human factors:** UI testing so **risk tier** and **recommended actions** are unambiguous and match local protocol.

NUMIC is at an early stage: **architecture and rule structure exist in software**; **formal QMS alignment and clinical evidence** are deliberate next steps — which is why engagement with UCL quality leadership is valuable **before** scaling claims or deployment.

---

## 7. Current status vs roadmap

| Stage | Status (high level) |
|--------|---------------------|
| Scoring logic & versioning | Prototype implemented; requires **clinical validation** and **change control** under QMS if marketed. |
| Measurement ingestion | **Today (prototype):** manual entry, spreadsheet import, and numeric feeds from overlay/PACS-style metadata. **Roadmap:** deeper **PACS/workflow integration** where needed; **eventually, automatic VI/AHW/TOD from cUS images** using **segmentation models**, with **clinical validation** before use in care. |
| Clinician UI | **Roadmap:** develop a **clinician-facing UI** focused on **ease of use**—the production experience, not raw APIs or demo pages. **Input from clinicians** (neonatologists, sonographers, and related roles) will be **essential** for screen flow, terminology, and how risk tiers and suggested actions are presented; the API and demo remain for engineering and early testing. |
| Regulatory strategy | **Open** — depends on intended use, jurisdiction (UKCA / MDR), and whether the system is **Software as a Medical Device** and in which class. |

---

## 8. What we would value from this conversation

NUMIC’s next steps depend heavily on **how** we position the product under device law and **what** evidence and governance UCL or partner sites would expect. Your perspective—drawing on device QMS and clinical governance—would help me **prioritise** documentation, timelines, and who to engage next.

- **Reality check** on positioning NUMIC as **clinical decision support** under UK / EU device thinking.
- **Minimum viable QMS path** if we pursue **clinical pilots** or **UCL‑affiliated evaluation**.
- **Clinical evaluation & risk management — where to start:** How far must we go (plan vs evidence) before showing **risk categories** or **suggested actions** to clinicians outside a purely internal prototype? Which artefacts you’d expect early on (e.g. intended use wording, clinical benefits/risks narrative, usability/safety considerations, post-market thinking) and **what level of formality** is proportionate at pilot stage vs a full **Software as a Medical Device** path.
- **Institutional gate — what to line up first:** Your read on **UCL** (or typical NHS trust) expectations before **any** real patient data or clinician-facing use: e.g. **DPIA**, information governance, **research vs service / clinical evaluation** boundaries, and whether we should treat an evaluation as “research” with full ethics first, or a defined service improvement path. **Concrete ask:** what we should **secure in writing** and **in what order** so we do not block useful pilots or create avoidable compliance debt.

---

## 9. NUMIC - one-line overview

> *“A structured PHVD risk summary that combines serial cUS size, rate of change, and key clinical modifiers into a transparent, versioned score — intended as decision support for neonatal teams, with formal device and clinical pathways still to be defined with quality and clinical leads.”*

---

## References

1. El-Dib M, Limbrick DD Jr, Inder T, Whitelaw A, Kulkarni AV, Warf B, Volpe JJ, de Vries LS. Management of Post-hemorrhagic Ventricular Dilatation in the Infant Born Preterm. *J Pediatr.* 2020 Nov;226:16-27.e3. doi: [10.1016/j.jpeds.2020.07.079](https://doi.org/10.1016/j.jpeds.2020.07.079). Epub 2020 Jul 30. PMID: 32739263; PMCID: PMC8297821.

---

*Document generated for internal stakeholder sharing. It does not constitute regulatory advice, clinical guidance, or a commitment of performance.*
