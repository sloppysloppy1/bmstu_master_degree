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
ex_cur = con.cursor()

# pdf в txt
def pdf_to_txt(num):
    with open(f'temp/files/{num}.txt', 'w', encoding = 'utf-8') as file:
        pdf_pages = convert_from_path('temp/temp.pdf')
        for pageNum,imgBlob in enumerate(pdf_pages):
            bill_text = pytesseract.image_to_string(imgBlob, lang='rus')
            file.write(bill_text)

# docx в txt
def docx_to_txt(num):
    output = pypandoc.convert_file('temp/temp.docx', 'plain', outputfile=f'files/{num}.txt')

#doc в docx
def doc_to_docx():
    wb = word.Documents.Open(str(pathlib.Path().resolve()) + '\\temp\\temp.doc')
    wb.SaveAs2(str(pathlib.Path().resolve()) + '\\temp\\temp.docx', FileFormat = 16)
    wb.Close()

# rtf в txt:
def rtf_to_txt(num):
    with open('temp/temp.rtf', 'r') as rtf_file:
        extracted_text = rtf_to_text(rtf_file.read())

    with open(f'files/{num}.txt', 'w', encoding = 'utf-8') as file:
        file.write(extracted_text)

# hmtl в txt:
def html_to_txt(num):
    with open('temp/temp.html') as file:
        soup = BeautifulSoup(file, features="html.parser")
    for script in soup(["script", "style"]):
        text = soup.get_text() # избавляемся от всех script и style
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    extracted_text = '\n'.join(chunk for chunk in chunks if chunk)

    with open(f'files/{num}.txt', 'w', encoding = 'utf-8') as file:
        file.write(extracted_text)

def do_stuff(num, url, file_extension):
        temp_file = open(f'temp/temp.{file_extension}','wb')
        # записываем
        req = requests.get(url)
        temp_file.write(req.content)
        temp_file.close()
        # в зависимости от расширения
        if file_extension.lower() == 'pdf':
            pdf_to_txt(num)
        elif file_extension.lower() == 'docx':
            docx_to_txt(num)
        elif file_extension.lower() == 'doc':
            try:
                doc_to_docx()
                docx_to_txt(num)
            except Exception:
                pass
        elif file_extension.lower() == 'rtf':
            rtf_to_txt(num)
        elif file_extension.lower() == 'html':
            html_to_txt(num)


if __name__ == '__main__':
    cur.execute('select * from bills')
    for i in range(100):
        bill = cur.fetchone()
        num = bill[1]
        state = bill[2]
        url = bill[9]
        file_extension = bill[10]
        ext_url = bill[11]
        ext_file_extension = bill[12]
        dl_flg = bill[22]
        print(num, state, url, file_extension, ext_url, ext_file_extension, dl_flg)
        # проверяем, что файла не существует
        if not os.path.isfile(f'files/{num}.txt'):
            ex_cur.execute('update bills set dl_flg = 2 where bill_num = ?', (num,))
            con.commit()
            ex_num = num + '_ex'
            do_stuff(num, url, file_extension)
            try:
                do_stuff(ex_num, ext_url, ext_file_extension)
            except Exception:
                pass
            # все в один файл
            try:
                with open(f'files/{ex_num}.txt', 'r', encoding = 'utf-8') as ex_file:
                    with open(f'files/{num}.txt', 'a', encoding = 'utf-8') as file:
                        text = ex_file.read()
                        file.write('\n\n----------------------' + \
                        '-------------------------------------\n' + text)
                os.remove(f'files/{ex_num}.txt')
            except FileNotFoundError:
                pass
            ex_cur.execute('update bills set dl_flg = 1 where bill_num = ?', (num,))
            con.commit()

    con.close()
