import cv2
import numpy as np
import os

class CharacterSegmenter:
    def __init__(self):
        pass

    def segment(self, clean_img, original_img):
        contours, _ = cv2.findContours(clean_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_h, img_w = clean_img.shape
        blobs = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)
            if h < 8 or h > (img_h * 0.4): continue
            if w < 5: continue
            if aspect_ratio < 0.25 or aspect_ratio > 4.0: continue
            
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0: continue
            solidity = cv2.contourArea(cnt) / float(hull_area)
            if solidity < 0.3: continue
            
            blobs.append({'box': (x, y, w, h), 'y_mid': y + h/2, 'area': w*h, 'w': w, 'x': x, 'solid': solidity})
        
        if not blobs:
            return [], []

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
        
        def line_score(group):
            length = len(group)
            if length < 5: return 0
            sorted_g = sorted(group, key=lambda b: b['x'])
            
            # 1. Basic Geometry
            line_w = (sorted_g[-1]['x'] + sorted_g[-1]['box'][2]) - sorted_g[0]['x']
            density = length / float(line_w) if line_w > 0 else 0
            
            # 2. Penalty for extreme crowding (Monitor vents are often very tight)
            crowding_penalty = 1.0
            if density > 0.08: crowding_penalty = 0.05 
            
            # 3. Size Uniformity Check (Real handwriting has variation)
            widths = [b['w'] for b in sorted_g]
            heights = [b['box'][3] for b in sorted_g]
            w_avg, w_std = np.mean(widths), np.std(widths)
            h_avg, h_std = np.mean(heights), np.std(heights)
            
            # If everything is EXACTLY the same size (like vents), it's probably NOT handwriting
            if w_avg > 0 and (w_std / w_avg) < 0.15: crowding_penalty *= 0.1
            if h_avg > 0 and (h_std / h_avg) < 0.10: crowding_penalty *= 0.1
            
            # 4. Gap Stability (Monitor vents have perfectly identical gaps)
            if length > 8:
                gaps = []
                for i in range(len(sorted_g)-1):
                    gap = sorted_g[i+1]['x'] - (sorted_g[i]['x'] + sorted_g[i]['box'][2])
                    gaps.append(max(0, gap))
                gap_avg = np.mean(gaps) if gaps else 0
                gap_std = np.std(gaps) if gaps else 0
                if gap_avg > 0 and (gap_std / gap_avg) < 0.20:
                    crowding_penalty *= 0.05 # Strong rejection of uniform patterns

            a_avg = np.mean([b['area'] for b in sorted_g])
            area_score = a_avg / 50.0
            y_pos = sum([b['y_mid'] for b in group]) / len(group)
            pos_weight = 1.0 + (y_pos / img_h) 
            pattern_bonus = 2.0 if 12 <= length <= 25 else 0.5
            
            return length * area_score * pos_weight * pattern_bonus * crowding_penalty

        scored_lines = []
        for g in line_groups:
            score = line_score(g)
            if score > 0:
                scored_lines.append((score, g))
        
        if not scored_lines:
             return [], []
        
        _, best_line = max(scored_lines, key=lambda x: x[0])
        
        boxes = [b['box'] for b in best_line]
        min_x = min([box[0] for box in boxes])
        max_x = max([box[0] + box[2] for box in boxes])
        min_y = min([box[1] for box in boxes])
        max_y = max([box[1] + box[3] for box in boxes])
        
        full_line_box = (min_x, min_y, max_x - min_x, max_y - min_y)
        x, y, w, h = full_line_box
        
        pad_x, pad_y = 30, 25 
        x_p = max(0, x - pad_x)
        y_p = max(0, y - pad_y)
        w_p = min(img_w - x_p, w + pad_x * 2)
        h_p = min(img_h - y_p, h + pad_y * 2)
        
        line_roi_bin = clean_img[y_p:y_p+h_p, x_p:x_p+w_p].copy()
        gray_orig = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
        line_roi_gray = gray_orig[y_p:y_p+h_p, x_p:x_p+w_p].copy()
        
        target_h = 120
        def normalize_roi(roi, is_binary):
            scale = target_h / roi.shape[0]
            roi_res = cv2.resize(roi, (int(roi.shape[1] * scale), target_h), interpolation=cv2.INTER_CUBIC)
            if is_binary:
                roi_res = cv2.bitwise_not(roi_res)
                _, roi_res = cv2.threshold(roi_res, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            border = 40
            roi_res = cv2.copyMakeBorder(roi_res, border, border, border, border, 
                                            cv2.BORDER_CONSTANT, value=255 if is_binary else int(np.mean(roi_res)))
            return roi_res

        line_bin_final = normalize_roi(line_roi_bin, True)
        line_gray_final = normalize_roi(line_roi_gray, False)
        
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
