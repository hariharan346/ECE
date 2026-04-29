# Project Reviewer's Guide: Adaptive Power Theft Detection

## 1. Project Overview
This project addresses the global issue of **Power Theft** (Non-Technical Losses) using a **Hybrid Edge-Cloud AI Architecture**. Unlike traditional systems that use simple thresholds, this system uses **Behavioral Analysis** and **Load Fingerprinting** to distinguish between authorized appliance usage and illegal line tapping.

---

## 2. Step-by-Step System Workflow
Explain this to show how the data flows from the sensor to the verdict:

1.  **Data Acquisition**: Arduino sends `Current` and `Spike` data every 500ms.
2.  **Edge AI Inference (Local)**: The Python script immediately checks the "signature" of the data against a known library (Fridge, AC, etc.).
3.  **Heuristic Triggering**: If a spike exceeds 1.5A or current stays high (>2.4A), an anomaly is triggered.
4.  **Cloud AI Audit**: The system sends the last 10 readings to Gemini for a "High-Level Audit."
5.  **Smart Fallback**: If the API is busy (429 Rate Limit), the system uses an internal engine to generate the verdict, ensuring the dashboard never goes blank.

---

## 3. Step-by-Step Scenario Explanation (Based on Demo Output)

### Scenario 1: Normal Load
*   **Data**: `Current: 1.50A | Spike: 0.00 | Status: OK`
*   **Logic**: Stable readings around the 1.5A baseline. No triggers.

### Scenario 2: Sudden Spike (Instant Theft)
*   **Data**: `Current: 4.20A | Spike: 2.70`
*   **Verdict**: `STATUS: THEFT`
*   **Explanation**: "The system detected an instantaneous jump of 2.7A. The **Edge AI** classified it as `GENERIC_LOAD` (meaning no appliance matched this signature), and the **Cloud AI** confirmed it as a line tap."

### Scenario 3: Steady Theft (Sustained Analysis)
*   **Data**: Spike 1.70 detected, followed by sustained 3.24A.
*   **Logic**: 
    1.  Initial Spike triggers the first alert.
    2.  Even after the spike value drops to 0.04, the system detects **SUSTAINED** current.
*   **Explanation**: "This shows our system's memory. Even if the thief stops making changes, the sustained high current triggers a second audit."

### Scenario 4: Irregular Fluctuation (Suspicious)
*   **Data**: `Current: 2.10A | Spike: 0.60`
*   **Verdict**: `STATUS: SUSPICIOUS`
*   **Explanation**: "The current is fluctuating above the 1.5A baseline but hasn't hit the 2.4A sustained theft threshold. The system flags this as **SUSPICIOUS** rather than theft, demonstrating its ability to handle 'gray area' behaviors."

### Scenario 5: Grid Noise (Temporary Spike)
*   **Data**: `Current: 3.00A | Spike: 1.50` but returns to `1.50A`.
*   **Result**: `Status: OK`
*   **Explanation**: "The system successfully filtered this out as noise because it didn't meet the 'Sustained' requirement (5 readings). This prevents unnecessary alerts."

### Scenario 6: Legitimate Load (AC Unit - Fingerprinting)
*   **Data**: `Current: 12.00A | Spike: 10.50`
*   **Edge Verdict**: `MATCHED_SIGNATURE: AC_UNIT`
*   **Explanation**: "**Crucial Step**: Although the current is very high (12A), the local AI recognized the AC Startup Signature. This prevents the grid operator from wrongly accusing a customer who just turned on their AC."

### Scenario 7: Unauthorized High Power Device
*   **Data**: `Current: 20.00A | Spike: 18.50`
*   **Edge Verdict**: `UNKNOWN_HIGH_POWER_SIGNATURE`
*   **Explanation**: "Because 20A is outside the range of any registered household appliance in our library, the system flags it as a potential commercial-scale theft."

---

## 4. Key "Viva" Questions & Answers
*   **Q: Why use Edge AI and Cloud AI together?**
    - **A**: Edge AI gives **Instant response** (Load fingerprinting), while Cloud AI gives **Deep Reasoning** (Auditing the history).
*   **Q: How does the system handle internet failure?**
    - **A**: I implemented an **Internal Audit Fallback**. If the API fails, the system uses local heuristics to generate the report so the dashboard remains functional.
*   **Q: What is 'Sliding Window' history?**
    - **A**: It means the AI sees the **Context** (last 10 readings), not just one number. This allows it to see the "Story" of the theft.

---

## 5. Closing Summary
> "Our project demonstrates a scalable, intelligent solution for smart grids. It doesn't just detect high current; it understands the behavior of the electricity to catch real thieves while protecting innocent customers."
