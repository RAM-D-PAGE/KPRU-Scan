const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const btnCamera = document.getElementById('btn-camera');
const btnSnap = document.getElementById('btn-snap');
const btnUpload = document.getElementById('btn-upload');
const fileInput = document.getElementById('file-input');
const apiKeyInput = document.getElementById('api-key');
const resultsSection = document.getElementById('results-section');
const statusBadge = document.getElementById('status-badge');
const finalText = document.getElementById('final-text');
const roiPreview = document.getElementById('roi-preview');
const loadingOverlay = document.getElementById('loading-overlay');

let stream = null;

// 1. Camera Handling
btnCamera.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" } // Prefer back camera
        });
        video.srcObject = stream;
        video.style.display = 'block';
        document.getElementById('static-preview').style.display = 'none';
        document.getElementById('placeholder').style.display = 'none';
        btnSnap.style.display = 'block';
        btnCamera.textContent = '🔄 สลับกล้อง';
    } catch (err) {
        alert("ไม่สามารถเข้าถึงกล้องได้: " + err);
    }
});

// 2. Upload Handling
btnUpload.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            const preview = document.getElementById('static-preview');
            preview.src = event.target.result;
            preview.style.display = 'block';
            video.style.display = 'none';
            document.getElementById('placeholder').style.display = 'none';
            btnSnap.style.display = 'block';
            // Stop camera if running
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
        reader.readAsDataURL(file);
    }
});

// 3. Scan & API Execution
btnSnap.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();

    loadingOverlay.style.display = 'flex';
    resultsSection.style.display = 'none';

    let blob;
    if (video.style.display !== 'none') {
        // Capture from video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9));
    } else {
        // Use static preview
        const response = await fetch(document.getElementById('static-preview').src);
        blob = await response.blob();
    }

    const formData = new FormData();
    formData.append('file', blob, 'scan.jpg');
    formData.append('api_key', apiKey);

    try {
        const apiUrl = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
            ? 'http://127.0.0.1:8000/api/scan'
            : '/api/scan';

        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.status === 'success') {
            finalText.textContent = result.final_text;
            roiPreview.src = result.preview;
            statusBadge.textContent = result.is_valid ? "✅ รูปแบบถูกต้อง" : "⚠️ รูปแบบคลาดเคลื่อน";
            statusBadge.style.background = result.is_valid ? "#22c55e" : "#eab308";
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            alert("Error: " + result.message);
        }
    } catch (err) {
        alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    } finally {
        loadingOverlay.style.display = 'none';
    }
});

// Copy to Clipboard
document.getElementById('btn-copy').addEventListener('click', () => {
    navigator.clipboard.writeText(finalText.textContent);
    alert("คัดลอกรหัสแล้ว!");
});
