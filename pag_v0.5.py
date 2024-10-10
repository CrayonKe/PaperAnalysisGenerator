import os, re, sys, ast, glob, json, time, copy
from tqdm import tqdm
from llm_api import default_config, default_msgs
from llm_api import llm_query, llm_query_pdf, llm_query_img
from krypy import get_page_number, pdf2txt
from prompts.planner_prompt import planner_inst_1, planner_inst_2
from prompts.writer_prompt import writer_inst_1
from prompts.scorer_prompt import scorer_inst_1, scorer_inst_2
from ffitz import PageElement, ImageElement
from process_image.parsePDF import extract_image

# 添加路径
# sys.path.append('./src')


class PaperAnalysisGenerator:
    default_msgs = [
        {
            "role": "system",
            "content": "你是一位学术研究专家，请阅读并总结科研论文的内容，用于专业学术研讨。",
        }
    ]
    file = None
    page_number = 1
    full_text = "None"
    summary = "None"
    plan = "None"
    N = 0
    steps = "None"
    paragraphs = None
    paragraphs_image = None
    article = ""
    headline = ""

    def __init__(self, file):
        self.file = file
        self.page_number = get_page_number(file)
        self.full_text = pdf2txt(file, self.page_number)
        print("-" * 20 + "PaperAnalysisGenerator initialized." + "-" * 20)

    def get_summary(self, verbose=False):
        msgs = copy.deepcopy(self.default_msgs)
        msgs.append({"role": "system", "content": self.full_text})
        msgs.append({"role": "user", "content": "请用500字详细介绍这篇论文的研究内容"})
        response = llm_query(msgs=msgs)
        self.summary = response.choices[0].message.content
        return self.summary

    def get_plan(self):
        # self.plan = planning(self.file)

        response = llm_query_pdf(file=self.file, prompt=planner_inst_1)
        # print(response)
        text = response.choices[0].message.content
        self.plan = text.strip().replace("\n\n", "\n")

        steps = self.plan.split("\n")
        self.steps = [step for step in steps if step.startswith("第")]
        self.N = len(self.steps)
        self.paragraphs = ["None" for i in range(self.N)]
        self.paragraphs_image = [[] for i in range(self.N)]
        return self.plan

    def write_paragraph(self, i):
        prompt = copy.deepcopy(writer_inst_1)

        prompt = prompt.replace("$PLAN$", self.plan).replace("$STEP$", self.steps[i])
        if i > 0:
            prompt = prompt.replace("$TEXT$", self.paragraphs[i - 1])
            # prompt = prompt.replace("$TEXT$", article)
        else:
            prompt = prompt.replace("$TEXT$", "None")

        print(prompt)
        response = llm_query_pdf(file=self.file, prompt=prompt)
        # print(response)
        text = response.choices[0].message.content
        self.paragraphs[i] = text
        print(text)

        return text

    def get_article(self):
        if self.N == 0:
            self.article = "None"
            return self.article

        n = self.N
        while n > 0 and self.paragraphs[n - 1] == "None":
            n -= 1
        for i in range(n):
            self.article += self.paragraphs[i] + "\n\n"

        return self.article

    def get_headline(self):
        msgs = copy.deepcopy(self.default_msgs)
        msgs.append({"role": "system", "content": self.full_text})
        msgs.append({"role": "user", "content": "请给这篇公众号文章取一个标题"})
        response = llm_query(msgs=msgs)
        self.headline = response.choices[0].message.content
        return self.headline


class PaperAnalysisGenerator_Agent:

    def __init__(
        self,
        config=default_config,
        use_memory=False,
    ):
        """
        初始化 LLM Agent，配置 API 密钥和模型名称。
        """
        self.config = config
        self.use_memory = use_memory
        self.history = self.default_msgs  # 用于存储多轮对话的上下文
        print("-" * 20 + "PaperAnalysisGenerator_Agent initialized." + "-" * 20)

    def _build_conversation(self, user_input: str):
        """构建 conversation，结合对话历史来维护上下文。"""
        if self.use_memory:
            self.history.append({"role": "user", "content": user_input})
        return self.history

    def __call__(self, prompt, max_tokens=2048):
        """生成并返回 LLM 的响应，使用多轮对话的上下文。"""

        # 构建带上下文的 prompt
        _ = self._build_conversation(prompt)
        response = llm_query(use_config=self.config, msgs=_)

        # 获取生成的响应文本
        agent_response_text = response.choices[0].message.content

        # 将当前对话存入历史中
        if self.use_memory:
            self.history.append({"role": "assistant", "content": agent_response_text})

        return agent_response_text

    def get_response(self, user_input, max_tokens=2048):
        """生成并返回 LLM 的响应，使用多轮对话的上下文。"""

        # 构建带上下文的 prompt
        _ = self._build_conversation(user_input)
        response = llm_query(use_config=self.config, msgs=_)

        # 获取生成的响应文本
        agent_response_text = response.choices[0].message.content

        # 将当前对话存入历史中
        if self.use_memory:
            self.history.append({"role": "assistant", "content": agent_response_text})

        return agent_response_text

    def clear_history(self):
        """清空对话历史。"""
        self.history = self.default_msgs


def chatbot():
    PAG = PaperAnalysisGenerator_Agent(default_config)
    print("Input 'exit' to terminate the process! (without the quotes)")
    while 1:
        prompt = input()
        if prompt.lower() == "exit":
            break
        response = PAG(prompt)
        print(response)


