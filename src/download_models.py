import requests
import os

MODELS_DIR = "models"
MODELS = {
    "yolov8n.pt": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
    "ambulance.pt": "https://huggingface.co/adityaeucloid/YOLOv8/resolve/main/best.pt",
    "fire.pt": "https://huggingface.co/Yusuf-ozen/Yolov8_Fire_Detection/resolve/main/best.pt"
}

def download_file(url, output_path):
    if os.path.exists(output_path):
        print(f"File {output_path} already exists. Skipping.")
        return

    print(f"Downloading {output_path} from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    for name, url in MODELS.items():
        download_file(url, os.path.join(MODELS_DIR, name))

if __name__ == "__main__":
    main()
