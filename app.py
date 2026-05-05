import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import sys
import importlib

# Import các file xử lý của bạn
import pdf2img
import main_v4

class AppGUI:
    def __init__(self, root):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.root = root
        self.root.title("Phần mềm AI trích xuất thông tin văn bản")
        self.root.geometry("700x600")

        # --- (1) Thông tin phần mềm ---
        header_frame = tk.Frame(self.root, pady=10)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="PHẦN MỀM TRÍCH XUẤT THÔNG TIN VĂN BẢN (AI)", font=("Helvetica", 14, "bold")).pack()
        tk.Label(header_frame, text="Version: 1.0.0 | Dev: Nguyễn Thanh Tùng | 0833.270.594 | wind.gemini.165@gmail.com", font=("Helvetica", 10, "italic")).pack()

        # --- (2) Hướng dẫn sử dụng ---
        instr_frame = tk.LabelFrame(self.root, text="Hướng dẫn sử dụng", padx=10, pady=10)
        instr_frame.pack(padx=20, pady=10, fill="x")
        
        instructions = (
            "Để sử dụng phần mềm, vui lòng làm theo các bước sau:\n"
            "- Bước 1: Thư mục 'output' và file 'ket_qua_ocr.xlsx' cũ (nếu có) đã được xóa tự động để đảm bảo không lỗi.\n"
            "- Bước 2: Copy các file PDF cần xử lý vào thư mục 'pdf'.\n"
            "- Bước 3: Ấn nút 'Xử lý PDF' để chuyển đổi PDF thành ảnh.\n"
            "- Bước 4: Ấn nút 'Trích xuất' để AI đọc dữ liệu và xử lý.\n"
            "*** Kết quả trích xuất sẽ được lưu vào file 'ket_qua_ocr.xlsx' trong thư mục gốc ***"
        )
        tk.Label(instr_frame, text=instructions, justify="left").pack(anchor="w")

        # --- (3) Buttons ---
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        self.btn_pdf = tk.Button(btn_frame, text="1. Xử lý PDF", width=20, height=2, 
                                 bg="#e1e1e1", command=self.run_pdf2img)
        self.btn_pdf.grid(row=0, column=0, padx=10)

        self.btn_ocr = tk.Button(btn_frame, text="2. Trích xuất", width=20, height=2, 
                                 bg="#e1e1e1", command=self.run_ocr)
        self.btn_ocr.grid(row=0, column=1, padx=10)

        # --- (4) Console Log ---
        tk.Label(self.root, text="Nhật ký hoạt động:").pack(anchor="w", padx=20)
        self.console = scrolledtext.ScrolledText(self.root, height=15, state='disabled', bg="black", fg="white")
        self.console.pack(padx=20, pady=5, fill="both", expand=True)

        # Redirect stdout
        sys.stdout = self

    def write(self, text):
        """Hàm để ghi log từ print() vào console giao diện"""
        self.console.config(state='normal')
        self.console.insert(tk.END, text)
        self.console.see(tk.END)
        self.console.config(state='disabled')

    def flush(self):
        pass

    def check_output_exists(self):
        """Kiểm tra thư mục output ở thư mục gốc"""
        output_path = os.path.join(self.base_dir, "output")
        if not os.path.exists(output_path):
            return False
        files = [f for f in os.listdir(output_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        return len(files) > 0

    def run_pdf2img(self):
        self.btn_pdf.config(state="disabled")
        # Chạy trong thread riêng để không bị treo giao diện
        thread = threading.Thread(target=self._execute_pdf_task)
        thread.start()

    def _execute_pdf_task(self):
        print("\n[HỆ THỐNG] Đang bắt đầu xử lý PDF...")
        try:
            importlib.reload(pdf2img)
            # QUAN TRỌNG: Phải gọi hàm main() của file pdf2img.py
            pdf2img.main() 
        except Exception as e:
            print(f"[LỖI] {str(e)}")
        finally:
            self.btn_pdf.config(state="normal")

    def run_ocr(self):
        # Kiểm tra điều kiện có file trong output chưa
        if not self.check_output_exists():
            messagebox.showwarning("Cảnh báo", "Thư mục 'output' chưa có ảnh! Vui lòng thực hiện Bước 1 (Xử lý PDF) trước.")
            return

        self.btn_ocr.config(state="disabled")
        thread = threading.Thread(target=self._execute_ocr_task)
        thread.start()

    def _execute_ocr_task(self):
        print("[HỆ THỐNG] Đang bắt đầu trích xuất dữ liệu OCR...")
        try:
            importlib.reload(main_v4)
            # QUAN TRỌNG: Phải gọi hàm main() của file main_v4.py
            main_v4.main()
            messagebox.showinfo("Hoàn thành", "Đã trích xuất xong!")
        except Exception as e:
            print(f"[LỖI] {str(e)}")
        finally:
            self.btn_ocr.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()