def scorer():
    # file_content = pdf2txt(directory + filename)

    for image_element in image_elements:
        msgs = copy.deepcopy(PAG.default_msgs)
        response = llm_query_img(
            msgs=msgs, file=[image_element.file_path], prompt=scorer_inst_1
        )
        text = response.choices[0].message.content
        if text.startswith("{"):
            aaa = ast.literal_eval(text)
            image_element.score1 = float(aaa["score"])
        msgs.append({"role": "system", "content": PAG.article})
        response = llm_query_img(
            msgs=msgs, file=[image_element.file_path], prompt=scorer_inst_2
        )
        text = response.choices[0].message.content
        print("IMAGE:\n", image_element.file_path)
        print(image_element.caption)
        print("TEXT:\n", text)
        if text.startswith("{"):
            aaa = ast.literal_eval(text)
            image_element.score2 = float(aaa["score"])
            image_element.choose = aaa["paragraph"]

    for image_element in image_elements:
        print(image_element.file_path, image_element.score1, image_element.score2)


def insert_image(threshold=0.5, verbose=False, save=False):
    for i, image_element in enumerate(image_elements):
        # if image_element.score1 >= threshold and image_element.score2 >= threshold:
        if image_element.score2 >= threshold:
            PAG.paragraphs_image[image_element.choose - 1].append(i)
    # 保存paragraphs_image到文件
    if verbose:
        print(json.dumps(PAG.paragraphs_image, indent=4, ensure_ascii=False))
    if save:
        with open(
            output_directory + "paragraph_image.json", "w", encoding="utf-8"
        ) as f:
            f.write(json.dumps(PAG.paragraphs_image, indent=4, ensure_ascii=False))


def output_article(image_elements):
    output_path = output_directory + "Article_" + filename[:-4] + ".md"
    with open(output_path, "w", encoding="utf-8") as f:
        for i, paragraph in enumerate(PAG.paragraphs):
            # 输出到终端当前正在执行的段落序号
            print(f"Paragraph {i + 1} is being processed.")

            f.write(paragraph + "\n\n")
            if PAG.paragraphs_image[i]:
                for x in PAG.paragraphs_image[i]:
                    f.write(
                        f"![{image_elements[x].caption}](./image/{image_elements[x].filename})\n\n"
                    )


directory = "./data/"
filename = "2024.acl-long.173.pdf"
# filename = "ToolkenGPT_Augmenting_Frozen_Language_Models_with_Massive_Tools_via_Tool_Embeddings_66f158bf470b968b4cb582e2_main.pdf"
# filename = "DoT.pdf"

# filename = "analogykb.pdf"
# filename = "EMNLP24_ordered_information_extraction.pdf"
# filename = "QWEN2-VL.pdf"
filename = "analogykb.pdf"
# filename = (
#     "Beneath Surface Similarity- Large Language Models Make Reasonable Scientific.pdf"
# )

# filename = (
#     "AutoScraper- A Progressive Understanding Web Agent for Web Scraper Generation.pdf"
# )
# filename = "CONSTRUCTURE - Benchmarking CONcept STRUCTUre REasoning for Multimodal Large Language Models.pdf"
# filename = "DetectBench - Can Large Language Model Detect and Piece Together Implicit Evidence?.pdf"
# filename = "From Complex to Simple - Enhancing Multi-Constraint Complex Instruction Following Ability of Large Language Models.pdf"
# filename = "Is There a One-Model-Fits-All Approach to Information Extraction? Revisiting Task Definition Biases.pdf"


current_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())

print(current_time)
output_directory = "./output/" + current_time + "-" + filename[:-4] + "/"

if not os.path.exists(output_directory):
    os.mkdir(output_directory)
    print(f"Created directory:\n{output_directory}")
else:
    print(f"Directory already exists:\n{output_directory}")


def stage_verbose(text):
    print("-" * 20 + text + "-" * 20)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"程序运行时间为: {execution_time} 秒")


if __name__ == "__main__":
    start_time = time.time()

    # chatbot()

    file = os.path.join(directory, filename)
    PAG = PaperAnalysisGenerator(file)

    # ##文本生成
    PAG.get_summary()

    output_file = output_directory + "Summary_" + filename[:-4] + ".md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(PAG.summary)

    # plan stage
    PAG.get_plan()

    output_file = output_directory + "Outline_" + filename[:-4] + ".md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(PAG.plan)

    # writing stage
    for i in tqdm(range(PAG.N), desc="Gernerating paragraphs"):
        PAG.write_paragraph(i)
    PAG.get_article()
    print("Paragraphs_number:", PAG.N)
    print("Article_length:", len(PAG.article))

    output_path = output_directory + "Article_" + filename[:-4] + "_text.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(PAG.article)

    stage_verbose("text generated.")

    # exit(0)
    # 视觉元素处理
    page_list, image_list = extract_image(file, PAG.page_number, output_directory)
    print(page_list[0])
    print(image_list[0])
    page_elements = []
    image_elements = []
    for item in page_list:
        page_elements.append(PageElement(item["page_number"], item["file_path"]))
    for item in image_list:
        image_elements.append(
            ImageElement(
                file_path=item["path"],
                type=item["type"],
                caption=item["caption"],
                page_number=item["page_number"],
            )
        )
    stage_verbose("images extracted.")

    # 图文结合
    scorer()

    THRESHOLD = 0.7
    insert_image(threshold=THRESHOLD, verbose=True, save=True)
    stage_verbose("images inserted.")

    # 生成文章
    output_article(image_elements)
    stage_verbose("article Generated!")
