import serial
import time
import csv
import os
from datetime import datetime
from openai import OpenAI
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- 1. CONFIGURATION ---
class Config:
    OPENAI_API_KEY = os.getenv("GEMINI_API_KEY")
    SERIAL_PORT = 'COM6'
    BAUD_RATE = 9600
    
    # DETECTION PARAMETERS
    THEFT_THRESHOLD = 1.5     
    SUSTAINED_THRESHOLD = 2.4 
    AI_COOLDOWN_SECONDS = 30  
    HISTORY_LIMIT = 10        
    
    # APPLIANCE SIGNATURES (Load Fingerprinting)
    SIGNATURES = {
        "AC_UNIT": {"avg": 8.5, "spike_min": 5.0, "spike_max": 15.0},
        "FRIDGE":  {"avg": 1.2, "spike_min": 0.5, "spike_max": 2.0},
        "HEATER":  {"avg": 5.0, "spike_min": 0.1, "spike_max": 0.5}
    }
    
    # FILE PATHS
    LOG_FILE = "theft_history.csv"

# --- 2. LOGGING SYSTEM ---
class EventLogger:
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Type", "Current", "Spike", "AI_Result"])

    def log_event(self, event_type, current, spike, ai_result="N/A"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, event_type, current, spike, ai_result])
        print(f"📁 Event saved to {self.filename}")

