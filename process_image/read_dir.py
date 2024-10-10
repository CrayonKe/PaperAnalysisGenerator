# Define the file path
import json


def read_res(file_path):

    with open(file_path, "r") as f:
        txt = f.read()
    bbox_table = []
    bbox_figure = []

    page_information = list(map(json.loads, txt.splitlines()))
    for item in page_information:
        if item["type"] == "figure":
            bbox_figure.append(item["bbox"])
        elif item["type"] == "table":
            bbox_table.append(item["bbox"])

    # print(table_list)
    if not bbox_table and not bbox_figure:
        return None, None
    else:
        return bbox_table, bbox_figure


def read_ref(file_path):

    with open(file_path, "r") as f:
        txt = f.read()
    ref = False

    page_information = list(map(json.loads, txt.splitlines()))
    for item in page_information:
        if item["type"] == "title":
            if item["res"]:
                if item["res"][0]["text"] == "References":
                    ref = True

    return ref
    # print(table_list)


file_path = "./output1/page_1/res_0.txt"
