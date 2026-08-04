"""
VanRakshak AI - CLI Prediction Testing Tool
A wrapper script that imports `predict_image` from `predictor.py` 
to run manual terminal tests and append results to a CSV ledger.
"""

import os
import csv
from datetime import datetime
from PIL import Image

# Import our new encapsulated ML logic
from predictor import predict_image


def save_to_csv(image_path: str, result: dict, csv_path: str = "predictions.csv"):
    """Appends the prediction results to a CSV file, creating headers if the file doesn't exist."""
    file_exists = os.path.isfile(csv_path)
    
    image_name = os.path.basename(image_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    top3 = result["top3"]
    top1 = top3[0]["class"] if len(top3) > 0 else ""
    top2 = top3[1]["class"] if len(top3) > 1 else ""
    top3_class = top3[2]["class"] if len(top3) > 2 else ""

    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Image Name", "Predicted Class", "Confidence", "Top1", "Top2", "Top3"])
        
        writer.writerow([
            timestamp, 
            image_name, 
            result["prediction"], 
            f"{result['confidence']:.2f}", 
            top1, 
            top2, 
            top3_class
        ])

def print_prediction_report(image_path: str, image_size: tuple, result: dict):
    """Prints a formatted, professional prediction report to the terminal."""
    image_name = os.path.basename(image_path)
    
    print("\n" + "="*50)
    print(" VANRAKSHAK AI - PREDICTION REPORT")
    print("="*50)
    print(f" Image Name       : {image_name}")
    print(f" Image Size       : {image_size[0]}x{image_size[1]}")
    print("-" * 50)
    print(f" PREDICTION       : {result['prediction']}")
    print(f" CONFIDENCE       : {result['confidence']:.2f}%")
    print(f" CONFIDENCE LEVEL : {result['confidence_level']}")
    print("-" * 50)
    print(" TOP 3 PREDICTIONS:")
    for i, item in enumerate(result["top3"], 1):
        print(f" {i}. {item['class'].ljust(25)} ({item['confidence']:.2f}%)")
    print("-" * 50)
    print(f" Prediction Time  : {result['prediction_time']:.4f} seconds")
    print("="*50 + "\n")


if __name__ == "__main__":
    # -----------------------------
    # Get Image Path
    # -----------------------------
    image_path = input("Enter image path:\n").strip()
    
    if not os.path.exists(image_path):
        print(f"\n❌ Error: File not found at {image_path}")
        exit()

    try:
        # Load image size solely for the CLI report presentation
        with Image.open(image_path) as img:
            image_size = img.size
            
        # -----------------------------
        # Execute Prediction API
        # -----------------------------
        result = predict_image(image_path)
        
        # -----------------------------
        # Output & Log Results
        # -----------------------------
        print_prediction_report(image_path, image_size, result)
        
        save_to_csv(image_path, result, csv_path="predictions.csv")
        print("✅ Result appended to predictions.csv")
        
    except Exception as e:
        print(f"\n❌ Failed to process image.\n{e}")