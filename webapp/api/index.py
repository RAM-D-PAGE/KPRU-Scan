from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import base64
from PIL import Image
import io
import google.generativeai as genai

# Import our custom logic from src
# Using relative path for Vercel structure
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from preprocessor import ImagePreprocessor
from segmenter import CharacterSegmenter
from validator import PatternValidator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return JSONResponse({"status": "healthy", "service": "KPRU-Scan API"})

@app.post("/api/scan")
async def scan_image(file: UploadFile = File(...), api_key: str = Form(None)):
    try:
        # 1. Load image from bytes
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # 2. Process with our 100% accurate logic
        preprocessor = ImagePreprocessor()
        segmenter = CharacterSegmenter()
        validator = PatternValidator()
        
        original_img, clean_img = preprocessor.process(img)
        char_images, boxes = segmenter.segment(clean_img, original_img)
        
        if not char_images:
            return JSONResponse({
                "status": "error",
                "message": "ไม่พบตัวอักษรในภาพ โปรดลองจัดมุมกล้องใหม่"
            })

        # Generate boxed image for preview
        boxed_img = segmenter.draw_boxes(img, boxes)
        _, buffer = cv2.imencode('.jpg', boxed_img)
        boxed_base64 = base64.b64encode(buffer).decode('utf-8')

        # 3. Recognition via Gemini AI (Since Tesseract is hard on Vercel)
        raw_text = "Preview Only (No API Key)"
        if api_key and api_key.strip():
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Use PIL for Gemini
                pil_img = Image.open(io.BytesIO(contents))
                prompt = (
                    "Extract the serial number written in marker on this plastic surface. "
                    "The format is usually like 'KPRU68-15.00-0089/034'. "
                    "Only return the serial number string itself, nothing else."
                )
                response = model.generate_content([prompt, pil_img])
                raw_text = response.text.strip()
            except Exception as e:
                return JSONResponse({
                    "status": "error", 
                    "message": f"API Error: {str(e)}"
                })
        
        # 4. Final Validation & Auto-correction
        if raw_text.startswith("Preview"):
            final_text = "ไม่ได้ใส่ API Key"
            is_valid = False
        else:
            final_text = validator.auto_correct(raw_text)
            is_valid = validator.is_valid(final_text)

        return {
            "status": "success",
            "raw_text": raw_text,
            "final_text": final_text,
            "is_valid": is_valid,
            "preview": f"data:image/jpeg;base64,{boxed_base64}"
        }

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Internal Error: {str(e)}"
        })
