import cv2
import numpy as np
import threading
import queue
from vision_engine import VisionSystem
from robot_controller import ESP32Robot

# ==========================================
# SYSTEM CONFIGURATION
# ==========================================
ROBOT_PORT = "COM4" # Check Device Manager for your Kikobot COM port!
BELT_SPEED = 35.0   # Belt speed in mm/second
# ==========================================

target_queue = queue.Queue()
processed_ids = set()

eye = VisionSystem(model_path="model/best.pt")
hand = ESP32Robot(port=ROBOT_PORT)

def robot_worker():
    """Background thread to process physical robot moves."""
    while True:
        item = target_queue.get()
        if item is None: break
        
        print(f"\n[+] NEW JOB: Sorting {item['label']} (ID: {item['id']})")
        hand.execute_sort(item['dist'], item['y'], BELT_SPEED)
        
        target_queue.task_done()

# Start the robot background thread
threading.Thread(target=robot_worker, daemon=True).start()

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("[*] System Armed. Watching conveyor belt...")

while True:
    ret, frame = cap.read()
    if not ret: break

    targets, debug_frame = eye.get_targets(frame)
    
    # Draw the yellow calibration boundary
    cv2.polylines(debug_frame, [np.int32(eye.px_corners)], True, (0, 255, 255), 2)
    
    for t in targets:
        # Extract the bounding box to find the center pixel
        x1, y1, x2, y2 = t['box']
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        
        # =======================================================
        # REGION OF INTEREST (ROI) FILTER
        # =======================================================
        is_inside = cv2.pointPolygonTest(np.int32(eye.px_corners), (float(cx), float(cy)), False)
        
        if is_inside < 0:
            # Object is outside the yellow box. Do nothing.
            continue 
        # =======================================================

        # --- DRAW VISUALS ONLY FOR OBJECTS INSIDE THE BOX ---
        cv2.rectangle(debug_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(debug_frame, f"ID:{t['id']} {t['label']}", (int(x1), int(y1)-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.circle(debug_frame, (int(cx), int(cy)), 4, (0, 255, 0), -1)

        # Queue the job if the robot is ready and we haven't processed this ID yet
        if t['id'] not in processed_ids and t['dist'] > 0: 
            if target_queue.empty(): 
                processed_ids.add(t['id'])
                target_queue.put(t)

    # Prevent memory bloat from processed_ids over long runs
    if len(processed_ids) > 1000:
        processed_ids.clear()

    cv2.imshow("Ginger Guard - Live Sorting", debug_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

# Clean Shutdown
target_queue.put(None) 
cap.release()
cv2.destroyAllWindows()