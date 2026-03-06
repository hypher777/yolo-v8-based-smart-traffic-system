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

import threading

# ==========================================
# USER CONFIGURATION: MULTI-ROAD
# ==========================================
CAMERA_SOURCES = [
    "http://192.168.130.118:4747/video",  # Road 1
    "http://192.168.130.224:4747/video",  # Road 2
    "http://192.168.130.96:4747/video",  # Road 3 (Placeholder)
    "http://192.168.130.214:4747/video"   # Road 4 (Placeholder)
]
# ==========================================

class CameraStream:
    """Threaded camera reader to eliminate lag and make process faster."""
    def __init__(self, src):
        self.cap = cv2.VideoCapture(str(src))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.status, self.frame = self.cap.read()
        self.stopped = False
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True

    def start(self):
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if not self.cap.isOpened():
                self.stopped = True
                break
            (self.status, self.frame) = self.cap.read()

    def get_frame(self):
        return self.frame if self.status else None

    def stop(self):
        self.stopped = True
        self.cap.release()

def open_cameras(mode, camera_args):
    streams = []
    if mode == "simulation":
        # Assume up to 4 video files for simulation based on camera count
        video_files = [f"videos/road{i}.mp4" for i in range(1, len(camera_args) + 1)]
        for vf in video_files:
            if os.path.exists(vf):
                cap = cv2.VideoCapture(vf)
                streams.append(cap)
            else:
                streams.append(None)
        return streams

    for i, src in enumerate(camera_args):
        print(f"Connecting to Road {i+1} Source: {src}...", end=" ", flush=True)
        stream = CameraStream(src).start()
        time.sleep(1) # Give time to buffer
        if stream.status:
            print("SUCCESS")
            streams.append(stream)
        else:
            print("FAILED. Attempting Fallback...")
            stream.stop()
            fallback = src.replace("/video", "/mjpegfeed") if "/video" in src else src.replace("/mjpegfeed", "/video")
            stream = CameraStream(fallback).start()
            if stream.status:
                print("SUCCESS (Fallback)")
                streams.append(stream)
            else:
                print("FAILED")
                streams.append(None)
    return streams

def read_frames(streams, mode):
    frames = []
    for s in streams:
        if s is None:
            frames.append(None)
        elif mode == "simulation":
            ret, f = s.read()
            frames.append(f if ret else None)
        else:
            frames.append(s.get_frame())
    return frames

def main():
    parser = argparse.ArgumentParser(description='Smart Traffic Signal Control')
    parser.add_argument('--mode', choices=['simulation', 'demo', 'live'], default='simulation')
    parser.add_argument('--cameras', nargs='+', default=CAMERA_SOURCES)
    parser.add_argument('--port', type=str, default='COM5')
    args = parser.parse_args()

    print(f"Initializing Smart Traffic ({len(args.cameras)} ROADS) | Mode: {args.mode.upper()}")
    
    # Create a single shared YOLO model instance to save memory and CPU
    base_detector = VehicleDetector()
    road_detectors = [base_detector] + [VehicleDetector(model_instance=base_detector.model) for _ in range(len(args.cameras) - 1)]
    
    emergency_logic = EmergencyHandler()
    controller = TrafficController(num_roads=len(args.cameras))
    arduino = ArduinoComm(port=args.port, simulation_mode=(args.mode == "simulation"))
    visualizer = SimulationVisualizer()

    caps = open_cameras(args.mode, args.cameras)
    frame_count = 0
    detector_cache = {} 
    
    try:
        while True:
            raw_frames = read_frames(caps, args.mode)
            frame_count += 1
            
            # FAST PROCESS: Only detect every 3rd frame to maximize speed
            # The visual will still be smooth since we draw labels on cached results
            run_detection = (frame_count % 3 == 0)
            
            annotated_frames = []
            vehicle_counts = []
            emergency_statuses = []

            for i, frame in enumerate(raw_frames):
                if frame is not None:
                    if run_detection:
                        # Use the specific detector for this road
                        ann, count, emg_list = road_detectors[i].detect(frame)
                        detector_cache[i] = (ann, count, emg_list)
                    else:
                        ann, count, emg_list = detector_cache.get(i, (frame, 0, []))
                    
                    is_emg, emg_type = emergency_logic.check_emergency(emg_list)
                    annotated_frames.append(ann)
                    vehicle_counts.append(count)
                    emergency_statuses.append(emg_type if is_emg else None)
                else:
                    annotated_frames.append(None)
                    vehicle_counts.append(0)
                    emergency_statuses.append(None)

            signal_states, switch = controller.decide_signals(vehicle_counts, emergency_statuses)
            if switch or any(emergency_statuses):
                for i, state in enumerate(signal_states):
                    arduino.send_command(i, state)

            grid = visualizer.display_multiview(annotated_frames, signal_states, vehicle_counts, emergency_statuses)
            cv2.imshow("Smart Traffic Control", grid)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
                
    finally:
        for s in caps: 
            if s:
                if hasattr(s, 'stop'): s.stop()
                elif hasattr(s, 'release'): s.release()
        arduino.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
