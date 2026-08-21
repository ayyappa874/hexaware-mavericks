# Survey Sentinel — Live Hackathon Pitch & Judge Click-Through Sequence

> **Positioning Statement**:  
> *"Honorable Judges, Survey Sentinel is an evidence-driven intelligence layer that complements CAPI/eSigma. We don't replace validation — we explain what static rules can't catch."*

---

## ⏱️ 3-Minute Live Presentation Flow

```
[0:00 - 0:35]  Act 1: Landing Pulse & Real-Time Stream Ingestion Demo (/demo)
[0:35 - 1:15]  Act 2: Hero Anomaly Investigation & Staggered Reveal (/record/[id])
[1:15 - 1:50]  Act 3: Counterfactual Explanations & Prescriptive Perturbations
[1:50 - 2:25]  Act 4: Active Learning Queue & Bayesian Weight Recalibration (/queue)
[2:25 - 3:00]  Act 5: Anomaly Clustering & MoSPI Temporal Round Drift (/clusters & /temporal)
```

---

## 🖱️ Step-by-Step Click Sequence for Judges

### 1. Act 1: Real-Time Stream Ingestion Demo (`http://localhost:3000/demo`)
- **Click**: Click the glowing red **`LIVE DEMO`** button in the top navbar.
- **Say**: *"Let's start by simulating real-time CAPI field unit microdata streaming into our platform. Notice as new records arrive every 2 seconds, our multi-detector pipeline computes peer cohort statistics and Isolation Forest scores in under 45ms."*
- **Action**: Click **Start Live Stream**. Point to the dynamic **Risk Gauge Meter** updating live as records arrive.

---

### 2. Act 2: Hero Anomaly Investigation (`http://localhost:3000/record/[id]`)
- **Click**: Click on any flagged record in the stream feed ticker.
- **Say**: *"Unlike black-box anomaly detectors, Survey Sentinel composes structured human-readable evidence narratives. Look at this progressive reveal animation: we explain WHY this record is anomalous across 5 distinct detectors."*
- **Point To**:
  1. **Radial Evidence Radar Graph**: Interactive SVG network displaying detector agreement.
  2. **Anomaly DNA Bar Chart**: Relative signal intensity for Distribution, Temporal, Enumerator, Cluster, and Rule detectors.
  3. **Narrative Evidence**: *"Salaried worker earnings ₹95,000 exceed State 07 Urban peer cohort standard (Z-Score = +3.85)."*

---

### 3. Act 3: Counterfactual Explanations ("What Needs to Change?")
- **Scroll**: Scroll down to the **Counterfactual What-If Panel**.
- **Say**: *"Instead of just flagging errors, we answer the supervisor's critical question: 'What needs to change for this record to be compliant?'"*
- **Point To**: Slide the interactive before/after card showing:
  - `Earnings_Last_Month: ₹95,000 → ₹28,500`
  - `Target Risk Score: 85.0% → 14.2% (NORMAL)`

---

### 4. Act 4: Active Learning Queue & Supervisor Feedback (`http://localhost:3000/queue`)
- **Click**: Navigate to **Investigation Queue** (`/queue`).
- **Say**: *"We provide supervisors with two specialized views: High Priority Flags for urgent review, and an Active Learning Queue sorted by uncertainty (|Risk - 50|). These boundary cases teach our Bayesian fusion model fastest."*
- **Click**: Click **Confirm Anomaly** on a boundary case. Show how supervisor decisions update fusion weights automatically in the database.

---

### 5. Act 5: Semantic Anomaly Clustering (`http://localhost:3000/clusters`)
- **Click**: Click **Semantic Clusters** in the left sidebar.
- **Say**: *"Instead of swamping supervisors with flat lists of thousands of errors, our clustering engine groups flags by shared root cause patterns — like FSU last-digit preference or regional wage anomalies."*
- **Point To**: Display cluster cards with record counts and aggregate risk scores.

---

### 6. Act 6: MoSPI Round-over-Round Temporal Drift (`http://localhost:3000/temporal`)
- **Click**: Click **Temporal Drift Monitor** in the left sidebar.
- **Say**: *"Finally, at the macro level, we compute official MoSPI Labour Force Participation Rate (LFPR), Worker Population Ratio (WPR), and Unemployment Rate (UR) indicators. We run statistical Z-tests round-over-round to flag structural shift anomalies."*
- **Point To**: Highlighting `SIGNIFICANT DRIFT (|Z| ≥ 2.0)` flags across states.

---

## 🏆 Closing Punchline for Judges

> *"Survey Sentinel combines rigorous PLFS validation rules, contextual peer cohort statistics, unsupervised ML, counterfactual explanations, and active supervisor learning — giving MoSPI total transparency from field unit CAPI microdata up to national indicators."*
