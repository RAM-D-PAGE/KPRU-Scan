import cv2
import numpy as np
import os
import warnings

# Suppress warnings for a cleaner experience
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import google.generativeai as genai
    from PIL import Image as PILImage
except ImportError:
    genai = None

class CharacterRecognizer:
    def __init__(self, mode="tesseract"):
        self.mode = mode
        if self.mode == "tesseract" and pytesseract is None:
            print("Warning: pytesseract is not installed. Will use dummy recognition.")
            self.mode = "dummy"

    def recognize_all(self, line_data):
        """
        Performs Deeper Multi-Pass recognition on both binary and grayscale images.
        """
        if line_data is None:
            return ""
            
        line_bin = line_data.get("binary")
        line_gray = line_data.get("gray")
        
        results = []
        
        # Debug path updated for structured project
        debug_dir = os.path.join("data", "outputs")
        os.makedirs(debug_dir, exist_ok=True)
        if line_bin is not None: cv2.imwrite(os.path.join(debug_dir, "ocr_input_bin.jpg"), line_bin)
        if line_gray is not None: cv2.imwrite(os.path.join(debug_dir, "ocr_input_gray.jpg"), line_gray)

        # Base Configs
        config_line = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'
        config_block = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'
        
        # --- PASSES ON BINARY IMAGE ---
        if line_bin is not None:
            results.append(pytesseract.image_to_string(line_bin, config=config_line).strip())
            results.append(pytesseract.image_to_string(line_bin, config=config_block).strip())
            
            # Sharpened Binary
            kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            line_sharp = cv2.filter2D(line_bin, -1, kernel_sharp)
            results.append(pytesseract.image_to_string(line_sharp, config=config_line).strip())
        
        # --- PASSES ON GRAY IMAGE ---
        if line_gray is not None:
            results.append(pytesseract.image_to_string(line_gray, config=config_line).strip())
            results.append(pytesseract.image_to_string(line_gray, config=config_block).strip())
            
            # High Contrast Gray
            alpha, beta = 1.5, 0 
            line_gray_hc = cv2.convertScaleAbs(line_gray, alpha=alpha, beta=beta)
            results.append(pytesseract.image_to_string(line_gray_hc, config=config_line).strip())
            
            # Laplacian Edge Pass (Helps with 8 vs 5 internal loops)
            line_laplace = cv2.Laplacian(line_gray, cv2.CV_8U, ksize=3)
            _, line_laplace = cv2.threshold(line_laplace, 40, 255, cv2.THRESH_BINARY_INV)
            results.append(pytesseract.image_to_string(line_laplace, config=config_line).strip())

        # Filter and Score
        valid_results = [r for r in results if r and len(r) > 5]
        if not valid_results: return ""
        
        def rate_result(r):
            score = 0
            r_up = r.upper()
            if "KPRU" in r_up: score += 50
            if "-" in r_up: score += 10
            if "." in r_up: score += 5
            score += sum(1 for c in r_up if c.isalnum() or c in '-./')
            return score

        best_result = max(valid_results, key=rate_result)
        return best_result.upper()

    def recognize_via_api(self, image_path, api_key):
        if not genai:
            return "Error: google-generativeai not installed"
        if not api_key:
            return "Error: No API Key provided"

        try:
            genai.configure(api_key=api_key)
            available_model = 'gemini-1.5-flash' 
            
            model = genai.GenerativeModel(available_model)
            img = PILImage.open(image_path)
            prompt = (
                "Extract the serial number written in marker on this plastic surface. "
                "The format is usually like 'KPRU68-15.00-0089/034'. "
                "Only return the serial number string itself, nothing else."
            )
            response = model.generate_content([prompt, img])
            return response.text.strip()
            
        except Exception as e:
            return f"API Error: {str(e)}"
