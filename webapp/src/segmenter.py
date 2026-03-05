import cv2
import numpy as np
import os

class CharacterSegmenter:
    def __init__(self):
        pass

    def segment(self, clean_img, original_img):
        char_images = []
        bounding_boxes = []
        
        # 1. Find all contours
        contours, _ = cv2.findContours(clean_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_h, img_w = clean_img.shape
        blobs = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)
            
            # --- AGGRESSIVE SLIVER REJECTION ---
            # Handwriting on monitors (KPRU) is usually 'boxy'. 
            # Vents are very thin slits.
            if h < 8 or h > (img_h * 0.4): continue
            if w < 5: continue # Characters aren't 1-2 pixels wide
            if aspect_ratio < 0.25 or aspect_ratio > 4.0: continue # Vents are usually < 0.2
            
            # Solidness check: Characters are more complex than simple slits
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0: continue
            solidity = cv2.contourArea(cnt) / float(hull_area)
            if solidity < 0.3: continue # Noise/Dust
            
            blobs.append({'box': (x, y, w, h), 'y_mid': y + h/2, 'area': w*h, 'w': w, 'x': x, 'solid': solidity})
        
        if not blobs:
            return [], []

        # 2. Robust Line Selection
        line_groups = []
        sorted_blobs = sorted(blobs, key=lambda b: b['x'])
        
        for b in sorted_blobs:
            added = False
            for group in line_groups:
                group_y_avg = sum([gb['y_mid'] for gb in group]) / len(group)
                group_h_avg = sum([gb['box'][3] for gb in group]) / len(group)
                if abs(b['y_mid'] - group_y_avg) < (group_h_avg * 0.6):
                    group.append(b)
                    added = True
                    break
            if not added:
                line_groups.append([b])
        
        # 3. Find the Serial Number Line
        def line_score(group):
            length = len(group)
            if length < 5: return 0
            
            sorted_g = sorted(group, key=lambda b: b['x'])
            widths = [b['w'] for b in sorted_g]
            heights = [b['box'][3] for b in sorted_g]
            areas = [b['area'] for b in sorted_g]
            
            w_avg, w_std = np.mean(widths), np.std(widths)
            h_avg, h_std = np.mean(heights), np.std(heights)
            a_avg = np.mean(areas)
            
            # --- VENT REJECTION (ENHANCED) ---
            penalty = 1.0
            
            # 1. Height Check: Vents are usually extremely short compared to KPRU text
            # Typical KPRU handwriting on a 1200px width image is 40-70px tall. Vents are < 15px.
            if h_avg < 20: penalty *= 0.01 
            
            # 2. Density Check: Vents are super packed (thin slits)
            line_w = (sorted_g[-1]['x'] + sorted_g[-1]['box'][2]) - sorted_g[0]['x']
            density = length / float(line_w) if line_w > 0 else 0
            if density > 0.09: penalty *= 0.02 
            
            # 3. Machine Uniformity: Vents have identical widths/heights
            if w_avg > 0 and (w_std / w_avg) < 0.12: penalty *= 0.1
            if h_avg > 0 and (h_std / h_avg) < 0.08: penalty *= 0.1
            
            # 4. Gap Stability: Vents have identical robotic gaps
            if length > 8:
                gaps = []
                for i in range(len(sorted_g)-1):
                    gap = sorted_g[i+1]['x'] - (sorted_g[i]['x'] + sorted_g[i]['box'][2])
                    gaps.append(max(0, gap))
                if gaps:
                    gap_avg = np.mean(gaps)
                    gap_std = np.std(gaps)
                    if gap_avg > 0 and (gap_std / gap_avg) < 0.18:
                        penalty *= 0.01

            # 5. Strength Signals
            # Big bold handwriting has a much higher area than thin vents.
            area_score = (a_avg / 30.0) ** 1.5 
            y_pos = sum([b['y_mid'] for b in group]) / len(group)
            pos_weight = 1.0 + (y_pos / img_h) 
            pattern_bonus = 3.0 if 15 <= length <= 25 else 1.0
            
            return length * area_score * pos_weight * pattern_bonus * penalty

        scored_lines = []
        for g in line_groups:
            score = line_score(g)
            if score > 0:
                scored_lines.append((score, g))
        
        if not scored_lines:
             return [], []
        
        # Pick the line with the highest technical score
        best_score, best_line = max(scored_lines, key=lambda x: x[0])
        
        # 4. Create the final Line ROI with tight padding
        boxes = [b['box'] for b in best_line]
        min_x = min([box[0] for box in boxes])
        max_x = max([box[0] + box[2] for box in boxes])
        min_y = min([box[1] for box in boxes])
        max_y = max([box[1] + box[3] for box in boxes])
        
        full_line_box = (min_x, min_y, max_x - min_x, max_y - min_y)
        x, y, w, h = full_line_box
        
        # 5. Extract and Normalize with White Padding
        # Padding is CRITICAL. Tesseract fails if characters touch the edges.
        pad_x, pad_y = 30, 25 
        x_p = max(0, x - pad_x)
        y_p = max(0, y - pad_y)
        w_p = min(img_w - x_p, w + pad_x * 2)
        h_p = min(img_h - y_p, h + pad_y * 2)
        
        # Binary ROI
        line_roi_bin = clean_img[y_p:y_p+h_p, x_p:x_p+w_p].copy()
        # Gray ROI (from original image for better details)
        gray_orig = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
        line_roi_gray = gray_orig[y_p:y_p+h_p, x_p:x_p+w_p].copy()
        
        # Standardize height for Tesseract
        target_h = 120
        
        def normalize_roi(roi, is_binary):
            scale = target_h / roi.shape[0]
            roi_res = cv2.resize(roi, (int(roi.shape[1] * scale), target_h), interpolation=cv2.INTER_CUBIC)
            if is_binary:
                roi_res = cv2.bitwise_not(roi_res)
                _, roi_res = cv2.threshold(roi_res, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # Add substantial WHITE boarder
            border = 40
            roi_res = cv2.copyMakeBorder(roi_res, border, border, border, border, 
                                            cv2.BORDER_CONSTANT, value=255 if is_binary else int(np.mean(roi_res)))
            return roi_res

        line_bin_final = normalize_roi(line_roi_bin, True)
        line_gray_final = normalize_roi(line_roi_gray, False)
        
        # Return as a dictionary for flexibility
        line_data = {
            "binary": line_bin_final,
            "gray": line_gray_final,
            "box": full_line_box
        }
            
        return [line_data], [full_line_box]
    
    def draw_boxes(self, img, boxes):
        display_img = img.copy()
        for (x, y, w, h) in boxes:
            cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        return display_img