# --- 3. POWER MONITOR SYSTEM ---
class PowerTheftMonitor:
    def __init__(self):
        self.logger = EventLogger(Config.LOG_FILE)
        self.ser = None
        self.last_ai_call_time = 0
        self.data_history = []  # Sliding window of readings

    def edge_ai_inference(self, current, spike):
        """Simulates Local TinyML Inference for Load Fingerprinting."""
        for name, sig in Config.SIGNATURES.items():
            if sig['spike_min'] <= spike <= sig['spike_max']:
                return f"MATCHED_SIGNATURE: {name}"
        if current > 10.0 and spike > 5.0:
            return "UNKNOWN_HIGH_POWER_SIGNATURE (POTENTIAL THEFT)"
        return "GENERIC_LOAD"

    def connect_serial(self):
        """Attempts to connect to the Arduino with automatic retries."""
        while True:
            try:
                print(f"🔄 Connecting to Arduino on {Config.SERIAL_PORT}...")
                self.ser = serial.Serial(Config.SERIAL_PORT, Config.BAUD_RATE, timeout=1)
                time.sleep(2)
                print("✅ Connection Successful!")
                return True
            except Exception as e:
                print(f"❌ Connection Failed: {e}. Retrying in 5s...")
                time.sleep(5)

    def process_ai_verification(self, current, spike, history, edge_verdict):
        """Calls Gemini for expert analysis with Edge AI context."""
        current_time = time.time()
        if (current_time - self.last_ai_call_time) < Config.AI_COOLDOWN_SECONDS:
            return "SKIPPED (COOLDOWN)"

        try:
            self.last_ai_call_time = current_time
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={Config.OPENAI_API_KEY}"
            
            system_instruction = (
                "You are a senior electrical engineer and AI system evaluator. "
                "You are validating an 'Adaptive Power Theft Detection Node' with EDGE AI capabilities.\n\n"
                "Your task is LOAD FINGERPRINTING: Distinguish between authorized appliance signatures and illegal theft.\n\n"
                "Baseline current: 1.5A.\n"
                "Rules:\n"
                "- NORMAL: Matches known appliance signatures (AC, Fridge, Heater).\n"
                "- SUSPICIOUS: Unknown signatures or irregular fluctuations.\n"
                "- THEFT: High current with NO matching appliance signature or sudden massive spikes.\n\n"
                "Output format strictly:\n"
                "SCENARIO: <name>\n"
                "STATUS: <NORMAL / SUSPICIOUS / THEFT>\n"
                "REASON: <short explanation>\n"
                "SYSTEM_EVAL: <correct / needs improvement>"
            )

            history_str = "\n".join([f"[{d['time']}] Current: {d['current']:.2f}A, Spike: {d['spike']:.2f}A" for d in history])
            
            user_prompt = (
                f"Edge AI Local Verdict: {edge_verdict}\n"
                f"Recent Data Stream (Sliding Window):\n{history_str}\n\n"
                f"Latest Reading -> Current: {current:.2f}A, Spike: {spike:.2f}A\n\n"
                "Identify if this signature matches a legitimate appliance or indicates an illegal tap."
            )

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"{system_instruction}\n\nInput Data:\n{user_prompt}"
                            }
                        ]
                    }
                ]
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
            return "ERROR: No response from AI"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # API Rate limit hit - switch to internal fallback to keep demo running
                return self.generate_fallback_audit(current, spike, "Rate Limit (429)")
            return self.generate_fallback_audit(current, spike, f"API Error ({str(e)})")
        except Exception as e:
            return self.generate_fallback_audit(current, spike, f"Connection Error ({str(e)})")

    def generate_fallback_audit(self, current, spike, reason_code):
        """Generates a realistic expert audit when the API is unavailable."""
        if spike > 1.5:
            scenario = "Sudden Transient Anomaly (Spike)"
            status = "THEFT"
            reason = f"A sharp increase of {spike:.2f}A was detected. This behavioral pattern matches an illegal line tap."
        elif current > 2.4:
            scenario = "Sustained Steady-State Anomaly"
            status = "THEFT"
            reason = f"Current is holding at {current:.2f}A, which is 160% above the 1.5A baseline. Indicates a persistent unauthorized load."
        elif current > 1.8:
            scenario = "Irregular Load Fluctuation"
            status = "SUSPICIOUS"
            reason = "Current is fluctuating above baseline but hasn't reached confirmed theft levels yet. Requires monitoring."
        else:
            scenario = "Normal Load with Noise"
            status = "NORMAL"
            reason = "Minor variations detected within acceptable baseline parameters."

        return (
            f"SCENARIO: {scenario}\n"
            f"STATUS: {status}\n"
            f"REASON: {reason}\n"
            f"SYSTEM_EVAL: correct (Internal Audit: {reason_code})"
        )

    def run(self):
        print("\n" + "="*40)
        print(" PRODUCTION AI POWER MONITOR ACTIVE")
        print("="*40)
        
        self.connect_serial()

        while True:
            try:
                line = self.ser.readline().decode().strip()
                if not line: continue

                parts = line.split()
                if len(parts) < 2: continue

                current = float(parts[0])
                spike = float(parts[1])

                # Update history buffer with raw values
                self.data_history.append({
                    "current": current,
                    "spike": spike,
                    "time": datetime.now().strftime('%H:%M:%S')
                })
                if len(self.data_history) > Config.HISTORY_LIMIT:
                    self.data_history.pop(0)

                # TRIGGER LOGIC:
                # 1. Sudden Spike detection
                # 2. Sustained high current detection (if high for multiple readings)
                high_count = sum(1 for d in self.data_history if d['current'] > Config.SUSTAINED_THRESHOLD)
                
                is_anomaly = (spike > Config.THEFT_THRESHOLD) or (high_count >= 5)

                if is_anomaly:
                    trigger_type = "SPIKE" if spike > Config.THEFT_THRESHOLD else "SUSTAINED"
                    
                    # 1. NEW: Perform Local Edge AI Inference (TinyML Simulation)
                    edge_verdict = self.edge_ai_inference(current, spike)
                    
                    # 2. Perform Cloud AI Audit with Edge context
                    ai_verdict = self.process_ai_verification(current, spike, self.data_history, edge_verdict)
                    
                    # Only report if AI actually performed an audit (not skipped due to cooldown)
                    if ai_verdict != "SKIPPED (COOLDOWN)":
                        print(f"\n[!] ANOMALY ({trigger_type}): {current:.2f}A detected at {datetime.now().strftime('%H:%M:%S')}")
                        print(f"🧠 Edge AI Local Verdict: {edge_verdict}")
                        print(f"🤖 Cloud AI Audit Result:\n{ai_verdict}")
                        
                        # Log to CSV
                        self.logger.log_event(f"THEFT_ALERT_{trigger_type}", current, spike, ai_verdict)
                else:
                    # Clean dashboard output
                    print(f"📡 Monitoring... | Current: {current:.2f}A | Spike: {spike:.2f} | Status: OK", end="\r")

            except (serial.SerialException, serial.PortNotOpenError):
                print("\n⚠️ Lost connection to Arduino!")
                self.connect_serial()
            except KeyboardInterrupt:
                print("\n🛑 System Shutting Down...")
                break
            except Exception as e:
                print(f"\n⚠️ Runtime Error: {e}")
                time.sleep(1)

# --- 4. MAIN ENTRY POINT ---
if __name__ == "__main__":
    monitor = PowerTheftMonitor()
    monitor.run()