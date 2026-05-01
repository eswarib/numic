# numic: Decision Support System for Post-Haemorrhagic Ventricular Dilatation (PHVD)

## Overview
**numic** is a clinical decision support tool designed for monitoring and risk assessment of **Post-Haemorrhagic Ventricular Dilatation (PHVD)** following intraventricular haemorrhage in preterm infants (<30 weeks gestation).

The system integrates cranial ultrasound (cUS) imaging data, temporal progression of ventricular measurements, and clinical inputs to support early intervention decisions in neonatal intensive care.

This project focuses on combining **medical imaging, time-series modelling, and machine learning** into a structured framework for neonatal brain monitoring.

---

## Clinical Motivation
Post-haemorrhagic ventricular dilatation (PHVD) is a serious complication following **intraventricular haemorrhage (IVH)** in preterm infants.

Clinical challenges include:
- Monitoring ventricular enlargement over time
- Determining when intervention is required
- Integrating imaging findings with clinical symptoms

Current workflows rely on:
- Manual measurements
- Intermittent assessment
- Subjective interpretation

**numic** aims to provide a consistent, data-driven framework for tracking disease progression and supporting clinical decisions.

---

## Key Features

### 🧠 Flexible Measurement Input
Supports two modes:

**1. Automated Extraction**
- Detects and measures:
  - Ventricular Index (VI)
  - Anterior Horn Width (AHW)
- Applied to cranial ultrasound images or video streams

**2. Pre-annotated Clinical Input**
- Accepts measurements from PACS systems
- Integrates directly with clinician workflows
- Avoids redundant computation when expert annotations are available

---

### ⏱️ Temporal Progression Modelling
- Tracks ventricular measurements over time
- Enables longitudinal analysis of PHVD progression
- Supports trend-based clinical assessment

---

### 📊 Risk Scoring Framework
- Combines:
  - Imaging-derived measurements (VI, AHW)
  - Temporal progression patterns
  - Clinical symptoms and observations
- Outputs a structured **risk score for PHVD progression**

---

### 👩‍⚕️ Clinical Decision Support
- Designed as a **support tool**, not a replacement for clinicians
- Enables:
  - earlier identification of high-risk cases
  - more consistent monitoring
  - integration of multimodal data

---

## Technical Approach

### Pipeline Overview

1. **Data Input**
   - Cranial ultrasound (cUS) imaging data
   - PACS-derived measurements (optional)
   - Clinical metadata

2. **Feature Input / Extraction**
   - Either:
     - Automated extraction of VI and AHW  
     - OR ingestion of pre-annotated measurements  

3. **Temporal Modelling**
   - Tracking changes across timepoints
   - Time-series representation of ventricular progression

4. **Risk Modelling**
   - Integration of imaging + clinical features
   - Computation of PHVD risk score

---

## Tech Stack
- Python
- NumPy / Pandas
- OpenCV
- (Add: PyTorch / TensorFlow if used)

---

## Research Relevance
This project relates to:
- Computational analysis of brain imaging  
- Time-series modelling in neurological conditions  
- AI for neonatal brain monitoring  
- Clinical decision support systems  

---

## Potential Extensions
- Deep learning-based segmentation of ventricular structures  
- Predictive modelling for intervention timing  
- Integration with electronic health records  
- Validation on longitudinal neonatal datasets  

---

## Status
Work in progress – ongoing development of modelling and integration pipeline.

---

## Author
Eswari Mathialagan  
MSc Physics & Engineering, UCL  
Software Developer  

GitHub: https://github.com/eswarib
