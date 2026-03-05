import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import cv2
import sys

# Ensure src is in the path for relative imports if run as script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# นำเข้าฟังก์ชันแสกนที่เราเขียนไว้ใน main.py มาใช้
import main
from main import process_image

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ระบบอ่านรหัสครุภัณฑ์ (Turnkey OCR System)")
        self.root.geometry("1000x800")
        self.root.config(bg="#f0f0f0")
        
        # ตัวแปรเก็บที่อยู่ภาพที่เลือก
        self.current_image_path = None
        
        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", pady=15)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, text="โปรแกรมสแกนหมายเลขซีเรียลจากภาพ (Hybrid Mode)", 
                               font=("Kanit", 16, "bold"), bg="#2c3e50", fg="white")
        title_label.pack()

        # Body Frame
        body_frame = tk.Frame(self.root, bg="#f0f0f0")
        body_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left Panel (Image Display)
        self.left_panel = tk.Frame(body_frame, bg="white", relief="groove", borderwidth=2, width=550, height=500)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        self.left_panel.pack_propagate(False)
        
        self.image_label = tk.Label(self.left_panel, text="คลิก 'เลือกรูปภาพ' ด้านขวา เพื่อดูภาพ", 
                                    font=("Kanit", 10), bg="white", fg="gray")
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Right Panel (Controls & Results)
        right_panel = tk.Frame(body_frame, bg="#f0f0f0", width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 1. API Config
        api_frame = tk.LabelFrame(right_panel, text="🔑 ตั้งค่า API (Cloud AI)", font=("Kanit", 10, "bold"), bg="#f0f0f0", pady=5, padx=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(api_frame, text="Google Gemini API Key:", font=("Kanit", 8), bg="#f0f0f0").pack(anchor=tk.W)
        
        key_input_frame = tk.Frame(api_frame, bg="#f0f0f0")
        key_input_frame.pack(fill=tk.X, pady=5)
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = tk.Entry(key_input_frame, textvariable=self.api_key_var, font=("Consolas", 10), show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add a show/hide toggle
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_btn = tk.Checkbutton(key_input_frame, text="แสดง", variable=self.show_key_var, 
                                           command=self.toggle_api_visibility, font=("Kanit", 8), bg="#f0f0f0")
        self.show_key_btn.pack(side=tk.RIGHT, padx=5)

        # Enable Copy/Paste/Select All for Windows
        self.api_key_entry.bind("<Control-a>", lambda e: self.api_key_entry.select_range(0, tk.END) or "break")
        self.api_key_entry.bind("<Control-c>", lambda e: self.root.clipboard_append(self.api_key_entry.get()) or "break")
        self.api_key_entry.bind("<Control-v>", lambda e: self.api_key_entry.insert(tk.INSERT, self.root.clipboard_get()) or "break")

        # 2. Control Buttons
        btn_frame = tk.LabelFrame(right_panel, text="เครื่องมือ (Controls)", font=("Kanit", 10, "bold"), bg="#f0f0f0", pady=10, padx=10)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_btn = tk.Button(btn_frame, text="📁 เลือกรูปภาพ (Select Image)", 
                                    font=("Kanit", 10), bg="#3498db", fg="white", 
                                    command=self.select_image)
        self.select_btn.pack(fill=tk.X, pady=5)
        
        self.scan_btn = tk.Button(btn_frame, text="🔍 สแกนรหัส (Scan Code)", 
                                  font=("Kanit", 12, "bold"), bg="#2ecc71", fg="white", 
                                  command=self.start_scan, state=tk.DISABLED)
        self.scan_btn.pack(fill=tk.X, pady=5)

        self.save_report_btn = tk.Button(btn_frame, text="💾 บันทึกรายงาน (Save Report)", 
                                         font=("Kanit", 10), bg="#95a5a6", fg="white", 
                                         command=self.save_report_to_file, state=tk.DISABLED)
        self.save_report_btn.pack(fill=tk.X, pady=5)

        # 3. Results Comparison
        res_frame = tk.LabelFrame(right_panel, text="ผลลัพธ์การสแกน (Results Comparison)", font=("Kanit", 10, "bold"), bg="#f0f0f0", pady=10, padx=10)
        res_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(res_frame, text="1. ข้อความดิบ (Local AI):", font=("Kanit", 9), bg="#f0f0f0").pack(anchor=tk.W)
        self.raw_text_var = tk.StringVar(value="-")
        tk.Entry(res_frame, textvariable=self.raw_text_var, state='readonly', font=("Consolas", 10)).pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(res_frame, text="2. รหัสที่แก้ไขแล้ว (Local Corrected):", font=("Kanit", 9, "bold"), bg="#f0f0f0", fg="blue").pack(anchor=tk.W)
        self.final_text_var = tk.StringVar(value="-")
        tk.Entry(res_frame, textvariable=self.final_text_var, state='readonly', font=("Consolas", 11, "bold"), fg="black").pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(res_frame, text="3. ผลลัพธ์จาก Cloud AI (คุณครู):", font=("Kanit", 9, "bold"), bg="#f0f0f0", fg="#8e44ad").pack(anchor=tk.W)
        self.api_text_var = tk.StringVar(value="-")
        tk.Entry(res_frame, textvariable=self.api_text_var, state='readonly', font=("Consolas", 11, "bold"), fg="#8e44ad").pack(fill=tk.X, pady=(0, 5))

        # 4. AI Tutor & QA Report
        qa_frame = tk.LabelFrame(right_panel, text="🎓 รายงานวิเคราะห์ (AI Tutor Report Card)", font=("Kanit", 10, "bold"), bg="#f0f0f0", pady=10, padx=10)
        qa_frame.pack(fill=tk.BOTH, expand=True)
        
        self.score_label = tk.Label(qa_frame, text="คะแนนความแม่นยำ: - %", font=("Kanit", 10, "bold"), bg="#f0f0f0")
        self.score_label.pack(anchor=tk.W)
        
        tk.Label(qa_frame, text="คำแนะนำจาก AI:", font=("Kanit", 9, "bold"), bg="#f0f0f0").pack(anchor=tk.W, pady=(5,0))
        self.feedback_text = tk.Text(qa_frame, height=4, font=("Kanit", 9), bg="#e8f6f3", relief="flat")
        self.feedback_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.feedback_text.config(state=tk.DISABLED)

    def toggle_api_visibility(self):
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์รูปภาพรหัส",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            self.current_image_path = file_path
            self.show_image(file_path)
            self.scan_btn.config(state=tk.NORMAL)
            self.reset_results()

    def show_image(self, img_path):
        try:
            # OpenCV color to RGB for PIL
            img_cv = cv2.imread(img_path)
            if img_cv is None: return
            
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            # Resize image to fit the panel
            panel_w, panel_h = 530, 480
            img_pil.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)
            
            self.tk_image = ImageTk.PhotoImage(img_pil)
            self.image_label.config(image=self.tk_image, text="")
        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถเปิดรูปภาพได้: {e}")

    def reset_results(self):
        self.raw_text_var.set("-")
        self.final_text_var.set("-")
        self.api_text_var.set("-")
        self.score_label.config(text="คะแนนความแม่นยำ: - %", fg="black")
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete('1.0', tk.END)
        self.feedback_text.config(state=tk.DISABLED)

    def start_scan(self):
        if not self.current_image_path:
            return
            
        api_key = self.api_key_var.get()
        self.score_label.config(text="กำลังวิเคราะห์...", fg="blue")
        self.root.update() 
        
        # เรียกใช้ฟังก์ชันจาก main.py
        result = process_image(self.current_image_path, api_key=api_key)
        
        if result["status"] == "error":
            messagebox.showerror("Scan Error", result["message"])
            return
            
        # Update Results on UI
        self.raw_text_var.set(result.get("raw_text", ""))
        self.final_text_var.set(result.get("final_text", ""))
        self.api_text_var.set(result.get("api_text", ""))
        
        # Update QA Report Card
        qa = result.get("qa_report")
        if qa:
            score = qa["score"] if "score" in qa else qa["final_score"]
            self.score_label.config(text=f"คะแนนความแม่นยำ: {score}%", fg="green" if score > 80 else "orange" if score > 50 else "red")
            
            self.feedback_text.config(state=tk.NORMAL)
            self.feedback_text.delete('1.0', tk.END)
            self.feedback_text.insert(tk.END, qa.get("feedback", ""))
            
            if qa.get("technical_details"):
                self.feedback_text.insert(tk.END, "\n\nรายละเอียดเชิงลึก:\n")
                for detail in qa["technical_details"]:
                    self.feedback_text.insert(tk.END, f"- {detail}\n")
            
            self.feedback_text.config(state=tk.DISABLED)

        # Show boxed image
        if result.get("boxed_image_path"):
            self.show_image(result["boxed_image_path"])

        # Enable Saving Report
        self.last_result = result
        self.save_report_btn.config(state=tk.NORMAL)

    def save_report_to_file(self):
        if not hasattr(self, 'last_result'):
            return
            
        res = self.last_result
        qa = res.get("qa_report", {})
        
        # Updated default save directory
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
        os.makedirs(default_dir, exist_ok=True)

        file_path = filedialog.asksaveasfilename(
            initialdir=default_dir,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"OCR_Report_{os.path.basename(self.current_image_path if self.current_image_path else 'scan')}.txt"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=== OCR ANALYSIS REPORT ===\n")
                f.write(f"Image Source: {self.current_image_path}\n")
                f.write(f"Status: {'PASS' if res.get('is_correct') else 'FAIL'}\n")
                f.write("-" * 30 + "\n")
                f.write(f"1. Raw Local OCR: {res.get('raw_text')}\n")
                f.write(f"2. Corrected OCR: {res.get('final_text')}\n")
                f.write(f"3. Teacher (Cloud): {res.get('api_text')}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Accuracy Score: {qa.get('score' if 'score' in qa else 'final_score', 0)}%\n")
                f.write(f"Correction Boost: +{qa.get('improvement', 0)} pts\n\n")
                f.write(f"AI Feedback:\n{qa.get('feedback', '')}\n\n")
                f.write("Technical Details:\n")
                for d in qa.get("technical_details", []):
                    f.write(f"- {d}\n")
                f.write("-" * 30 + "\n")
                f.write("Generated by Turnkey OCR System\n")
            
            messagebox.showinfo("Success", f"บันทึกรายงานเรียบร้อยแล้วที่:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถบันทึกไฟล์ได้: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
