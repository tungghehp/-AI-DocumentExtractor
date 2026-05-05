from paddleocr import PaddleOCR

# Khởi tạo OCR cho tiếng Việt, CPU
ocr = PaddleOCR(lang='vi', use_angle_cls=True)

# OCR trên ảnh
image_path = "test.jpg"  # đường dẫn tới file ảnh của bạn
result = ocr.predict(image_path)

# In kết quả
print(result)
