
import subprocess
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

#========================
# CHECK DEPENDENCIES
#========================
def install_basic_libs():
    """
    Kiểm tra và cài các thư viện cần thiết:
    - requests
    - opencv-python
    - pillow
    """

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

install_basic_libs() # Chạy kiểm tra và cài đặt thư viện trước khi import
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

result = []  # Biến global chứa toàn bộ kết quả



# =========================
# 1️⃣ XỬ LÝ ẢNH
# =========================
def img_process(image_path):

    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # Crop 45% phía trên (đủ trích yếu)
    cropped = img[0:int(h * 0.3), :]

    ch, cw = cropped.shape[:2]

    # Resize mạnh hơn một chút
    max_width = 1000
    if cw > max_width:
        ratio = max_width / cw
        cropped = cv2.resize(
            cropped,
            (max_width, int(ch * ratio))
        )

    # JPEG nhẹ hơn
    _, buffer = cv2.imencode(
        ".jpg",
        cropped,
        [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    )

    return base64.b64encode(buffer).decode("utf-8")


# =========================
# 2️⃣ GỬI OCR TỚI OLLAMA
# =========================
def ocr_process(img_base64, filename):
    """
    Gửi ảnh tới Ollama và lấy JSON
    Thêm kết quả vào biến result
    """
    print("Độ dài base64:", len(img_base64))

    global result

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
    "max_tokens": 200
}
    raw_text = None

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        resp_json = response.json()

        if "choices" in resp_json:
            raw_text = resp_json["choices"][0]["message"]["content"]
        else:
            print("Response không hợp lệ:", resp_json)
            return

        # Trích JSON an toàn
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            print(f"Không tìm thấy JSON hợp lệ: {filename}")
            return

        data = json.loads(match.group())

        data["filename"] = filename  # lưu lại tên file
        result.append(data)

        print(f"OCR xong: {filename}")

    except Exception as e:
        print(f"Lỗi OCR {filename}: {e}")
    print("RAW MODEL OUTPUT:")
    print(raw_text)

# =========================
# 3️⃣ CHUẨN HÓA KẾT QUẢ CUỐI
# =========================
def result_process():
    """
    Chuẩn hóa dữ liệu:
    - Kiểm tra format ngày
    - Làm sạch số văn bản
    - Thay null string thành None
    """

    global result

    for item in result:

        # Chuẩn hóa null
        for key, value in item.items():
            if value in ["null", "", "None"]:
                item[key] = None

        # Chuẩn hóa ngày (đảm bảo dd/mm/yyyy)
        if item.get("ngay_banhanh"):
            if not re.match(r"\d{2}/\d{2}/\d{4}", item["ngay_banhanh"]):
                item["ngay_banhanh"] = None

        # Làm sạch số văn bản (loại bỏ khoảng trắng dư)
        if item.get("so_vb"):
            item["so_vb"] = item["so_vb"].strip()

    print("Chuẩn hóa dữ liệu hoàn tất.")


# =========================
# 4️⃣ MAIN
# =========================
def main():
    global result

    start_time = time.time() #Bắt đầu đếm thời gian

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

    for filename in image_files:
        image_path = os.path.join(IMAGE_FOLDER, filename)

        img_base64 = img_process(image_path)
        if img_base64:
            ocr_process(img_base64, filename)

    # Sau khi quét xong tất cả
    result_process()

    # In kết quả cuối
    print(json.dumps(result, indent=2, ensure_ascii=False))

    end_time = time.time()  # ⏱ kết thúc
    total_time = end_time - start_time

    print(f"\n⏳ Tổng thời gian xử lý: {total_time:.2f} giây")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()