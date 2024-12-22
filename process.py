import re
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def split_text_by_pattern(text, pattern):
    # 使用正则表达式按给定模式分割文本
    sections = re.split(pattern, text)
    return sections

def save_sections_to_file(sections, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        for section in sections:
            file.write("#####\n")
            file.write(section.strip() + "\n")

def main():
    pdf_path = '/Users/limingzhe/Desktop/OCRandSearch/questions.pdf'  # 输入的PDF文件路径
    output_path = '/Users/limingzhe/Desktop/OCRandSearch/questions.txt'  # 输出的文本文件路径
    pattern = r'\[.*?\]'  # 分割模式

    text = extract_text_from_pdf(pdf_path)
    sections = split_text_by_pattern(text, pattern)
    save_sections_to_file(sections, output_path)
    print("文本已成功分割并保存到文件中")

if __name__ == "__main__":
    main()