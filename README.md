# Adaptive Power Theft Detection Node

A hybrid Edge-Cloud system for real-time power theft detection using behavioral analysis and load fingerprinting.

## Setup Instructions

1.  **Hardware**: Connect your Arduino to your PC via USB (Default: `COM6`).
2.  **Environment**: 
    - Create a `.env` file in the root directory.
    - Add your Gemini API Key: `GEMINI_API_KEY=your_key_here`
3.  **Install Dependencies**:
    ```powershell
    pip install pyserial requests python-dotenv
    ```
4.  **Run Production Monitor**:
    ```powershell
    python .\ai_detection.py
    ```
5.  **Run Demo Simulator**:
    ```powershell
    python .\demo_tester.py
    ```

## Project Logic
- **Edge AI**: Performs local load fingerprinting to identify legitimate appliances.
- **Cloud AI (Gemini)**: Performs expert audits on anomalies using historical data context.
- **Adaptive Detection**: Handles both transient spikes and sustained theft.
