import sys
from tqdm import tqdm

sys.path.append("./process_image/")

from pdocr import get_pictab_bbox
from get_caption import *
from splitPDF import pdf_to_pages
from read_dir import *


def extract_image(pdf_upload, page_number=10, output_dir="./output1"):

    figure_dic = {}
    table_dic = {}
    available_page = []
    caption_dic = {}

    page_list = []
    image_list = []
    pdf_to_pages(pdf_upload, output_dir + "page/")

    for i in tqdm(range(page_number), desc="Parsing pages"):
        image_path = output_dir + "page/page_" + str(i + 1) + ".png"
        page_list.append({"page_number": i + 1, "file_path": image_path})
        get_pictab_bbox(image_path, output_dir)
        file_path = output_dir + "tmp/page_" + str(i + 1) + "/res_0.txt"
        try:
            table_bbox, figure_bbox = read_res(file_path)
        except Exception as e:
            print("Error:", e)
            raise e
        if table_bbox or figure_bbox:
            available_page.append(i + 1)
            figure_dic[i + 1] = figure_bbox
            table_dic[i + 1] = table_bbox
    figure_num = 1
    table_num = 1
    if not os.path.exists(output_dir + "image/"):
        os.makedirs(output_dir + "image/")
    for item in available_page:
        image_cap_path = output_dir + "page/page_" + str(item) + ".png"
        for figure in figure_dic[item]:
            caption = get_response(image_cap_path, figure)
            path = output_dir + f"image/figure_{figure_num}.jpg"
            figure_num += 1
            image_list.append(
                {
                    "path": path,
                    "type": "figure",
                    "page_number": item,
                    "caption": caption,
                }
            )
            crop_image(image_cap_path, figure, path)  # 切割图片并保存
        for i, table in enumerate(table_dic[item]):
            caption = get_response(image_cap_path, table)
            path = output_dir + f"image/table_{table_num}.jpg"
            table_num += 1
            image_list.append(
                {
                    "path": path,
                    "type": "table",
                    "page_number": item,
                    "caption": caption,
                }
            )
            crop_image(image_cap_path, table, path)  # 切割图表并保存

    with open(output_dir + "caption.txt", "w", encoding="utf-8") as file:
        for i, item in enumerate(image_list):
            file.write(f"{i+1}:{item['caption']}\n")  # 每个元素写入文件并换行

    with open(output_dir + "caption.txt", "r", encoding="utf-8") as file:
        content = ""
        for line in file:
            content += line.strip() + "\n"
    print(content)
    # print(image_list[0])  # 测试用
    return page_list, image_list

    # with open("article.txt", "r", encoding="utf-8") as file:
    #     article = ""
    #     for line in file:
    #         article += line.strip() + "\n"
    #     #读取已经标号的文章内容
    #
    # request = '这是一篇讲述论文的文章，我希望你可以根据这篇文章和我给出的若干图片标题告诉我每个图片应该插入的位置，文章的每一段都已经标号，你只需要说明插入位置在哪两段中间，返回的内容只需要包括两个数字，文章的内容如下'
    # ask_caption = request + article
    # client = OpenAI()
    # question = '以下是若干个图表的标题，你需要告诉我每个图片应该插入在我给的文章中的位置，记住：返回的内容只需要两个段落的序号'
    #
    # response = client.chat.completions.create(
    #   model="gpt-4o",
    #   messages=[
    #     {"role": "system", "content": ask_caption},
    #     {"role": "user", "content": question + content},
    #   ]
    # )

    # 做一个段落标号脚本


if __name__ == "__main__":
    pdf_upload = "/data2/kry/work/PaperAnalysisGenerator/data/2024.acl-long.173.pdf"
    output_dir = "./page"  # 分割PDF后得到图片的文件夹，其中保存的图片格式为“page_x.png”
    extract_image(pdf_upload=pdf_upload, page_number=3, output_dir="./outputxx/")
