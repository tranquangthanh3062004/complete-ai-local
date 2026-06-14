import os
import glob
import pandas as pd
from docx import Document
import PyPDF2
import re

DATA_DIR = r"c:\Users\ADMIN 88\OneDrive\Desktop\my_open_llm\data"
RAW_SUBDIR = os.path.join(DATA_DIR, "raw_data")
HANOI_DIR = os.path.join(DATA_DIR, "hanoi")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")

def process_kienthuc():
    input_path = os.path.join(DATA_DIR, "gtcc_kienthuc.txt")
    out_metro = os.path.join(HANOI_DIR, "metro_hanoi.txt")
    out_bus = os.path.join(HANOI_DIR, "bus_brt_hanoi.txt")
    out_general = os.path.join(HANOI_DIR, "quy_dinh_phap_luat.txt")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by parts
    parts = re.split(r'={80}\nPHẦN [A-Z] — ', content)
    
    hanoi_metro = []
    hanoi_bus = []
    hanoi_brt = []
    hanoi_faq = []
    hanoi_general = []

    for part in parts:
        if part.startswith('METRO HÀ NỘI'):
            hanoi_metro.append(part)
        elif part.startswith('XE BUÝT HÀ NỘI'):
            hanoi_bus.append(part)
        elif part.startswith('XE BUÝT NHANH BRT'):
            # Filter HCM BRT
            lines = part.split('\n')
            filtered_lines = [l for l in lines if 'TP.HCM' not in l and 'Rạch Chiếc' not in l and 'Miền Tây' not in l]
            hanoi_brt.append('\n'.join(filtered_lines))
        elif part.startswith('GỢI Ý LỘ TRÌNH'):
            lines = part.split('\n')
            filtered_lines = [l for l in lines if 'HÀ NỘI' in l or 'Nội Bài' in l or 'Cát Linh' in l or 'Nhổn' in l]
            hanoi_faq.append('\n'.join(filtered_lines))
        elif part.startswith('QUY ĐỊNH'):
            hanoi_general.append(part)
        elif part.startswith('CÂU HỎI THƯỜNG GẶP'):
            lines = part.split('\n')
            filtered_lines = [l for l in lines if 'Hà Nội' in l or 'Nội Bài' in l or 'Cát Linh' in l or 'Nhổn' in l or 'BRT' in l]
            hanoi_faq.append('\n'.join(filtered_lines))
            
    with open(out_metro, 'w', encoding='utf-8') as f:
        f.write("=== METRO HÀ NỘI ===\n")
        f.write('\n'.join(hanoi_metro))
        
    with open(out_bus, 'w', encoding='utf-8') as f:
        f.write("=== XE BUÝT HÀ NỘI ===\n")
        f.write('\n'.join(hanoi_bus))
        f.write("\n=== BRT HÀ NỘI ===\n")
        f.write('\n'.join(hanoi_brt))
        f.write("\n=== GỢI Ý LỘ TRÌNH HÀ NỘI ===\n")
        f.write('\n'.join(hanoi_faq))

    with open(out_general, 'w', encoding='utf-8') as f:
        f.write("=== QUY ĐỊNH PHÁP LUẬT ===\n")
        f.write('\n'.join(hanoi_general))


def process_excel():
    excel_files = glob.glob(os.path.join(RAW_SUBDIR, "*.xlsx"))
    if not excel_files:
        print("No Excel files found.")
        return
    file = excel_files[0]
    try:
        df = pd.read_excel(file)
        out_path = os.path.join(HANOI_DIR, "danh_sach_tuyen_buyt.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("=== DANH SÁCH TUYẾN XE BUÝT HÀ NỘI (TỪ EXCEL) ===\n\n")
            for index, row in df.iterrows():
                row_str = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                f.write(f"- {row_str}\n")
    except Exception as e:
        print(f"Error processing Excel: {e}")

def process_word():
    word_files = glob.glob(os.path.join(RAW_SUBDIR, "*.docx"))
    if not word_files:
        print("No Word files found.")
        return
    file = word_files[0]
    try:
        doc = Document(file)
        out_path = os.path.join(HANOI_DIR, "lich_trinh_buyt.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("=== LỊCH TRÌNH CÁC TUYẾN XE BUÝT HÀ NỘI ===\n\n")
            for para in doc.paragraphs:
                if para.text.strip():
                    f.write(para.text + "\n")
    except Exception as e:
        print(f"Error processing Word: {e}")

def process_pdf():
    pdf_files = glob.glob(os.path.join(RAW_SUBDIR, "*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        return
    
    out_path = os.path.join(HANOI_DIR, "tai_lieu_phap_ly.txt")
    with open(out_path, 'w', encoding='utf-8') as f_out:
        f_out.write("=== TÀI LIỆU PHÁP LÝ & QUY ĐỊNH ===\n\n")
        for pdf_file in pdf_files:
            try:
                f_out.write(f"\n--- Tài liệu: {os.path.basename(pdf_file)} ---\n")
                reader = PyPDF2.PdfReader(pdf_file)
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    text = page.extract_text()
                    if text:
                        f_out.write(text + "\n")
            except Exception as e:
                print(f"Error processing PDF {pdf_file}: {e}")

if __name__ == "__main__":
    if not os.path.exists(HANOI_DIR):
        os.makedirs(HANOI_DIR)
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    
    print("Processing Kienthuc...")
    process_kienthuc()
    print("Processing Excel...")
    process_excel()
    print("Processing Word...")
    process_word()
    print("Processing PDFs...")
    process_pdf()
    print("Done!")
