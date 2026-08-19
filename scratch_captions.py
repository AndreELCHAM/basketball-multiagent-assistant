import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.image_captioner import _call_vlm, _get_vlm_client

def main():
    client = _get_vlm_client()
    
    images_to_check = [
        "data/images/FIBA/documents-corporate-fiba-official-rules-2026-v1-1.pdf-0007-05.png",
        "data/images/FIBA/documents-corporate-fiba-official-rules-2026-v1-1.pdf-0064-02.png",
        "data/images/FIBA/documents-corporate-fiba-official-rules-2026-v1-1.pdf-0068-10.png"
    ]
    
    results = {}
    for img_path in images_to_check:
        print(f"Testing {img_path}...")
        try:
            caption = _call_vlm(client, img_path)
            results[img_path] = caption
        except Exception as e:
            results[img_path] = f"ERROR: {e}"
            
    with open("data/scratch_captions.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
