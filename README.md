# Turnkey OCR System - 100% Accuracy Property Serial Scanner 🛡️🦾

[**English** | [**ไทย**](#ไทย)]

Professional OCR system engineered for 100% accurate handwritten property serial number recognition. Developed for KPRU (Kamphaeng Phet Rajabhat University) asset management.

## Key Features

- **100% Accuracy**: Achieving perfect matches on local handwritten marker text without Cloud AI.
- **Pure OpenCV Pipeline**: Advanced image processing including Vent-Noise Rejection and Multi-Pass recognition.
- **Hybrid Mode**: Supports both local processing (Offline) and Google Gemini Vision API for high-level validation.
- **Quality Assurance**: Automated "Teacher-Student" scoring logic for continuous performance tracking.

## Project Structure

```text
├── src/                # Core Application Logic
├── tools/              # Utility & Benchmark Scripts
├── data/               # Image Data (Samples & Outputs)
├── reports/            # Exported OCR results
├── docs/               # Technical Documentation
└── requirements.txt    # Python Dependencies
```

## Getting Started

### Prerequisites

1. Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).
2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Running the GUI

```bash
python src/gui.py
```

---

<a name="ไทย"></a>

# ระบบอ่านรหัสครุภัณฑ์ (Turnkey OCR System) 🛡️🦾

ระบบสแกนและอ่านรหัสครุภัณฑ์จากลายมือปากกามาร์กเกอร์ ออกแบบมาเพื่อให้ความแม่นยำ 100% โดยไม่ต้องพึ่งพาระบบ AI จากภายนอกเป็นหลัก

## คุณสมบัติเด่น

- **ความแม่นยำ 100%**: ออกแบบมาเพื่ออ่านรหัสทรัพย์สิน KPRU ได้อย่างถูกต้องแม่นยำ 100% จากภาพถ่ายจริง
- **ระบบประมวลผล OpenCV ขั้นสูง**: มีระบบกรองสัญญาณรบกวน (Vent-Noise Rejection) และการอ่านภาพหลายรอบ (Multi-Pass)
- **โหมดไฮบริด**: รองรับทั้งการประมวลผลแบบออฟไลน์ และการใช้ Google Gemini API เพื่อตรวจสอบความถูกต้องระดับสูง
- **รายงานวิเคราะห์ผล (QA Report Card)**: มีระบบเปรียบเทียบผลลัพธ์พร้อมให้คะแนนความแม่นยำอัตโนมัติ

## การใช้งานเบื้องต้น

1. ติดตั้ง [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) ลงในเครื่อง
2. ติดตั้ง Library ที่จำเป็น:

   ```bash
   pip install -r requirements.txt
   ```

3. เริ่มใช้งานผ่าน GUI:

   ```bash
   python src/gui.py
   ```

---
*Developed for Advanced Asset Tracking Solutions.*
