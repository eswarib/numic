# NUMIC — Accelerator application brief



## 1. Business value proposition and model

**Problem**  
In preterm babies, **bleeding in or around the brain** sometimes occurs (**IVH**). **When the brain’s fluid-filled spaces enlarge beyond what teams expect** (**post‑haemorrhagic ventricular dilation, PHVD**), care depends on **how large those spaces are**, **how fast they change** on **repeat head ultrasounds**, and **how the baby is doing overall**. Teams **already build a risk picture** from the latest scan, earlier scans, and the bedside story—but **most of that work is done manually**: gathering the right measurements, **comparing them with the prior scan**, and **weighing that trend with the clinical picture** take **time and sustained attention** on a busy neonatal unit.

**Proposition**  
**NUMIC** is **decision support software**. It turns the **same inputs staff already use**—standard head‑ultrasound numbers (how wide key fluid spaces are), **change since the last scan**, plus a **short, structured note on clinical concern**—into a single **risk band** (low / moderate / high), using transparent rules we call **NumicFlow**. **The score and band are explainable:** the output shows **how each part contributed** (current size, change since the prior scan, clinical modifier) and **which rule version** was applied, so the reasoning stays **visible and repeatable**, not a black box.

**NUMIC does not choose treatment.** Staff use the band to **match local pathways** (how often to scan, when to escalate, when to involve neurosurgery, and so on). **The team and the hospital stay in charge of decisions.**

**Value**  
- A **shared, written risk level** that is **explainable**—**plain reasons** and a **per‑part breakdown**, so everyone means the same thing at handover.  
- A **clear record** of what drove the band (breakdown + rule version) for governance and learning.  
- A route to **fit into hospital workflows** over time (starting with measurements staff already record; any **smarter imaging step** would come later, with proper validation).

**Business model:** B2B SaaS—**annual licence** per **NHS trust or neonatal network**, with **optional pilot pricing** in year one and **separate setup / integration fees** where needed.

### Why this matters (clinical context—not a product proof)

Experts link **PHVD** to **patterns of brain injury** and **weaker long‑term development** in preterm infants. In practice, care leans heavily on **repeat head ultrasound**—both **the size of the fluid spaces** and **whether they are getting worse**—so teams can act **in good time** and along **consistent local pathways**.

Separately, **large national studies** show that children born **moderately or late preterm**—who make up **most preterm births**—can still face **higher long‑term neurodevelopmental risk** than full‑term peers. That is **background** on why neonatal brain care is a **public health scale** issue; it does **not** by itself prove anything about PHVD tools. **Supporting publications** at the end of this brief give optional reading.

**What NUMIC adds** is **less repetitive manual work**: staff do not have to **trace back through prior scans and dates** to **re‑check every measurement** against **agreed cut‑offs**—for example **high‑percentile lines (such as the 97th) or fixed millimetre limits**—before a consistent risk picture is clear. **The unit’s agreed protocol is written into versioned rules**; NumicFlow **applies that bundle** and returns an **explainable risk band** (sub‑scores and rule version visible)—**always** with normal **clinical judgment** still in charge.

---

## 2. Technology — plain‑English overview

NUMIC is **software** that takes **trusted ultrasound measurements** from head scans, **when each scan was done**, and a **short ward‑side note** on how worrying the overall picture is. It runs **clear, written rules** (“NumicFlow”) to produce a **risk band** (low / moderate / high). **That is the same judgment neonatologists already make** from “then vs now” on the scans and the baby’s course; NUMIC puts it **on the page, consistently**, labels **which version of the rules** was used, and shows **what drove the score**—so the result is **explainable**, not opaque.

**The software does not prescribe treatment**—it supports **local escalation and follow‑up practice**.

The design allows data to come in **manually today** and from **hospital systems later**. A **browser demo** shows how a band is produced; the **real product** is a proper clinical deployment with governance—not the demo on its own.

---

## 3. Technology — extra detail (optional for reviewers)

*Skip this section if you only need the business story; it is here for due diligence.*

