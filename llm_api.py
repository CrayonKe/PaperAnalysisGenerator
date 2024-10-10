import os, re, glob, json, time, copy, requests
from openai import OpenAI
import base64, tiktoken
from PIL import Image
from krypy import pdf2txt
from dotenv import load_dotenv

load_dotenv(verbose=True)
api_key = os.environ["OPENAI_API_KEY"]
base_url = os.environ["OPENAI_BASE_URL"]
model_name = os.environ["LLM_MODEL_NAME"]

default_config = (api_key, base_url, model_name)

# default_api_key = "EMPTY"
# default_base_url = "http://10.176.40.140:8272/v1"
# default_model_name = "/data2/kry/Qwen/Qwen2.5-72B-Instruct"

# default_config = (default_api_key, default_base_url, default_model_name)

vision_api_key = "EMPTY"
vision_base_url = "http://10.176.40.140:8372/v1"
vision_model_name = "/data2/kry/Qwen/Qwen2.5-72B-Instruct"

vision_config = (vision_api_key, vision_base_url, vision_model_name)

default_msgs = [
    {
        "role": "system",
        "content": "You are a helpful assistant.",
    },
]

query_pdf_msgs = [
    {
        "role": "system",
        "content": "你是一位学术研究专家，请阅读并理解科研论文的内容，用于专业学术研讨。",
    }
]

# query_img_msgs = []


def compress_image(image_path, output_path, quality=85):
    with Image.open(image_path) as img:
        img.save(output_path, "PNG", optimize=True, quality=quality)


def encode_image(image_path):
    """Function to encode the image"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


img_dir = "/data2/kry/work/PaperAnalysisGenerator/process_image/output1"

# img_dir = "./output/20240926-144435-QWEN2-VL/page"

# entries = os.listdir(img_dir)
# print(entries)
# MAX_SIZE = 0
# for entry in entries:
#     if entry.endswith(".png"):
#         fp = os.path.join(img_dir, entry)
#         print(fp)
#         file_size = os.path.getsize(fp)
#         print(f"The size of the file is: {file_size} bytes")

#         if file_size > MAX_SIZE:
#             MAX_SIZE = file_size

#         aaa = encode_image(fp)
#         print(len(aaa))
#         print("")
# print("MAX_SIZE=", MAX_SIZE)
# exit(0)


def tokens_counter(messages, model):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        # 计算每个 message 的 role 和 content 的 token 数
        num_tokens += len(encoding.encode(message["role"]))
        if type(message["content"]) == str:
            num_tokens += len(encoding.encode(message["content"]))
        elif type(message["content"]) == list:
            for item in message["content"]:
                if item["type"] == "text":
                    num_tokens += len(encoding.encode(item["text"]))
                elif item["type"] == "image_url":
                    num_tokens += len(encoding.encode(item["image_url"]["url"]))
        # 如果 message 中有 name 字段（如系统消息），也要计算
        if "name" in message:
            num_tokens += len(encoding.encode(message["name"]))
        # 对于消息中的特殊 token，OpenAI 额外加上 2 个 token 消耗
        num_tokens += 2
    return num_tokens


def llm_query0(prompt):
    metadata = {"model": "gpt-4o", "temperature": 0.2, "max_tokens": 2048}
    history = [{"role": "user", "content": prompt}]
    aaa = requests.post(
        "http://10.176.64.118:40004/ans",
        json={
            # "name_key": "RCRyX3gdL4tmtspcE8aXEsmkqKwcL/t9FoQWO7T64Jq3G0ziQ39t1rHmquiIVdQejlKXyI78U80Cle0y3zKENA==",
            "name_key": "EexJEkPXMlL8Dy6qFIT95MTkiJGAsocEjkrgVRrauvDOibfwmvIr46cQ9/qOj2OzYpSNuDvUSwDPAgJCWM7z2g==",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    # '"以下哪个选项与"{x}"的逻辑关系最相似？", "以下哪个选项可以与"{x}"类比？", "与"{x}"的逻辑关系最相似的是：", 可以给我生成20句与上述相似的句子吗',
                },
                {
                    "role": "user",
                    "content": prompt,
                    # '"以下哪个选项与"{x}"的逻辑关系最相似？", "以下哪个选项可以与"{x}"类比？", "与"{x}"的逻辑关系最相似的是：", 可以给我生成20句与上述相似的句子吗',
                },
            ],
            **metadata,
        },
    )
    print(type(aaa))
    ttt = str(aaa)
    with open("log.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(ttt, indent=4, ensure_ascii=False))
        f.write("\n")
    response = aaa.json()["ans"][0]
    return response


def llm_query(
    use_config=default_config,
    msgs=default_msgs,
    verbose=True,
):
    api_key, base_url, model_name = use_config
    if type(msgs) == str:
        msgs = [{"role": "user", "content": msgs}]
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=300)

    # ##计算 messages 的 token 消耗
    if verbose:
        token_count = tokens_counter(msgs, model_name)
        print(f"Total tokens used: {token_count}")

        # with open("log.json", "a", encoding="utf-8") as f:
        #     f.write(json.dumps(msgs, ensure_ascii=False))
        #     f.write("\n")

    response = client.chat.completions.create(
        model=model_name,
        messages=msgs,
        temperature=0.5,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    # print(response)
    # print(response.choices[0].message.content)

    # if verbose:
    #     with open("log.json", "a", encoding="utf-8") as f:
    #         f.write(json.dumps(response.to_dict(), ensure_ascii=False))
    #         f.write("\n\n")
    return response


def llm_query_pdf(use_config=default_config, file=None, prompt=None):
    msgs = copy.deepcopy(query_pdf_msgs)

    if file:
        full_text = pdf2txt(file)
        # print("Full_text_length=", len(full_text))
        msgs.append({"role": "system", "content": full_text})

    if prompt:
        msgs.append({"role": "user", "content": prompt})

    response = llm_query(use_config, msgs)
    return response


def add_image_to_msgs(msgs, image_path):
    base64_image = encode_image(image_path)
    msgs.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            ],
        }
    )


def llm_query_img(use_config=default_config, msgs=default_msgs, file=None, prompt=None):
    if type(file) == list:
        for f in file:
            add_image_to_msgs(msgs, f)
    elif file:
        add_image_to_msgs(msgs, file)

    if prompt:
        msgs.append({"role": "user", "content": prompt})
    try:
        response = llm_query(use_config, msgs)
    except Exception as e:
        print("Error:", e)
        raise e
    return response


if __name__ == "__main__":
    # test
    pass
