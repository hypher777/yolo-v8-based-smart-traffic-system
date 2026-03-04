import subprocess
import os

def ping_device(ip):
    print(f"Checking connectivity to {ip}...")
    try:
        # -n 2 means send 2 packets
        output = subprocess.check_output(f"ping -n 2 {ip}", shell=True).decode()
        if "Reply from" in output and "Destination host unreachable" not in output:
            print(f"✅ SUCCESS: Device at {ip} is REACHABLE.")
            return True
        else:
            print(f"❌ FAILED: Device at {ip} is NOT responding to ping.")
            return False
    except Exception as e:
        print(f"❌ ERROR: Could not ping {ip}. {str(e)}")
        return False

targets = ["192.168.130.118", "192.168.130.224"]
for t in targets:
    ping_device(t)
    print("-" * 30)

print("\nNETWORK TIP: If ping fails, ensure:")
print("1. Phone and PC are on the same WiFi (e.g., both on 'Home_5G').")
print("2. AP Isolation is OFF in your router settings.")
print("3. Phone screen is ON and DroidCam app is running.")
