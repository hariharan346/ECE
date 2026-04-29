import time
import requests
import json
from datetime import datetime
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

try:
    from ai_detection import Config, PowerTheftMonitor
except ImportError:
    print("Error: ai_detection.py not found in the current directory.")
    sys.exit(1)

def print_banner(text):
    print("\n" + "="*60)
    print(f" SCENARIO: {text}")
    print("="*60)

class DemoSimulator(PowerTheftMonitor):
    def __init__(self):
        super().__init__()
        self.last_ai_call_time = 0
        self.data_history = []

    def run_scenario(self, name, current_values):
        print_banner(name)
        # Reset state for clean demo
        self.data_history = []
        self.last_ai_call_time = 0 
        prev = 1.5
        
        for current in current_values:
            spike = abs(current - prev)
            
            # Update history
            self.data_history.append({
                "current": current,
                "spike": spike,
                "time": datetime.now().strftime('%H:%M:%S')
            })
            if len(self.data_history) > Config.HISTORY_LIMIT:
                self.data_history.pop(0)

            # Logic
            high_count = sum(1 for d in self.data_history if d['current'] > Config.SUSTAINED_THRESHOLD)
            is_anomaly = (spike > Config.THEFT_THRESHOLD) or (high_count >= 5)

            status = "ANOMALY DETECTED" if is_anomaly else "OK"
            print(f"Data: {current:.2f}A | Spike: {spike:.2f} | Status: {status}")

            if is_anomaly:
                trigger_type = "SPIKE" if spike > Config.THEFT_THRESHOLD else "SUSTAINED"
                print(f"  [!] Trigger Event: {trigger_type} detected.")
                
                # Check cooldown
                curr_time = time.time()
                if (curr_time - self.last_ai_call_time) < Config.AI_COOLDOWN_SECONDS:
                    print(f"  AI Audit Result: SKIPPED (Cooldown: {int(Config.AI_COOLDOWN_SECONDS - (curr_time-self.last_ai_call_time))}s left)\n")
                else:
                    print(f"  🧠 Calling Gemini AI for Expert Audit...")
                    # Perform real AI Audit
                    verdict = self.process_ai_verification(current, spike, self.data_history)
                    print(f"  🤖 AI Verdict:\n{verdict}\n")
                    self.last_ai_call_time = curr_time
            
            prev = current
            time.sleep(0.5) # Simulate Arduino speed

def main():
    sim = DemoSimulator()
    
    # Temporarily lower cooldown for demo purposes so user doesn't wait 60s
    Config.AI_COOLDOWN_SECONDS = 10 

    while True:
        print("\nSELECT SCENARIO TO DEMO:")
        print("1. Normal Load (Baseline)")
        print("2. Sudden Spike (Instant Theft)")
        print("3. Steady Theft (Sustained Load)")
        print("4. Irregular Fluctuation (Suspicious)")
        print("5. Noise (Temporary Spike)")
        print("Q. Quit")
        
        choice = input("\nEnter choice (1-5 or Q): ").upper()
        
        if choice == '1':
            sim.run_scenario("NORMAL LOAD", [1.5, 1.52, 1.48, 1.51, 1.50, 1.49])
        elif choice == '2':
            sim.run_scenario("SUDDEN SPIKE", [1.5, 1.5, 4.2, 4.15, 4.1])
        elif choice == '3':
            # Needs 5 high readings to trigger SUSTAINED
            sim.run_scenario("STEADY THEFT", [1.5, 3.2, 3.25, 3.22, 3.28, 3.24, 3.21])
        elif choice == '4':
            sim.run_scenario("FLUCTUATION", [1.5, 2.1, 1.6, 2.2, 1.7, 2.3])
        elif choice == '5':
            sim.run_scenario("NOISE", [1.5, 3.0, 1.5, 1.52, 1.5])
        elif choice == 'Q':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
