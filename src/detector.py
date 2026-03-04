import cv2
import os
from ultralytics import YOLO
import numpy as np

class VehicleDetector:
    def __init__(self, models_dir='models'):
        """
        Initialize YOLOv8 models.
        """
        self.tracker = {} # {id: {'box': [x1,y1,x2,y2], 'missed': 0, 'conf': c}}
        self.emergency_history = {} # {id: [last_5_statuses]}
        
        # Strictly use best.pt
        self.model_path = os.path.join(models_dir, "best.pt")
        if not os.path.exists(self.model_path):
            # Fallback to local directory if models/ not found
            self.model_path = "best.pt"
            
        if not os.path.exists(self.model_path):
             print(f"WARNING: '{self.model_path}' not found. Ensure your trained model is in the folder.")
             # We won't raise error here to allow system to start (though detection will fail)
             self.model = None
        else:
            print(f"Loading Trained Model: {self.model_path}")
            self.model = YOLO(self.model_path)
            
        self.vehicle_classes = [0] 

    def detect(self, frame):
        """
        Advanced Detection with Hysteresis, Persistence, and ArUco Markers.
        ArUco ID 1 -> Ambulance, ID 2 -> Fire Truck
        """
        if self.model is None:
            return frame, 0, []

        # 1. Setup ArUco detector (Dictionary 4x4)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        
        # Enhanced ArUco params
        aruco_params.adaptiveThreshWinSizeMin = 3
        aruco_params.adaptiveThreshWinSizeMax = 23
        aruco_params.adaptiveThreshWinSizeStep = 5
        aruco_params.minMarkerPerimeterRate = 0.01
        aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        
        aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
        
        # 2. Run YOLO with hysteresis confidence
        results = self.model(frame, verbose=False, conf=0.35)[0]
        
        current_detections = []
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < 0.25: continue # Exit threshold
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            current_detections.append({'box': [x1,y1,x2,y2], 'conf': conf})

        # 3. Persistence and Hysteresis
        new_tracker = {}
        for det in current_detections:
            matched = False
            for old_id, old_data in self.tracker.items():
                ox1, oy1, ox2, oy2 = old_data['box']
                cx1, cy1, cx2, cy2 = det['box']
                if abs(ox1-cx1) < 50 and abs(oy1-cy1) < 50:
                    new_tracker[old_id] = {'box': det['box'], 'missed': 0, 'conf': det['conf']}
                    matched = True
                    break
            if not matched:
                new_id = len(new_tracker) + len(self.tracker)
                new_tracker[new_id] = {'box': det['box'], 'missed': 0, 'conf': det['conf']}

        for old_id, old_data in self.tracker.items():
            if old_id not in new_tracker and old_data['missed'] < 3:
                old_data['missed'] += 1
                new_tracker[old_id] = old_data

        self.tracker = new_tracker
        
        # 4. ArUco Marker - GLOBAL SEARCH
        global_corners, global_ids, _ = aruco_detector.detectMarkers(frame)
        frame_emergency_map = {}
        
        if global_ids is not None:
            flat_ids = global_ids.flatten()
            for i, marker_id in enumerate(flat_ids):
                status_type = None
                if marker_id == 1: status_type = 'ambulance'
                elif marker_id == 2: status_type = 'fire truck'
                
                if status_type:
                    m_corners = global_corners[i][0]
                    m_center = np.mean(m_corners, axis=0)
                    
                    best_vid = None
                    min_dist = 150
                    
                    for vid, data in self.tracker.items():
                        x1, y1, x2, y2 = data['box']
                        v_center = np.array([(x1+x2)/2, (y1+y2)/2])
                        dist = np.linalg.norm(m_center - v_center)
                        
                        if dist < min_dist:
                            min_dist = dist
                            best_vid = vid
                    
                    if best_vid is not None:
                        frame_emergency_map[best_vid] = status_type
        
        # 5. Annotation
        emergency_list = []
        vehicle_count = 0
        annotated_frame = frame.copy()

        if global_ids is not None:
            cv2.aruco.drawDetectedMarkers(annotated_frame, global_corners, global_ids)

        for vid, data in self.tracker.items():
            if data['conf'] < 0.35 and vid not in self.emergency_history: continue
            
            vehicle_count += 1
            x1, y1, x2, y2 = data['box']
            conf = int(data['conf'] * 100)
            status = frame_emergency_map.get(vid, None)
            
            if vid not in self.emergency_history: self.emergency_history[vid] = []
            self.emergency_history[vid].append(status)
            if len(self.emergency_history[vid]) > 5: self.emergency_history[vid].pop(0)
            
            history = self.emergency_history[vid]
            final_status = None
            for s_type in ['ambulance', 'fire truck']:
                if history.count(s_type) >= 2:
                    final_status = s_type
                    break
            
            base_label = self.model.names[0] if self.model and self.model.names else "vehicle"
            
            if final_status:
                emergency_list.append(final_status)
                color = (0, 0, 255) if final_status == 'fire truck' else (255, 0, 255)
                display_label = f"{final_status.upper()} {conf}%"
                thickness = 3
            else:
                color = (255, 0, 0)
                display_label = f"{base_label} {conf}%"
                thickness = 2
                
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            (tw, th), _ = cv2.getTextSize(display_label, font, font_scale, 2)
            label_y = y1 - 10 if y1 > 30 else y1 + th + 20
            
            cv2.rectangle(annotated_frame, (x1, label_y-th-5), (x1+tw+10, label_y+5), color, -1)
            cv2.putText(annotated_frame, display_label, (x1+5, label_y-2), 
                        font, font_scale, (255, 255, 255), 2)

        return annotated_frame, vehicle_count, list(set(emergency_list))
