import pytesseract
import fitz
from PIL import Image
import io
import re

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


file_path = 'test.pdf'
full_content = []

TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
try:
    if TESSERACT_PATH:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
except Exception as e:
    print(f"❌ Cảnh báo: Không thể thiết lập đường dẫn Tesseract. Vui lòng kiểm tra lại TESSERACT_PATH. Lỗi: {e}")

def clean_ocr_text(text):
    """Loại bỏ ký tự dư thừa và khoảng trắng lặp lại từ kết quả OCR."""
    text = text.replace('\f', ' ')
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = '\n'.join(line.strip() for line in text.split('\n'))
    return text.strip()

def normalize_text(text):
    lines = text.split("\n")
    paragraphs = []
    buf = ""

    for line in lines:
        line = line.strip()
        if not line:
            if buf:
                paragraphs.append(buf.strip())
                buf = ""
        else:
            buf += " " + line

    if buf:
        paragraphs.append(buf.strip())

    return paragraphs

doc = fitz.open(file_path)

for page_number in range(len(doc)):
    page = doc.load_page(page_number)
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    ocr_text = pytesseract.image_to_string(img, lang='vie')
    text = clean_ocr_text(ocr_text)
    full_content.append(text)

#print(full_content)
full_text = "\n\n".join(full_content)
paragraphs = normalize_text(full_text)

#print(paragraphs)
model_path = "protonx-models/protonx-legal-tc"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

max_tokens = 160

for text in paragraphs:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_tokens
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            num_beams=10,
            num_return_sequences=1,     # <- return all beams
            max_new_tokens=max_tokens,
            early_stopping=True,
            return_dict_in_generate=True,  # <- return full dict
            output_scores=True             # <- include beam scores
        )

    sequences = outputs.sequences
    scores = outputs.sequences_scores

    print(f"Input: {text}")

    for i, (seq, score) in enumerate(zip(sequences, scores)):
        decoded = tokenizer.decode(seq, skip_special_tokens=True)
        # print(f"Beam {i+1} | Score: {float(score):.4f}")
        print(f"Output: {decoded}")
        print("-" * 40)