import base64
import requests
import os
import fitz  # PyMuPDF
from PIL import Image
import json
from openai import OpenAI
import cv2

# OpenAI API Key
api_key = "EMPTY"


from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_size(image_path):
    # 打开图片
    with Image.open(image_path) as img:
        # 获取图片的尺寸
        width, height = img.size
        return width, height


def bbox_to_relative(bbox, image_path):  # 将bbox转换为相对坐标
    """
    Convert absolute bbox coordinates to relative coordinates.

    Parameters:
    bbox (list): The bounding box coordinates [x_min, y_min, x_max, y_max].
    image_width (int): The width of the image.
    image_height (int): The height of the image.

    Returns:
    list: Relative bounding box coordinates [rel_x_min, rel_y_min, rel_x_max, rel_y_max].
    """
    x_min, y_min, x_max, y_max = bbox
    image_width, image_height = get_image_size(image_path)
    # Calculate relative coordinates
    rel_x_min = x_min / image_width * 1000
    rel_y_min = y_min / image_height * 1000
    rel_x_max = x_max / image_width * 1000
    rel_y_max = y_max / image_height * 1000

    return [rel_x_min, rel_y_min, rel_x_max, rel_y_max]


# Example usage


# Path to your image


def ask_llm_caption(image_path, bbox):
    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"已知图片或表格的bbox坐标为{bbox}，请提取出这张图或表的caption内容，你只需要输出caption的内容，例如：Table 1: A comparison of our ToolBench to notable instruction tuning dataset for tool learning.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )
    return response.json()

    # 返回对应图片的caption并储存为文本


def get_pictab_caption(image_path, bbox):
    rel_bbox = bbox_to_relative(bbox, image_path)
    response = ask_llm_caption(image_path, rel_bbox)
    content = response["choices"][0]["message"]["content"]

    return content


def crop_image(image_path, bbox, path):
    image = cv2.imread(image_path)
    # 3. 计算切割区域
    x, y, w, h = bbox
    cut_image = image[y:h, x:w]

    # 4. 保存或显示切割后的图像
    cv2.imwrite(path, cut_image)  # 保存切割后的图像
    print("save image to ", "'" + path + "'")


def get_response(image_path, bbox):
    base64_image = encode_image(image_path)
    client = OpenAI(
        api_key="sk-xxx",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    Qwen_bbox = bbox_to_relative(bbox, image_path)
    completion = client.chat.completions.create(
        model="qwen-vl-max-2024-08-09",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                    {
                        "type": "text",
                        "text": f"这张图片中有图/表，给你他的bbox：{Qwen_bbox}，请在bbox坐标的附近找到这张图表的标题。注意，只输出图中的原文，例如：Table 1: A comparison of our ToolBench to notable instruction tuning dataset for tool learning.",
                    },
                ],
            }
        ],
    )
    # response = completion
    # print(completion.model_dump_json())
    # print(type(completion))
    result = completion.choices[0].message.content

    return result


# image_path  =  r'C:\Users\29627\Desktop\Paddle\essay\page_8.png'
# bbox = [140, 818, 578, 934]
# # get_pictab_caption(image_path, bbox)
# get_response(image_path,bbox)
