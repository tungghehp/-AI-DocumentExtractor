from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang='vi',  # QUAN TRỌNG
    use_textline_orientation=True
)

result = ocr.ocr("test.jpg")

for line in result:
    print(line)