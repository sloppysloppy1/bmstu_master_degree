import requests
import sqlite3
import pathlib
import os.path
import pytesseract #pdf
from pdf2image import convert_from_path
import glob
import pypandoc #docx
import win32com.client # doc
from striprtf.striprtf import rtf_to_text #rtf
from bs4 import BeautifulSoup #html
import pathlib

# tesseract для pdf
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# word для doc
word = win32com.client.Dispatch("Word.Application")
word.visible = False

# подключение к бд
con = sqlite3.connect('db')
cur = con.cursor()

# pdf в txt
def pdf_to_txt(num):
    with open(f'files/{num}.txt', 'w', encoding='utf-8') as file:
        pdf_pages = convert_from_path('temp.pdf')
        for pageNum,imgBlob in enumerate(pdf_pages):
            bill_text = pytesseract.image_to_string(imgBlob, lang='rus')
            file.write(bill_text)

# docx в txt
def docx_to_txt(num):
    output = pypandoc.convert_file('temp.docx', 'plain', outputfile=f'files/{num}.txt')

#doc в docx
def doc_to_docx():
    wb = word.Documents.Open(str(pathlib.Path().resolve()) + '\\temp.doc')
    wb.SaveAs2(str(pathlib.Path().resolve()) + '\\temp.docx', FileFormat = 16)
    wb.Close()

# rtf в txt:
def rtf_to_txt(num):
    with open('temp.rtf', 'r') as rtf_file:
        extracted_text = rtf_to_text(rtf_file.read())

    with open(f'files/{num}.txt', 'w') as file:
        file.write(extracted_text)

# hmtl в txt:
def hmtl_to_txt(num):
    with open('temp.html') as file:
        soup = BeautifulSoup(file, features="html.parser")
    for script in soup(["script", "style"]):
        text = soup.get_text() # избавляемся от всех script и style
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    extracted_text = '\n'.join(chunk for chunk in chunks if chunk)

    with open(f'files/{num}.txt', 'w') as file:
        file.write(extracted_text)


if __name__ == '__main__':
    cur.execute('select * from bills')
    for i in range(100):
        bill = cur.fetchone()
        num = bill[1]
        state = bill[2]
        url = bill[3]
        file_extension = bill[4]
        print(num, state, url, file_extension)
        # проверяем, что файла не существует
        if not os.path.isfile(f'files/{num}.txt'):
            # создаем временный файл
            temp_file = open(f'temp.{file_extension}','wb')
            # записываем в него
            req = requests.get(url)
            temp_file.write(req.content)
            temp_file.close()
            # в зависимости от расширения
            if file_extension.lower() == 'pdf':
                pdf_to_txt(num)
            elif file_extension.lower() == 'docx':
                docx_to_txt(num)
            elif file_extension.lower() == 'doc':
                doc_to_docx()
                docx_to_txt(num)
            elif file_extension.lower() == 'rtf':
                rtf_to_txt(num)
            elif file_extension.lower() == 'html':
                html_to_txt(num)


    con.close()
