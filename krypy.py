import os, re, glob, json, time, requests
from pathlib import Path
import fitz


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def get_absolute_path(relative_path):
    working_directory_path = Path(os.getcwd())
    # 使用/操作符将工作目录和相对路径组合起来
    combined_path = working_directory_path / relative_path
    # 使用.resolve()方法获取绝对路径
    absolute_path = combined_path.resolve()
    return str(absolute_path)


def get_files(directory, suffix=".pdf"):
    files = glob.glob(os.path.join(directory, "*" + suffix))
    filenames = [os.path.basename(file) for file in files]
    # print(files)
    return filenames


def get_page_number(file):
    try:
        doc = fitz.open(file)
    except Exception as e:
        print("Error:", e)
        raise e

    page_number = len(doc)
    for i, page in enumerate(doc):
        text = page.get_text()
        if "Reference" in text or "REFERENCE" in text:
            page_number = i + 1
            break
    doc.close()
    return page_number


def pdf2txt(file=None, page_number=-1):
    try:
        doc = fitz.open(file)
        print("File:", file)
        # print("Type(doc):", type(doc[0]))
        print("Len(doc):", len(doc))

        full_text = ""
        for i, page in enumerate(doc):
            full_text += page.get_text() + "\n\f\n"
            if page_number > 0 and i >= page_number - 1:
                break
        doc.close()

    except Exception as e:
        print("Error:", e)
        raise e
    return full_text


file = "./data/2024.acl-long.173.pdf"
if __name__ == "__main__":
    # with open("test.txt", "w", encoding="utf-8") as f:
    #     f.write(pdf2txt(file))

    pass
