import gradio as gr
import time, copy
from llm_api import llm_query
from krypy import 


# 定义处理 PDF 上传的函数
def process_pdf(file):
    # 这里添加处理 PDF 的逻辑
    # 例如，返回文件名作为示例
    return f"PDF content processed: {file.name}"


with gr.Blocks() as demo:
    # 创建左侧列
    with gr.Row():
        # 第一列：用于上传 PDF 和放置按钮
        with gr.Column(scale=2):
            pdf_upload = gr.File(label="Upload PDF")
            process_button = gr.Button("Process PDF")

            def summarize_pdf():
                return llm_query("Summarize the PDF content")

            def plan_pdf():
                return llm_query("Plan based on the PDF content")

            def write_all_paragraphs():
                return llm_query("Write all paragraphs based on the PDF content")

            def write_single_paragraph():
                return llm_query("Write a single paragraph based on the PDF content")

            with gr.Column():
                with gr.Row():
                    btn1 = gr.Button("Summarize")
                    btn2 = gr.Button("Plan")

                with gr.Row():
                    btn3 = gr.Button("Write_all_Paragraph")
                    btn4 = gr.Button("Write_single_Paragraph")

            # btn1.click(summarize_pdf, outputs=chatbot)
            # btn2.click(plan_pdf, outputs=chatbot)
            # btn3.click(write_all_paragraphs, outputs=chatbot)
            # btn4.click(write_single_paragraph, outputs=chatbot)
            @btn1.click
            def btn1_action():
                # text=llm_query())
                return summarize_pdf()
                pass

            # 定义处理 PDF 的事件
            @process_button.click
            def process_uploaded_file(file):
                new_msgs = process_pdf(file)

                return process_pdf(file)

        # 第二列：用于显示聊天历史和聊天输入框
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(type="messages", label="PaperAnalysisGenerator")
            msg = gr.Textbox(placeholder="Type your message...")

            # 定义响应函数
            def respond(message, chat_history):
                try:
                    response = llm_query(msgs=message)
                    bot_message = response.choices[0].message.content
                    chat_history.append({"role": "user", "content": message})
                    chat_history.append({"role": "assistant", "content": bot_message})
                    return "", chat_history
                except Exception as e:
                    # 如果发生错误，将错误信息添加到聊天历史中
                    chat_history.append(
                        {"role": "system", "content": f"Error: {str(e)}"}
                    )

            # 当点击提交按钮时，调用响应函数
            def submit():
                return respond(msg.value, chatbot.value["chat_history"])

            # 当文本框提交时，调用响应函数
            msg.submit(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

            # 创建一个行，用于放置提交和清除按钮
            with gr.Row():
                clear_btn = gr.Button("Clear")
                submit_btn = gr.Button("Submit")
                # 定义按钮点击事件
                submit_btn.click(fn=submit, inputs=[msg], outputs=[chatbot, msg])
                clear_btn.click(fn=lambda: ("", []), inputs=[], outputs=[msg, chatbot])


# 设置界面的标题和描述
demo.title = "Chatbot with PDF Uploader"
demo.description = "Upload a PDF and chat with the bot."
# with gr.Blocks() as demo:
#     with gr.Row():
#         with gr.Column(scale=1):
#             text1 = gr.Textbox()
#             text2 = gr.Textbox()
#         with gr.Column(scale=4):
#             btn1 = gr.Button("Button 1")
#             btn2 = gr.Button("Button 2")
# 启动界面

demo.launch()