- **Prototype build:** A small web service (Python / FastAPI) that accepts measurement records and returns **NumicFlow** scores and bands; **an** HTML/JS demo runs alongside for the same system.  
- **NumicFlow (logic):** One total score (**0–14**) from (i) **how big** key fluid‑space measures are on the current scan (**0–6**), (ii) **how much they have moved** since a **previous** scan (**0–6**), (iii) a **clinical concern** slot (**0–2**). The **risk band** (low / moderate / high) comes from **versioned** cut‑points on that total. **Outputs stay explainable:** each layer’s points are surfaced with the total, not hidden. **No treatment text** is emitted—only the band and breakdown.  
- **Rule versions:** Rules are packaged under **named versions** (e.g. `numic_flow_v1`) so results stay tied to **a specific rule set** as guidance updates.  
- **Inputs today:** Typed entry, spreadsheet‑style import, or simple feeds of numbers; **automatic “draw on the image and measure”** is **future work** and needs validation before clinical use.  
- **Roadmap:** Proper clinician UI, data storage, **hospital imaging/workflow** links where needed; any **AI on images** only after **clinical validation**.  
- **Regulatory / governance (open, not final):** Device **classification and market routes** (for example UK and EU frameworks and whether NUMIC is **software as a medical device**, and in which class) are **still to be settled** with clinical and quality advisors. The same conversations need to pin down **intended use** (who it is for, what it may and may not claim), a **clinical validation** approach before use near patients, **risk management** (e.g. wrong inputs, wrong rule version, misunderstood band), **software lifecycle and cybersecurity** for a connected product, **data protection** if identifiable patient data are processed, and **usability** so teams read outputs consistently on busy wards.

*No confidential model weights, unpublished trial data, or undisclosed third‑party IP beyond what is described above.*

---

## 4. Brief summary of key team members

| Name | Role / expertise | Relevant background |
|------|------------------|---------------------|
| Eswari Mathialagan | Software development | Software developer; Master’s student at UCL |
| `[TBC]` | `[TBC]` | `[TBC]` |

*Add founders, clinical advisors, key technical leads. Optional: advisors listed separately.*

---

## 5. Investments and grants raised to date

**None to date** (bootstrapped).

---

## 6. Investment sources (non‑dilutive, angel/syndicate, VC, corporate venturer)

**None to date** — no equity or non‑dilutive funding has been accepted yet.

---

## 7. Pre‑ or post‑revenue

**Pre‑revenue** — no commercial or pilot revenue recorded to date.

---

## 8. Present location of company (or virtual)

**Virtual** — no fixed operating premises; team and work are location‑independent.

---

## 9. Interest in Discovery Park

Primary interest is **geographic proximity** and the **pathway to NHS and clinical advisers**—including design‑partner conversations, neonatology input, and regional health‑innovation networks that sit naturally around Discovery Park and the wider Kent / South East cluster. NUMIC is **neonatal decision support**; credible iteration depends on **trusted clinical voices** as much as engineering.

---

## 10. Benefits of Discovery Spark

NUMIC’s next stretch is **part clinical**, **part regulatory**—not only engineering. The benefits we are looking for from Spark are **practical rather than abstract**:

- **Regulatory introductions:** Access to people who understand **UK/EU health‑software regulation**, **software as a medical device**, and **proportionate** routes from prototype toward **responsible clinical use**—so **intended use**, classification, and evidence planning are informed early, not improvised alone.  
- **Clinical advisors (and design‑partner conversations):** Introductions to **neonatology, imaging, and NHS governance** perspectives who can **stress‑test** NumicFlow against real **ward workflow, handover, and local pathways**—**before** wider pilots or stronger claims.

Broader programme benefits (mentorship, ecosystem, credibility, facilities) still matter; the two bullets above are the **main gaps** we hope Spark helps fill.

## Elevator line (optional paste into forms)

> *NUMIC helps neonatal teams turn **repeat head ultrasound measurements** and bedside context into a **clear, explainable risk band** when **IVH is followed by PHVD**—so **next steps follow local protocol**, with every **driver of the score** visible, not hidden. It supports teamwork and record‑keeping; it **does not** replace clinical judgment.*

---

## Supporting publications (optional background)

Mitha A, et al. Neurological development in children born moderately or late preterm: national cohort study. *BMJ.* 2024;384:e075630. <https://doi.org/10.1136/bmj-2023-075630>

El‑Dib M, et al. Management of Post‑hemorrhagic Ventricular Dilatation in the Infant Born Preterm. *J Pediatr.* 2020;226:16‑27.e3. <https://doi.org/10.1016/j.jpeds.2020.07.079>

---

