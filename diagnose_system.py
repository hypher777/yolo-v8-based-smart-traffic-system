import cv2
import serial.tools.list_ports
import requests
import time

def test_camera(url):
    print(f"\nTesting Camera: {url}")
    try:
        # First test if the IP is even reachable via HTTP
        resp = requests.get(url, timeout=3)
        print(f"  HTTP Reachability: SUCCESS (Status {resp.status_code})")
    except Exception as e:
        print(f"  HTTP Reachability: FAILED ({e})")
    
    # Now test with OpenCV
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        print("  OpenCV Connection: SUCCESS")
        ret, frame = cap.read()
        if ret:
            print("  Frame Capture: SUCCESS")
        else:
            print("  Frame Capture: FAILED")
        cap.release()
    else:
        print("  OpenCV Connection: FAILED")

def scan_ports():
    print("\nScanning Serial Ports...")
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("  No serial ports found!")
    for p in ports:
        print(f"  Found: {p.device} ({p.description})")

if __name__ == "__main__":
    print("=== Smart Traffic System Diagnostics ===")
    
    # Test the current IPs
    test_camera("http://192.168.130.45:4747/video")
    test_camera("http://192.168.130.45:4747/mjpegfeed")
    test_camera("http://192.168.130.224:4747/video")
    test_camera("http://192.168.130.224:4747/mjpegfeed")
    
    scan_ports()
    print("\n========================================")
    print("If all FAILED, check if your VPN is ON or if phones are on a different WiFi.")
