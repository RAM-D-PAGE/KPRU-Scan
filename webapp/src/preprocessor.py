import cv2
import numpy as np

class ImagePreprocessor:
    def __init__(self):
        pass

    def process(self, img):
        """Modified to accept image object directly for Web API"""
        if img is None:
            raise ValueError("Input image is None")
            
        # Resize to a reasonable width
        width = img.shape[1]
        if width > 1200:
            scale = 1200 / width
            img = cv2.resize(img, (1200, int(img.shape[0] * scale)))
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        kernel_tophat = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
        tophat = cv2.morphologyEx(enhanced, cv2.MORPH_TOPHAT, kernel_tophat)
        
        smoothed = cv2.bilateralFilter(tophat, 11, 75, 75)
        
        thresh = cv2.adaptiveThreshold(smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 21, -8)
        
        kernel_noise = np.ones((2,2), np.uint8)
        clean_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_noise, iterations=1)
        
        kernel_close = np.ones((2, 2), np.uint8)
        clean_img = cv2.morphologyEx(clean_img, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        
        return img, clean_img
