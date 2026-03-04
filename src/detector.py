import cv2
import os
from ultralytics import YOLO
import numpy as np

class VehicleDetector:
    def __init__(self, models_dir='models', model_instance=None):
        """
        Initialize YOLOv8 models.
        """
        self.tracker = {} # {id: {'box': [x1,y1,x2,y2], 'missed': 0, 'conf': c}}
        self.emergency_history = {} 
        
        if model_instance:
            self.model = model_instance
            return

        # Strictly use best.pt
        self.model_path = os.path.join(models_dir, "best.pt")
        if not os.path.exists(self.model_path):
            self.model_path = "best.pt"
            
        if not os.path.exists(self.model_path):
             print(f"WARNING: '{self.model_path}' not found. Ensure your trained model is in the folder.")
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
        
        # 2. Optimization: Resize for YOLO Speed
        yolo_input = cv2.resize(frame, (416, 416))
        
        # 3. Run YOLO with refined parameters
        # Lowered confidence back to 0.25 and removed class filters
        results = self.model(yolo_input, verbose=False, conf=0.25, iou=0.45)[0]
        
        if not hasattr(self, '_logged_names'):
            print(f"DEBUG: Model Detects Classes: {self.model.names}")
            self._logged_names = True

        current_detections = []
        h, w = frame.shape[:2]
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < 0.20: continue # Lower exit threshold
            
            bx1, by1, bx2, by2 = box.xyxy[0]
            # Ignore very small boxes (less than 30 pixels) to avoid noise
            if (bx2-bx1) < 30 or (by2-by1) < 30: continue

            x1 = int(bx1 * w / 416)
            y1 = int(by1 * h / 416)
            x2 = int(bx2 * w / 416)
            y2 = int(by2 * h / 416)
            
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
        
        # Cleanup history for lost IDs to prevent "Status Leakage"
        current_active = set(self.tracker.keys())
        self.emergency_history = {vid: history for vid, history in self.emergency_history.items() if vid in current_active}
        
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
                    min_dist = 300 # Increased radius to catch markers on car hoods/roofs
                    
                    for vid, data in self.tracker.items():
                        x1, y1, x2, y2 = data['box']
                        v_center = np.array([(x1+x2)/2, (y1+y2)/2])
                        dist = np.linalg.norm(m_center - v_center)
                        
                        if dist < min_dist:
                            min_dist = dist
                            best_vid = vid
                    
                    if best_vid is not None:
                        frame_emergency_map[best_vid] = status_type
        
        # 5. Annotation & Reporting
        # Initialize emergency_list with markers found in frame (Strict Priority)
        # This ensures logic triggers even if YOLO misses the car
        emergency_list = []
        if global_ids is not None:
            for mid in global_ids.flatten():
                if mid == 1: emergency_list.append('ambulance')
                elif mid == 2: emergency_list.append('fire truck')

        vehicle_count = 0
        annotated_frame = frame.copy()

        if global_ids is not None:
            cv2.aruco.drawDetectedMarkers(annotated_frame, global_corners, global_ids)

        for vid, data in self.tracker.items():
            if data['conf'] < 0.35: continue
            
            vehicle_count += 1
            x1, y1, x2, y2 = data['box']
            conf = int(data['conf'] * 100)
            
            # STRICT RULE: Only flag as emergency if a marker is VISIBLE IN THIS FRAME near this car
            # Also fallback to general frame marker status for labeling
            marker_status = frame_emergency_map.get(vid, None)
            
            # If marker exists but wasn't perfectly matched to a VID, use general list for label fallback
            if not marker_status and emergency_list:
                marker_status = emergency_list[0] 
                
            if marker_status:
                color = (0, 0, 255) if marker_status == 'fire truck' else (255, 0, 255)
                display_label = f"{marker_status.upper()} EMERGENCY"
                thickness = 4 # High visibility
            else:
                color = (255, 0, 0) # Blue for Normal Vehicles
                display_label = f"Car {conf}%"
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
