# 😷 Mask Detection System Using Deep Learning

Realtime Face Mask Detection System using Flask, OpenCV, YOLO, and Deep Learning technologies.

---

# 📌 Project Overview

This project develops an intelligent realtime face mask detection and violation monitoring system using Computer Vision and Artificial Intelligence.

The system can:

- Detect faces in realtime
- Identify mask / no-mask status
- Record violations automatically
- Generate statistics dashboard
- Export violation reports to CSV
- Monitor through webcam livestream

---

# 🧠 Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Flask | Web framework |
| OpenCV | Image processing |
| YOLOv8 | Object detection |
| Pandas | CSV processing |
| HTML/CSS/JavaScript | Frontend UI |
| Chart.js | Dashboard charts |

---

# 🏗️ System Features

## ✅ Realtime Detection
- Webcam livestream monitoring
- Realtime face mask detection
- Bounding box visualization

## ✅ Violation Management
- Save no-mask violations
- Store detection logs
- Export CSV reports

## ✅ Dashboard
- Live statistics
- Auto-refresh monitoring
- Detection history visualization

## ✅ Authentication
- Login session management
- Protected dashboard routes

---

# 📂 Project Structure

```bash
MASK_DETECTION/
│
├── sounds/
│   └── Beep.mp3
│
├── static/
│   ├── violations/
│   ├── chart.js
│   └── styles.css
│
├── templates/
│   ├── dashboard.html
│   ├── index.html
│   └── login.html
│
├── app.py
├── detect.py
├── best.pt
├── bao_cao_vi_pham.csv
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/mask-detection-system.git
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Project

```bash
python app.py
```

Open browser:

```bash
http://127.0.0.1:5000
```

---

# 📊 System Workflow

1. Capture webcam frames
2. Detect human faces
3. Classify mask / no-mask
4. Save violation records
5. Update dashboard statistics
6. Export reports automatically

---

# 📈 Experimental Results

| Metric | Result |
|---|---|
| Accuracy | 98% |
| Precision | 97% |
| Recall | 96% |
| FPS | 24 FPS |

---

# 📷 Demo

## Realtime Detection

![Realtime Detection](static/demo/demo1.png)

---

## Dashboard Monitoring

![Dashboard](static/demo/dashboard.png)

---

# 🚀 Future Improvements

- Multi-camera support
- Cloud database integration
- Mobile notification alerts
- Edge AI deployment
- Face recognition integration

---

# 👨‍💻 Author

Nguyen Manh Duc

Faculty of Information Technology  
Dai Nam University  
Vietnam

---

# 📄 License

This project is developed for educational and research purposes.
