import cv2
import numpy as np
import os

def generate_marker(marker_id, size=400, border_bits=1):
    # Use the 4x4_50 dictionary as established in detector.py
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Generate the marker image
    marker_img = np.zeros((size, size), dtype=np.uint8)
    marker_img = cv4_aruco_generate_marker(dictionary, marker_id, size, marker_img, border_bits)
    
    # Add an EXTRA SIGNIFICANT white border (Quiet Zone)
    # We want a very thick 150px white margin for maximum reliability.
    margin = 150
    final_size = size + 2 * margin
    white_img = np.ones((final_size + 100, final_size), dtype=np.uint8) * 255 # Extra height for label
    
    # Paste the marker into the center of the white square
    white_img[margin:margin+size, margin:margin+size] = marker_img
    
    return white_img

def cv4_aruco_generate_marker(dictionary, marker_id, size, img, border_bits):
    if hasattr(cv2, 'aruco') and hasattr(cv2.aruco, 'generateImageMarker'):
        return cv2.aruco.generateImageMarker(dictionary, marker_id, size, img, border_bits)
    else:
        return cv2.aruco.drawMarker(dictionary, marker_id, size, img, border_bits)

if __name__ == "__main__":
    output_dir = "markers_printable"
    system_dir = "markers"
    
    for d in [output_dir, system_dir]:
        if not os.path.exists(d): os.makedirs(d)
        
    # ID 1 = Ambulance, ID 2 = Fire Truck
    markers = {1: "Ambulance", 2: "FireTruck"}
    
    print(f"Generating ULTIMATE markers with 150px white borders...")
    
    for mid, name in markers.items():
        img = generate_marker(mid)
        # Add label text to the image (below the marker)
        cv2.putText(img, f"ID: {mid} - {name}", (50, img.shape[0] - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
        
        # Save to both locations
        filename1 = os.path.join(output_dir, f"marker_{mid}_{name}.png")
        filename2 = os.path.join(system_dir, f"marker_{mid}_{name}.png")
        
        cv2.imwrite(filename1, img)
        cv2.imwrite(filename2, img)
        print(f"  Created: {filename1}")

    print("\nSUCCESS! Please print the images from the 'markers_printable' folder.")
    print("These have a thick 150px white border for perfect camera detection.")
