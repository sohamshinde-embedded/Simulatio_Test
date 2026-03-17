import cv2
import numpy as np
from ultralytics import YOLO

class VisionSystem:
    def __init__(self, model_path="model/best.pt"):
        self.model = YOLO(model_path)
        
        # --- CALIBRATION ---
        # Adjust these pixel coordinates to perfectly match your camera's view of the belt
        self.px_corners = np.array([[150, 100], [350, 100], [350, 300], [150, 300]], dtype=np.float32)
        
        # Real-world measurements of that box in millimeters
        self.mm_corners = np.array([[0, 0], [130, 0], [130, 130], [0, 130]], dtype=np.float32)
        
        self.M = cv2.getPerspectiveTransform(self.px_corners, self.mm_corners)
        
        # Physical distance from the camera box to the Robot's center
        self.OFFSET_TO_ROBOT = 220.0 

    def get_targets(self, frame):
        # Run YOLO with ByteTrack to keep IDs stable
        results = self.model.track(frame, persist=True, verbose=False, tracker="bytetrack.yaml")
        targets = []
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)
            clss = results[0].boxes.cls.cpu().numpy().astype(int)

            for box, track_id, cls in zip(boxes, ids, clss):
                # IMPORTANT: Change '0' if the class ID you want to ignore changes
                if cls == 0: continue 
                
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                px_pt = np.array([[[cx, cy]]], dtype=np.float32)
                
                # Transform to mm
                mm_pt = cv2.perspectiveTransform(px_pt, self.M)[0][0]
                
                # Calculate total distance the object must travel
                distance_to_travel = (130.0 - mm_pt[0]) + self.OFFSET_TO_ROBOT
                
                targets.append({
                    'id': track_id,
                    'dist': distance_to_travel, 
                    'y': mm_pt[1], 
                    'label': self.model.names[cls],
                    'box': box
                })
                
        # RETURN A CLEAN FRAME instead of YOLO's auto-drawn frame
        return targets, frame.copy()