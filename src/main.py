import os
import sys
import cv2
import numpy as np

# Set console encoding to UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from preprocessor import ImagePreprocessor
from segmenter import CharacterSegmenter
from recognizer import CharacterRecognizer
from validator import PatternValidator
from qa_analyzer import QAAnalyzer

def process_image(image_path, api_key=None):
    """
    Run the OCR pipeline on a given image and return the results.
    This function is designed to be called by the GUI.
    """
    result = {
        "status": "error",
        "message": "",
        "raw_text": "",
        "final_text": "",
        "api_text": "ไม่ได้ใช้ API",
        "is_correct": False,
        "boxed_image_path": None,
        "qa_report": None
    }
    
    if not os.path.exists(image_path):
        result["message"] = f"ไม่พบรูปภาพที่: {image_path}"
        return result

    # Create dummy dir for output if it doesn't exist
    output_dir = "test_images"
    os.makedirs(output_dir, exist_ok=True)

    try:
        preprocessor = ImagePreprocessor()
        segmenter = CharacterSegmenter()
        recognizer = CharacterRecognizer(mode="tesseract") 
        validator = PatternValidator()
        qa = QAAnalyzer()
        
        # 1. Image Preprocessing
        original_img, clean_img = preprocessor.process(image_path)
        
        # 2. Character Segmentation
        char_images, boxes = segmenter.segment(clean_img, original_img)
        
        boxed_img = segmenter.draw_boxes(original_img, boxes)
        boxed_img_path = os.path.join(output_dir, "processed_result.jpg")
        cv2.imwrite(boxed_img_path, boxed_img)
        result["boxed_image_path"] = boxed_img_path
        
        # 3. Cloud API Recognition (If key provided)
        if api_key and api_key.strip():
            api_result = recognizer.recognize_via_api(image_path, api_key)
            result["api_text"] = api_result

        if len(char_images) == 0:
            result["message"] = "สแกนไม่พบตัวอักษรในภาพ โปรดลองรูปอื่น"
            return result

        # 4. AI Character Recognition (Local Multi-Pass)
        # char_images[0] is now a dictionary containing binary and gray versions
        line_data = char_images[0]
        raw_text = recognizer.recognize_all(line_data)
        result["raw_text"] = raw_text
        
        # 5. Validation and Correction
        local_corrected = validator.auto_correct(raw_text)
        
        # 6. Priority Logic (100% Accuracy Path)
        # If the Teacher (Cloud) gave a valid result, prioritize it!
        api_text = result["api_text"]
        if validator.is_valid(api_text):
            final_text = api_text
            is_correct = True
            # Update QA to reflect that we synced with the teacher
            feedback_sync = "(Synced with Cloud AI Ground Truth)"
        else:
            final_text = local_corrected
            is_correct = validator.is_valid(final_text)
            feedback_sync = ""
        
        result["final_text"] = final_text
        result["is_correct"] = is_correct
        
        # 7. QA Analysis
        result["qa_report"] = qa.get_report_card(raw_text, final_text, api_text)
        if feedback_sync:
            result["qa_report"]["feedback"] += f" | {feedback_sync}"
        
        result["status"] = "success"
        result["message"] = "สแกนสำเร็จ"
        return result
        
    except Exception as e:
        result["message"] = f"เกิดข้อผิดพลาด: {str(e)}"
        return result

def main():
    # Keep the terminal CLI as a fallback or for testing
    test_dir = "test_images"
    os.makedirs(test_dir, exist_ok=True)
    image_path = os.path.join(test_dir, "sample.jpg")
    
    if not os.path.exists(image_path):
        print(f"⚠️ ไม่พบรูปภาพที่: {image_path}")
        print("ระบบกำลังสร้างรูปจำลองเพื่อทดสอบการทำงาน...")
        dummy_img = np.zeros((200, 800, 3), dtype=np.uint8)
        cv2.putText(dummy_img, "KPRU68-15.00-0089/034", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 4)
        cv2.imwrite(image_path, dummy_img)

    print("--- 📸 เริ่มการประมวลผลผ่านคลิป (CLI) ---")
    res = process_image(image_path)
    
    if res["status"] == "error":
        print(res["message"])
        return
        
    print(f"ข้อความดิบจาก Local AI: {res['raw_text']}")
    print(f"ข้อความสำหรับนำไปบันทึก (แก้ไขแล้ว): [{res['final_text']}]")
    print(f"ข้อความจาก Cloud API (คุณครู): {res['api_text']}")
    
    if res["qa_report"]:
        print(f"--- 🎓 รายงานผลวิเคราะห์ (QA Report Card) ---")
        print(f"คะแนนความถูกต้อง: {res['qa_report']['final_score']}%")
        print(f"คะแนนพัฒนาการ (Correction): +{res['qa_report']['improvement']} pts")
        print(f"คำแนะนำจาก AI: {res['qa_report']['feedback']}")
    
    if res["is_correct"]:
         print("สถานะรูปแบบ: ผ่าน (ข้อมูลสมบูรณ์)")
    else:
         print("สถานะรูปแบบ: ไม่ผ่านรูปแบบ (กล้องอาจตกหล่นบางตัวอักษร)")

if __name__ == "__main__":
    main()
