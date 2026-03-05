import cv2
import numpy as np

class ImagePreprocessor:
    def __init__(self):
        pass

    def process(self, image_path):
        # 1. Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Cannot find image at {image_path}")
            
        # Resize to a reasonable width while maintaining aspect ratio
        width = img.shape[1]
        if width > 1200:
            scale = 1200 / width
            img = cv2.resize(img, (1200, int(img.shape[0] * scale)))
        
        # 2. Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Enhances local contrast to fight glare and inconsistent lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 4. Top-Hat Transform: Highlights bright marker ink on dark background
        # Helps remove the rough surface texture of the plastic
        kernel_tophat = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
        tophat = cv2.morphologyEx(enhanced, cv2.MORPH_TOPHAT, kernel_tophat)
        
        # 5. Bilateral Filter: Smooths remaining noise while keeping text edges sharp
        smoothed = cv2.bilateralFilter(tophat, 11, 75, 75)
        
        # 6. Adaptive Thresholding - Gaussian C
        thresh = cv2.adaptiveThreshold(smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 21, -8)
        
        # 7. Denoising & Fine Closing
        kernel_noise = np.ones((2,2), np.uint8)
        clean_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_noise, iterations=1)
        
        # 8. Stroke Dilation: Subtle thickening (Can be tweaked for different markers)
        # kernel_dilate = np.ones((2, 2), np.uint8)
        # clean_img = cv2.dilate(clean_img, kernel_dilate, iterations=1)
        
        kernel_close = np.ones((2, 2), np.uint8)
        clean_img = cv2.morphologyEx(clean_img, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        
        return img, clean_img
