import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pdf2image import convert_from_path
import shutil

# ====== CẤU HÌNH ======

# Lấy đường dẫn thư mục 'data'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Lùi lại 1 cấp để ra thư mục gốc[cite: 1]
BASE_DIR = os.path.dirname(CURRENT_DIR)

PDF_FOLDER = os.path.join(BASE_DIR, "pdf")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(BASE_DIR, "ket_qua_ocr.xlsx")

# Đường dẫn tới thư mục bin của Poppler nằm trong thư mục hiện hành
POPPLER_PATH = os.path.join(CURRENT_DIR, "poppler", "Library", "bin")

DPI = 300
MAX_THREADS = 6
JPEG_QUALITY = 90
# ======================

# Xử lý làm sạch thư mục output
if os.path.exists(OUTPUT_FOLDER):
    try:
        shutil.rmtree(OUTPUT_FOLDER) # Xóa toàn bộ thư mục và file con bên trong
        print(f"--- Đã làm sạch thư mục: {OUTPUT_FOLDER} ---")
    except Exception as e:
        print(f"Không thể xóa thư mục cũ: {e}")

# Tạo lại thư mục output trống
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Xóa file Excel cũ nếu tồn tại
if os.path.exists(OUTPUT_FILE):
    try:
        os.remove(OUTPUT_FILE)
        print(f"--- Đã xóa file cũ: {OUTPUT_FILE} ---")
    except Exception as e:
        print(f"Không thể xóa file Excel cũ: {e}")

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)
    print(f"Đã tạo thư mục đầu vào: {PDF_FOLDER}. Hãy bỏ file PDF vào đây.")

def normalize_filename(name):
    """
    - Bỏ dấu tiếng Việt
    - Bỏ khoảng trắng
    - Loại ký tự đặc biệt
    """
    nfkd_form = unicodedata.normalize('NFKD', name)
    no_accent = ''.join(c for c in nfkd_form if not unicodedata.combining(c))
    no_space = no_accent.replace(" ", "")
    cleaned = re.sub(r'[^A-Za-z0-9._-]', '', no_space)
    return cleaned

def make_unique_filename(path):
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    return new_path

def extract_one(filename):
    pdf_path = os.path.join(PDF_FOLDER, filename)
    try:
        pages = convert_from_path(
            pdf_path,
            dpi=DPI,
            first_page=1,
            last_page=1,
            poppler_path=POPPLER_PATH
        )

        if pages:
            base_name = os.path.splitext(filename)[0]
            base_name = normalize_filename(base_name)
            output_name = base_name + ".jpg"
            output_path = os.path.join(OUTPUT_FOLDER, output_name)
            output_path = make_unique_filename(output_path)

            pages[0].save(output_path, "JPEG", quality=JPEG_QUALITY)
            print(f"✔ {filename} -> {os.path.basename(output_path)}")
    except Exception as e:
        print(f"✖ Lỗi {filename}: {e}")

def main():
    if not os.path.exists(PDF_FOLDER):
        print("Thư mục PDF_FOLDER không tồn tại!")
        return

    files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    total = len(files)
    print(f"Tổng số file PDF tìm thấy: {total}")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(extract_one, files)

    print("=== HOÀN THÀNH ===")

if __name__ == "__main__":
    main()