import subprocess
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

#========================
# CHECK DEPENDENCIES
#========================
def install_basic_libs():
    required_packages = {
        "requests": "requests",
        "cv2": "opencv-python",
        "PIL": "pillow"
    }

    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"✓ Đã có {package_name}")
        except ImportError:
            print(f"→ Đang cài {package_name} ...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name]
            )
            print(f"✓ Cài xong {package_name}")

install_basic_libs()

import cv2
import requests
import base64
import json
import re

# =========================
# CONFIG
# =========================
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "ocr_ai"
IMAGE_FOLDER = "input_images"

result = []
result_lock = threading.Lock()  # 🔐 tránh xung đột khi multi-thread


# =========================
# 1️⃣ XỬ LÝ ẢNH
# =========================
def img_process(image_path):

    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # Giữ 30% phía trên
    cropped = img[0:int(h * 0.3), :]

    ch, cw = cropped.shape[:2]

    max_width = 900
    if cw > max_width:
        ratio = max_width / cw
        cropped = cv2.resize(
            cropped,
            (max_width, int(ch * ratio))
        )

    _, buffer = cv2.imencode(
        ".jpg",
        cropped,
        [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    )

    return base64.b64encode(buffer).decode("utf-8")


# =========================
# 2️⃣ OCR
# =========================
def process_single_image(filename):

    global result

    image_path = os.path.join(IMAGE_FOLDER, filename)
    img_base64 = img_process(image_path)

    if not img_base64:
        return

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Hãy trích xuất thông tin văn bản và trả về JSON."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        "stream": False,
        "max_tokens": 150
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        resp_json = response.json()

        if "choices" not in resp_json:
            print("Response lỗi:", resp_json)
            return

        raw_text = resp_json["choices"][0]["message"]["content"]

        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            print(f"Không tìm thấy JSON hợp lệ: {filename}")
            return

        data = json.loads(match.group())
        data["filename"] = filename

        # 🔐 thêm vào result an toàn
        with result_lock:
            result.append(data)

        print(f"OCR xong: {filename}")

    except Exception as e:
        print(f"Lỗi OCR {filename}: {e}")


# =========================
# 3️⃣ CHUẨN HÓA
# =========================
def result_process():

    global result

    for item in result:

        for key, value in item.items():
            if value in ["null", "", "None"]:
                item[key] = None

        if item.get("ngay_banhanh"):
            if not re.match(r"\d{2}/\d{2}/\d{4}", item["ngay_banhanh"]):
                item["ngay_banhanh"] = None

        if item.get("so_vb"):
            item["so_vb"] = item["so_vb"].strip()

    print("Chuẩn hóa dữ liệu hoàn tất.")


# =========================
# 4️⃣ MAIN
# =========================
def main():

    global result

    start_time = time.time()

    if not os.path.exists(IMAGE_FOLDER):
        print("Thư mục ảnh không tồn tại.")
        return

    image_files = [
        f for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not image_files:
        print("Không có ảnh trong thư mục.")
        return

    print(f"Tìm thấy {len(image_files)} ảnh.")
    print("🚀 Bắt đầu multi-thread (2 luồng)...")

    # 🔥 Multi-thread tại đây
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_single_image, f) for f in image_files]

        for future in as_completed(futures):
            future.result()

    # Sau khi xử lý xong tất cả ảnh
    result_process()

    print(json.dumps(result, indent=2, ensure_ascii=False))

    end_time = time.time()
    print(f"\n⏳ Tổng thời gian xử lý: {end_time - start_time:.2f} giây")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()