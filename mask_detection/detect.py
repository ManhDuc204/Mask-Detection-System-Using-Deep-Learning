"""
detect.py – Script chạy nhận diện khẩu trang độc lập (không cần web server)
Nhấn 'Q' để thoát và xuất báo cáo CSV.
"""

from ultralytics import YOLO
import cv2
import pygame
import time
import os
import pandas as pd

# ── Tạo thư mục lưu ảnh vi phạm ─────────────────────────────────
os.makedirs("violations", exist_ok=True)

# ── Load model AI ─────────────────────────────────────────────────
model = YOLO("best.pt")
print("-> Model AI: ĐÃ TẢI XONG")

# ── Khởi tạo âm thanh ────────────────────────────────────────────
sound_ready = False
try:
    pygame.mixer.init()
    alert_sound = pygame.mixer.Sound("sounds/Beep.mp3")
    sound_ready = True
    print("-> Hệ thống âm thanh: SẴN SÀNG")
except Exception as e:
    print(f"-> Chế độ im lặng: {e}")

# ── Biến quản lý ──────────────────────────────────────────────────
log_data = []
last_beep_time = 0
last_save_time = 0

# ── Camera ───────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("LỖI: Không thể mở camera!")
    exit(1)

print("-> Camera: SẴN SÀNG")
print("-> Nhấn 'Q' để kết thúc và xuất báo cáo.\n")

# ── Vòng lặp chính ───────────────────────────────────────────────
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("LỖI: Không đọc được frame từ camera.")
        break

    # FIX: Bỏ stream=True khi dùng trong vòng lặp thông thường
    # stream=True trả về generator, không phải list → phải dùng next() hoặc for
    # Ở đây dùng list thông thường để đơn giản và ổn định hơn
    results = model.predict(frame, conf=0.6, iou=0.45, verbose=False)

    mask_count = 0
    nomask_count = 0
    violation_detected = False

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            label = model.names[cls].lower()

            if "no" in label:
                color = (0, 0, 255)   # Đỏ = No Mask
                nomask_count += 1
                violation_detected = True
            else:
                color = (0, 255, 0)   # Xanh = Mask
                mask_count += 1

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # ── Xử lý vi phạm ────────────────────────────────────────────
    current_time = time.time()

    if violation_detected:
        # Phát còi (cách nhau ít nhất 2 giây)
        if sound_ready and (current_time - last_beep_time > 2):
            alert_sound.play()
            last_beep_time = current_time

        # Lưu ảnh bằng chứng (cách nhau ít nhất 5 giây)
        if current_time - last_save_time > 5:
            timestamp = time.strftime("%H%M%S-%d%m%Y")
            file_path = f"violations/vi-pham_{timestamp}.jpg"
            cv2.imwrite(file_path, frame)

            log_data.append({
                "Thoi_Gian": time.strftime("%Y-%m-%d %H:%M:%S"),
                "So_Nguoi_Khong_Khau_Trang": nomask_count,
                "So_Nguoi_Co_Khau_Trang": mask_count,
                "Loai_Vi_Pham": "Khong deo khau trang",
                "Anh_Bang_Chung": file_path
            })
            print(f"  [VI PHẠM] Đã lưu: {file_path}")
            last_save_time = current_time

    # ── Vẽ overlay thông tin lên frame ───────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (640, 110), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    status_text = "WARNING: NO MASK" if violation_detected else "STATUS: SAFE"
    status_color = (0, 0, 255) if violation_detected else (0, 255, 0)

    cv2.putText(frame, status_text, (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)
    cv2.putText(frame, f"Mask: {mask_count}", (15, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"No Mask: {nomask_count}", (200, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("He thong Kiem soat Khau trang AI", frame)

    # Thoát khi nhấn 'Q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("\n-> Đang thoát...")
        break

# ── Dọn dẹp & Xuất báo cáo ───────────────────────────────────────
cap.release()
cv2.destroyAllWindows()

if log_data:
    df = pd.DataFrame(log_data)
    output_file = "bao_cao_vi_pham.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n{'='*40}")
    print(f"  HOÀN THÀNH")
    print(f"  Số vi phạm: {len(log_data)}")
    print(f"  Ảnh lưu tại: violations/")
    print(f"  Báo cáo: {output_file}")
    print(f"{'='*40}")
else:
    print("\n-> Không có vi phạm nào được ghi nhận.")

if sound_ready:
    pygame.mixer.quit()