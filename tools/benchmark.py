import os
import csv
import cv2
import time
import sys

# Add root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.main import process_image
except ImportError:
    # If run from within tools folder
    sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
    from main import process_image

class OCRBenchmark:
    def __init__(self, input_dir=os.path.join("data", "samples"), output_dir="reports"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.debug_dir = os.path.join(output_dir, "debug_logs")
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.debug_dir, exist_ok=True)

    def run_batch(self, api_key=None):
        """
        Processes all images in the input directory and saves results to CSV.
        """
        if not os.path.exists(self.input_dir):
            print(f"Error: Input directory {self.input_dir} not found.")
            return

        image_files = [f for f in os.listdir(self.input_dir) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print(f"Error: No images found in {self.input_dir}")
            return

        print(f"🚀 Starting AI Tutor Benchmark on {len(image_files)} images...")
        
        report_path = os.path.join(self.output_dir, "ocr_accuracy_report.csv")
        
        with open(report_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Filename", "Local Corrected", "Teacher Result", 
                "Score (%)", "Correction Boost", "Status", 
                "AI Feedback", "Time (s)"
            ])

            for filename in image_files:
                img_path = os.path.join(self.input_dir, filename)
                start_time = time.time()
                
                print(f"🔍 Analyzing: {filename}...")
                res = process_image(img_path, api_key=api_key)
                
                duration = round(time.time() - start_time, 2)
                status = "PASS" if res.get("is_correct") else "FAIL"
                
                qa = res.get("qa_report", {})
                score = qa.get("final_score", 0)
                boost = qa.get("improvement", 0)
                feedback = qa.get("feedback", "N/A")
                
                writer.writerow([
                    filename,
                    res.get("final_text", ""),
                    res.get("api_text", "N/A"),
                    f"{score}%",
                    f"+{boost}%",
                    status,
                    feedback,
                    duration
                ])
                
                if res.get("boxed_image_path"):
                    debug_img = cv2.imread(res["boxed_image_path"])
                    if debug_img is not None:
                        cv2.imwrite(os.path.join(self.debug_dir, f"debug_{filename}"), debug_img)

        print(f"✅ Benchmark Complete! Report saved to: {report_path}")

if __name__ == "__main__":
    benchmark = OCRBenchmark()
    benchmark.run_batch()
