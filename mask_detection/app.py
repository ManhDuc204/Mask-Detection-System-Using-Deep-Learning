from flask import (
    Flask,
    render_template,
    Response,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify
)

from ultralytics import YOLO

import cv2
import os
import time
import pandas as pd
import pygame
import threading

app = Flask(__name__)
app.secret_key = "mask_secret_key_2024"

model = YOLO("best.pt")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

sound_ready = False
try:
    pygame.mixer.init()
    alert_sound = pygame.mixer.Sound("sounds/Beep.mp3")
    sound_ready = True
    print("-> Hệ thống âm thanh: SẴN SÀNG")
except Exception as e:
    print(f"-> Chế độ im lặng: {e}")

# ── Thư mục lưu ảnh vi phạm ─────────────────────────────────────
os.makedirs("static/violations", exist_ok=True)

# ── Thông tin đăng nhập ─────────────────────────────────────────
USERNAME = "admin"
PASSWORD = "123456"

# ── Dữ liệu toàn cục (thread-safe) ──────────────────────────────
lock = threading.Lock()
logs = []
last_beep = 0
last_save = 0

frame_mask_count = 0
frame_nomask_count = 0
total_violations = 0  # Tổng lượt vi phạm được ghi nhận (mỗi 5s/lần)


def generate_frames():
    global last_beep, last_save
    global frame_mask_count, frame_nomask_count, total_violations

    while True:
        success, frame = cap.read()
        if not success:
            # Nếu camera lỗi, gửi frame trống để tránh crash
            blank = 255 * __import__('numpy').ones((480, 640, 3), dtype='uint8')
            ret, buffer = cv2.imencode(".jpg", blank)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes() +
                b"\r\n"
            )
            time.sleep(0.1)
            continue

        results = model.predict(frame, conf=0.6, verbose=False)

        mask_count = 0
        nomask_count = 0
        violation = False

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                label = model.names[cls].lower()

                if "no" in label:
                    color = (0, 0, 255)
                    nomask_count += 1
                    violation = True
                else:
                    color = (0, 255, 0)
                    mask_count += 1

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                )

        # FIX: Cập nhật count theo frame hiện tại (không cộng dồn)
        with lock:
            frame_mask_count = mask_count
            frame_nomask_count = nomask_count

        current_time = time.time()

        if violation:
            # Phát âm thanh (cách nhau ít nhất 2 giây)
            if sound_ready and (current_time - last_beep > 2):
                alert_sound.play()
                last_beep = current_time

            # Lưu ảnh vi phạm (cách nhau ít nhất 5 giây)
            if current_time - last_save > 5:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}.jpg"
                filepath = os.path.join("static/violations", filename)
                cv2.imwrite(filepath, frame)

                with lock:
                    total_violations += 1
                    logs.append({
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "NO MASK",
                        "image": filename
                    })

                last_save = current_time

        # Overlay status bar
        status = "WARNING: NO MASK" if violation else "STATUS: SAFE"
        status_color = (0, 0, 255) if violation else (0, 255, 0)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (640, 120), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        cv2.putText(frame, status, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 3)
        cv2.putText(frame, f"Mask: {mask_count}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"No Mask: {nomask_count}", (220, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )


# ── Routes ───────────────────────────────────────────────────────

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Sai tên đăng nhập hoặc mật khẩu!"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """FIX: Thêm route logout bị thiếu"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    with lock:
        current_logs = list(logs)
        current_mask = frame_mask_count
        current_nomask = frame_nomask_count

    return render_template(
        "dashboard.html",
        total_mask=current_mask,
        total_nomask=current_nomask,
        total_violations=total_violations,
        logs=current_logs
    )


@app.route("/video")
def video():
    if "user" not in session:
        return redirect(url_for("login"))

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/stats")
def api_stats():
    """FIX: API endpoint cho live stats (dashboard auto-refresh)"""
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401

    with lock:
        return jsonify({
            "mask": frame_mask_count,
            "nomask": frame_nomask_count,
            "total_violations": total_violations,
            "logs": list(logs)[-10:]  # 10 log gần nhất
        })


@app.route("/download")
def download():
    if "user" not in session:
        return redirect(url_for("login"))

    with lock:
        current_logs = list(logs)

    if not current_logs:
        # FIX: Trả về CSV rỗng thay vì crash khi logs trống
        df = pd.DataFrame(columns=["time", "status", "image"])
    else:
        df = pd.DataFrame(current_logs)

    file_name = "report.csv"
    df.to_csv(file_name, index=False, encoding="utf-8-sig")

    return send_file(file_name, as_attachment=True)


# ── Khởi động ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("  MASK DETECTION WEB SYSTEM")
    print("  URL:      http://localhost:5000")
    print("  Username: admin")
    print("  Password: 123456")
    print("=" * 40)
    app.run(debug=True, threaded=True)