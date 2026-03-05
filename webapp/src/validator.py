import re

class PatternValidator:
    def __init__(self):
        self.pattern = r"^KPRU\d{2}-\d{2}\.\d{2}-\d{4}/\d{3}$"
        
    def auto_correct(self, raw_text):
        raw_text = raw_text.upper().replace(' ', '').strip()
        if raw_text.startswith("NS"):
            if "-" in raw_text:
                raw_text = raw_text[raw_text.find("-")+1:]
            else:
                raw_text = raw_text[2:]
        
        text = raw_text.replace(':', '-').replace(';', '-').replace(',', '.')
        slash_idx = text.rfind('/')
        s5_raw = text[slash_idx+1:] if slash_idx != -1 else ""
        main_part = text[:slash_idx] if slash_idx != -1 else text
        
        parts = re.split(r'[-\.]', main_part)
        parts = [p for p in parts if p]
        
        s1_raw = parts[0] if len(parts) >= 1 else ""
        s1_digits = self._extract_digits(s1_raw, 2, from_right=True)
        s2 = self._extract_digits(parts[1], 2) if len(parts) >= 2 else "00"
        s3 = self._extract_digits(parts[2], 2) if len(parts) >= 3 else "00"
        s4 = self._extract_digits(parts[3], 4) if len(parts) >= 4 else "0000"
        s5 = self._extract_digits(s5_raw, 3)
            
        if s1_digits == "65" and ("8" in s1_raw or "S" in s1_raw or "B" in s1_raw):
            s1_digits = "68"

        return f"KPRU{s1_digits}-{s2}.{s3}-{s4}/{s5}"

    def _extract_digits(self, segment, n, from_right=False):
        digits = []
        for char in segment:
            d = self._to_digit(char)
            if d.isdigit():
                digits.append(d)
        if from_right:
            res = "".join(digits[-n:]) if digits else ""
        else:
            res = "".join(digits[:n]) if digits else ""
        return res.zfill(n)

    def _to_digit(self, char):
        if char.isdigit(): return char
        mapping = {
            'O': '0', 'D': '0', 'Q': '0', 'U': '0', '(': '0', 'G': '6', '@': '0', 'C': '0',
            'I': '1', 'L': '1', 'T': '1', '|': '1', '!': '1', '[': '1', 'J': '1',
            'Z': '2', 'S': '8', '$': '8', 'E': '3', 'H': '4', 'A': '4', 'B': '8',
            'P': '9', 'V': '0', 'K': 'K', 'R': 'R', 'U': 'U'
        }
        return mapping.get(char, "")

    def is_valid(self, text):
        return bool(re.match(self.pattern, text))
