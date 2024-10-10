import fitz  # PyMuPDF
import os


def pdf_to_pages(pdf_path, page_dir):
    # 确保输出目录存在
    if not os.path.exists(page_dir):
        os.makedirs(page_dir)

        # 打开PDF文件
    doc = fitz.open(pdf_path)

    # 遍历PDF的每一页
    for page_num in range(len(doc)):
        page = doc[page_num]

        # 设置图片的分辨率（DPI），这会影响图片的质量
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)

        # 生成图片文件名
        image_filename = os.path.join(page_dir, f"page_{page_num+1}.png")

        # 将图片保存到文件
        pix.save(image_filename)

        # 关闭PDF文件
    doc.close()
    print(f"PDF拆分完成，页面已保存到 {page_dir}")


# pdf_to_images(
#     "/data2/kry/work/PaperAnalysisGenerator/data/2024.acl-long.173.pdf", "./output1"
# )
