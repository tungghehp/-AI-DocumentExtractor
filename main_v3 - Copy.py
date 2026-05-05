import subprocess
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import cv2
import base64
import json
import re
import numpy as np


# =========================
# CONFIG
# =========================
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "ocr_ai"
IMAGE_FOLDER = "output"
MAX_WORKERS = 2

result = []

# Tạo session dùng chung để reuse connection
session = requests.Session()


# =========================
# 1️⃣ XỬ LÝ ẢNH
# =========================
def img_process(image_path):
    
    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # Chỉ cắt 1/3 phía trên
    cropped = img[0:int(h / 3), :]

    # Encode giữ nguyên chất lượng cao
    _, buffer = cv2.imencode(
        ".jpg",
        cropped,
        [int(cv2.IMWRITE_JPEG_QUALITY), 75]
    )

    return base64.b64encode(buffer).decode("utf-8")


# =========================
# 2️⃣ OCR
# =========================
def process_single_image(data):

    filename, img_base64 = data

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
        "max_tokens": 500,
        "keep_alive": "5m",
        "top_p": 0.1
    }

    try:
        response = session.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        raw_text = response.json()["choices"][0]["message"]["content"]

        # Tối ưu parse JSON nhanh hơn regex
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1

        if start == -1 or end == -1:
            print(f"Không tìm thấy JSON: {filename}")
            return

        data_json = json.loads(raw_text[start:end])
        data_json["filename"] = filename

        result.append(data_json)

        print(f"OCR xong: {filename}")

    except Exception as e:
        print(f"Lỗi OCR {filename}: {e}")


# =========================
# 3️⃣ CHUẨN HÓA
# =========================
def result_process():

    for item in result:

        for key, value in item.items():
            if value in ["null", "", "None"]:
                item[key] = None

        if item.get("ngay_banhanh"):
            if not re.match(r"\d{2}/\d{2}/\d{4}", item["ngay_banhanh"]):
                item["ngay_banhanh"] = None

        if item.get("so_vb"):
            item["so_vb"] = item["so_vb"].strip()


# =========================
# 4️⃣ MAIN
# =========================
def main():

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
    
    # BƯỚC 1: Encode ảnh trước (CPU)
    encoded_data = []

    for filename in image_files:
        path = os.path.join(IMAGE_FOLDER, filename)
        img_base64 = img_process(path)
        if img_base64:
            encoded_data.append((filename, img_base64))

    # BƯỚC 2: Gửi API song song
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_single_image, d) for d in encoded_data]

        for future in as_completed(futures):
            future.result()

    result_process()

    print(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n⏳ Tổng thời gian: {time.time() - start_time:.2f} giây")


if __name__ == "__main__":
    main()