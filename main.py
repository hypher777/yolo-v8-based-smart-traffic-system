import cv2
import time
import argparse
import sys
import os

# Ensure src is in path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.detector import VehicleDetector
from src.emergency import EmergencyHandler
from src.traffic_logic import TrafficController
from src.arduino_comm import ArduinoComm
from src.simulation import SimulationVisualizer

# ==========================================
# USER CONFIGURATION: EDIT YOUR PHONE IPs HERE
# ==========================================
CAMERA_SOURCES = [
    "http://192.168.130.45:4747/mjpegfeed",  # Road 1 (Phone 1)
    "http://192.168.130.224:4747/mjpegfeed", # Road 2 (Phone 2)
    "0",                                    # Road 3 (Slot 3)
    "1"                                     # Road 4 (Slot 4)
]
# ==========================================

def open_cameras(mode: str, camera_args: list):
    caps = []
    backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY

    if mode == "simulation":
        video_files = [f"videos/road{i}.mp4" for i in range(1, 5)]
        for vf in video_files:
            if os.path.exists(vf):
                caps.append(cv2.VideoCapture(vf))
            else:
                caps.append(None)
        return caps

    if mode == "demo" or mode == "live":
        for i, src in enumerate(camera_args[:4]):
            if src is None:
                caps.append(None)
                continue
            
            print(f"Connecting to Road {i+1} Source: {src}...", end=" ", flush=True)
            if str(src).isdigit():
                idx = int(src)
                cap = cv2.VideoCapture(idx, backend)
            else:
                # WiFi/Phone URLs
                cap = cv2.VideoCapture(src)
            
            if cap.isOpened():
                print("SUCCESS")
                caps.append(cap)
            else:
                print("FAILED")
                caps.append(None)
        
        if mode == "demo" and len(caps) == 1 and caps[0]:
            return [caps[0]] * 4
            
        while len(caps) < 4:
            caps.append(None)
        return caps

    return [None] * 4

def read_frames(caps):
    frames = []
    cache = {}
    for cap in caps:
        if cap is None:
            frames.append(None)
            continue
        cap_id = id(cap)
        if cap_id not in cache:
            ret, frame = cap.read()
            cache[cap_id] = (ret, frame)
        ret, frame = cache[cap_id]
        frames.append(frame if ret else None)
    return frames

def main():
    parser = argparse.ArgumentParser(description='Smart Traffic Signal Control')
    parser.add_argument('--mode', choices=['simulation', 'demo', 'live'], default='simulation')
    parser.add_argument('--cameras', nargs='+', default=CAMERA_SOURCES, help='Camera indices or URLs')
    parser.add_argument('--port', type=str, default='COM5', help='Arduino Port')
    args = parser.parse_args()

    mode = args.mode
    print(f"Initializing Smart Traffic System | Mode: {mode.upper()}")
    
    detector = VehicleDetector()
    emergency_logic = EmergencyHandler()
    controller = TrafficController(num_roads=4)
    arduino = ArduinoComm(port=args.port, simulation_mode=(mode == "simulation"))
    visualizer = SimulationVisualizer()

    caps = open_cameras(mode, args.cameras)
    print("System Started. Press 'q' to exit.")

    try:
        while True:
            raw_frames = read_frames(caps)
            
            annotated_frames = []
            vehicle_counts = []
            emergency_statuses = []

            for i, frame in enumerate(raw_frames):
                if frame is not None:
                    ann, count, emg_list = detector.detect(frame)
                    is_emg, emg_type = emergency_logic.check_emergency(emg_list)
                    
                    annotated_frames.append(ann)
                    vehicle_counts.append(count)
                    emergency_statuses.append(emg_type if is_emg else None)
                else:
                    annotated_frames.append(None)
                    vehicle_counts.append(0)
                    emergency_statuses.append(None)

            signal_states, switch_happened = controller.decide_signals(vehicle_counts, emergency_statuses)
            
            if switch_happened or any(emergency_statuses):
                for i, state in enumerate(signal_states):
                    arduino.send_command(i, state)

            grid = visualizer.display_multiview(annotated_frames, signal_states, vehicle_counts, emergency_statuses)
            cv2.imshow("Smart Traffic Control", grid)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        seen = set()
        for cap in caps:
            if cap and id(cap) not in seen:
                cap.release()
                seen.add(id(cap))
        arduino.close()
        cv2.destroyAllWindows()
        print("\nExited.")

if __name__ == "__main__":
    main()
