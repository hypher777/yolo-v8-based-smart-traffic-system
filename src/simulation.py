import cv2
import numpy as np

class SimulationVisualizer:
    def __init__(self):
        # Color definitions
        self.RED = (0, 0, 255)
        self.YELLOW = (0, 255, 255)
        self.GREEN = (0, 255, 0)
        self.GRAY = (100, 100, 100)
        
    def draw_traffic_light(self, frame, state, road_index):
        """Draw a traffic light overlay on the frame."""
        h, w = frame.shape[:2]
        top_left = (w - 100, 20)
        bottom_right = (w - 20, 220)
        cv2.rectangle(frame, top_left, bottom_right, (50, 50, 50), -1)
        
        c_red = (w - 60, 60)
        c_yel = (w - 60, 120)
        c_grn = (w - 60, 180)
        radius = 25
        
        col_red = self.RED if state == "RED" else self.GRAY
        col_yel = self.YELLOW if state == "YELLOW" else self.GRAY
        col_grn = self.GREEN if state == "GREEN" else self.GRAY
        
        cv2.circle(frame, c_red, radius, col_red, -1)
        cv2.circle(frame, c_yel, radius, col_yel, -1)
        cv2.circle(frame, c_grn, radius, col_grn, -1)
        
        cv2.putText(frame, f"Road {road_index+1}", (w - 95, 20 + 215), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return frame

    def display_multiview(self, frames, states, vehicle_counts, emergency_status):
        """Combine active road frames into an adaptive grid."""
        target_size = (640, 480)
        
        # Identify active roads (cameras that aren't None)
        active_indices = [i for i, f in enumerate(frames) if f is not None]
        num_active = len(active_indices)
        
        # Prepare all frames (including placeholders for inactive roads)
        display_frames = []
        for i, f in enumerate(frames):
            if f is None:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, f"No Signal - Road {i+1}", (50, 240), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                f = blank
            else:
                f = cv2.resize(f, target_size)
            
            info_color = (0, 255, 0)
            if emergency_status[i]:
                info_color = (0, 0, 255)
                cv2.putText(f, f"EMERGENCY: {emergency_status[i].upper()}", (10, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, info_color, 2)
                
            cv2.putText(f, f"Vehicles: {vehicle_counts[i]}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, info_color, 2)
            
            f = self.draw_traffic_light(f, states[i], i)
            display_frames.append(f)

        # Build adaptive grid
        if num_active <= 2:
            # 1x2 Grid Side-by-Side (Road 1 and Road 2)
            grid = np.hstack((display_frames[0], display_frames[1]))
            title = "Smart Traffic Control - Dual View"
        else:
            # 2x2 Grid for 3 or 4 roads
            top_row = np.hstack((display_frames[0], display_frames[1]))
            bot_row = np.hstack((display_frames[2], display_frames[3]))
            grid = np.vstack((top_row, bot_row))
            title = "Smart Traffic Control - 4-Way View"

        cv2.putText(grid, title, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Ensure window is visible
        cv2.namedWindow("Smart Traffic Control", cv2.WINDOW_AUTOSIZE)
        return grid
