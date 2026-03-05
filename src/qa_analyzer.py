import difflib

class QAAnalyzer:
    def __init__(self):
        pass

    def analyze(self, student_text, teacher_text):
        """
        Compares student output with teacher output and provides feedback.
        """
        s = student_text.upper().replace(' ', '').strip()
        
        # 1. Handle No Teacher Case (offline mode)
        if not teacher_text or "Error" in teacher_text or teacher_text == "ไม่ได้ใช้ API":
            import re
            pattern = r"^KPRU\d{2}-\d{2}\.\d{2}-\d{4}/\d{3}$"
            is_structurally_valid = bool(re.match(pattern, s))
            
            return {
                "score": 100 if is_structurally_valid else (50 if len(s) > 10 else 0),
                "feedback": "ยอดเยี่ยม! ข้อมูลถูกต้องตามรูปแบบ (Offline Validated)" if is_structurally_valid else "ไม่มีข้อมูลคุณครู และรูปแบบยังไม่สมบูรณ์",
                "details": ["ระบบตรวจสอบความถูกต้องเชิงโครงสร้าง (Structural Validation) แทนการเทียบกับ Cloud AI"]
            }

        t = teacher_text.upper().replace(' ', '').strip()

        matcher = difflib.SequenceMatcher(None, s, t)
        ratio = matcher.ratio()
        
        diff = list(difflib.ndiff(s, t))
        
        details = []
        for d in diff:
            if d.startswith('- '):
                details.append(f"ส่วนเกิน (Insertion): พบ '{d[2:]}' ในระบบคุณ แต่ไม่มีในของจริง")
            elif d.startswith('+ '):
                details.append(f"ส่วนที่ขาด (Deletion): ระบบคุณมองข้าม '{d[2:]}' ไป")

        # Pattern-based feedback
        feedback_list = []
        if ratio == 1.0:
            feedback_list.append("ยอดเยี่ยม! ระบบคุณอ่านได้ถูกต้องตรงกับคุณครู 100%")
        elif ratio > 0.8:
            feedback_list.append("เกือบสมบูรณ์แล้ว มีจุดผิดพลาดเล็กน้อยระดับตัวอักษร")
        else:
            feedback_list.append("มีความคลาดเคลื่อนค่อนข้างมาก ควรตรวจสอบขั้นตอน Preprocessing")

        return {
            "score": int(ratio * 100),
            "feedback": " | ".join(feedback_list),
            "details": details
        }

    def get_report_card(self, raw_local, corrected_local, teacher_cloud):
        """
        Generates a comprehensive report card comparing Local vs Cloud.
        """
        raw_analysis = self.analyze(raw_local, teacher_cloud)
        corrected_analysis = self.analyze(corrected_local, teacher_cloud)
        
        report = {
            "base_score": raw_analysis["score"],
            "final_score": corrected_analysis["score"],
            "improvement": corrected_analysis["score"] - raw_analysis["score"],
            "feedback": corrected_analysis["feedback"],
            "technical_details": corrected_analysis["details"]
        }
        
        return report
