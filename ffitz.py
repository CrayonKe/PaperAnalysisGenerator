import os, sys, json
import fitz  # PyMuPDF


# from prompts import pageparser_inst


class PageElement:
    def __init__(self, page_number, file_path, page_width=100, page_height=100):
        self.page_number = page_number
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.page_width = page_width
        self.page_height = page_height


# 定义一个图片类，包含图片的路径和bbox，以及图片的caption
class ImageElement:
    score1 = 0
    score2 = 0
    choose = None

    def __init__(
        self,
        file_path,
        type=None,
        page_number=0,
        caption=None,
        bbox=[1, 1, 1, 1],
    ):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.type = type
        self.page_number = page_number
        self.caption = caption
        self.bbox = bbox

    def output(self):
        # 用json格式打印，不要有indent参数换行
        print(json.dumps(self.__dict__, indent=4))


def extract_images_from_pdf(file, output_directory):
    # 打开PDF文件
    # 如果没有输出目录，创建一个
    if not os.path.exists(output_directory + "page/"):
        os.makedirs(output_directory + "page/")
    if not os.path.exists(output_directory + "image/"):
        os.makedirs(output_directory + "image/")

    doc = fitz.open(file)
    page_elements = []
    image_elements = []
    for page_num in range(len(doc)):
        # 获取PDF的一页
        page = doc.load_page(page_num)
        # print(type(page))
        text = page.get_text()
        pos = text.find("References")
        if pos >= 0:
            break
        pix = page.get_pixmap()
        page_filename = os.path.join(
            output_directory + "page/", f"page_{page_num + 1}.png"
        )
        pix.save(page_filename)
        print(f"Page {page_num + 1} saved as {page_filename}")

        page_element = PageElement(page_num, page_filename, pix.width, pix.height)
        page_elements.append(page_element)

        # 提取当前页的图像列表
        image_list = page.get_images(full=True)
        print("Page:", page_num, " - Number of images:", len(image_list))

        # 遍历图像列表
        for image_index, img in enumerate(image_list):
            xref = img[0]
            # 获取图像的边界框
            bbox = img[2]

            # 提取图像
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # 保存图像
            image_filename = f"image_page{page_num+1}_{image_index}.png"
            image_path = os.path.join(output_directory + "image/", image_filename)

            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

            print(f"Image {image_index} saved to {image_path}")

            response = llm_query_img(
                files=[image_path, page_filename],
                prompt="第二张图是从第一张图截取出来的，请从第一张图中，找到第二张图的caption。请注意，只输出caption，不要输出其他内容。",
            )
            caption = response.choices[0].message.content
            print("caption:", '"', caption, '"')

            image_element = ImageElement(
                file_path=image_path,
                page_number=page_num,
                caption=caption,
            )
            image_elements.append(image_element)

    # 关闭PDF文件
    doc.close()
    return page_elements, image_elements


# def extract_image(output_directory:str , pdf) #函数名不重要，
#     '''抽取视觉元素，按格式保存到目录'''
#     # 提取过程

#     pass
#     return [image.path, image.type, image.caption]


if __name__ == "__main__":
    directory = "./data/"
    file = "DoT.pdf"

    output_directory = "./output/20240925-015708-DoT/"
    extract_images_from_pdf(directory + file, output_directory)
    pass


# 页面保存格式
"<output_directory>/page/page_xxx.png"
# 图像元素格式
"<output_directory>/image/image_xxx.png"
