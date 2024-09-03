#!/usr/bin/python3
# coding=utf-8
'''
File: fengze_auto_day_task.py
Author: manx98
Date: 2024/9/3 8:57
cron: * 40 8 * * 1-5
new Env('fengze每一日一题');
'''
import os
import random

from zhipuai import ZhipuAI

import requests

ApiHost = "https://micheng-api.zhongfu.net"

session = requests.Session()
session.headers = {
    "authorization": os.getenv("FZ_AUTH_TOKEN"),
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}

client = ZhipuAI(api_key=os.getenv("FZ_ZHIPU_TOKEN"))


def study_task_list_v2():
    """
    获取任务列表
    :return:
    """
    url = f"{ApiHost}/study/task/list/v2"
    response = session.post(url, json={"page": 1, "pageSize": 15, "name": "", "taskType": [1, 11, 6, 9, 10, 2]}).json()
    try:
        return response["data"]["list"]
    except Exception:
        raise Exception(f"study_task_list_v2: {response}")


def start_exam(task_id, detail_id):
    """
    获取考试内容
    :param task_id:
    :param detail_id:
    :return:
    """
    url = f"{ApiHost}/study/exam/start"
    rsp = session.post(url, json={
        "taskId": task_id,
        "detailId": detail_id,
        "face": "",
    }).json()
    try:
        return rsp["data"]
    except Exception:
        raise Exception(f"start_exam: {rsp}")


def get_question_answer(question_info):
    """
    使用智谱获取问题答案答案
    :param question_info:
    :return:
    """
    options = question_info["options"]
    options_str = "\n".join([f"{option['id']}. {option['title']}" for option in options])
    content = f"""{question_info["title"]}
{options_str}
请直接给出正确答案序号并使用“,”分割
"""
    print(content)
    response = client.chat.completions.create(
        model="glm-4-0520",
        messages=[
            {"role": "user", "content": content},
        ],
        stream=False,
    )
    content = response.choices[0].message.content
    answers = []
    try:
        for choice in content.split(","):
            choice = choice.strip(', \n\t')
            if choice:
                answers.append(int(choice))
    except Exception:
        print(f"invalid AI answer: {content}")
    return answers


def submit_exam(exam_info):
    """
    提交考试信息
    :param exam_info:
    :return:
    """
    url = f"{ApiHost}/study/exam/submit"
    ret = session.post(url, json=exam_info).json()
    print("考试提交成功: ", ret)


def auto_exam():
    tasks = study_task_list_v2()
    if not tasks:
        for task in tasks:
            name = task["taskName"]
            if name.find("保密每日一练") > -1:
                exam_info = start_exam(task["taskId"], task["detailId"])
                exam_info["submitType"] = 2
                for question in exam_info["questions"]:
                    answers = get_question_answer(question)
                    options = question["options"]
                    if answers:
                        for answer in answers:
                            for option in options:
                                if option.get("id") == answer:
                                    option["isRight"] = True
                    else:
                        print("can't get question answer, will random choice one")
                        option = random.choice(options)
                        if option:
                            option["isRight"] = True
                    answers = []
                    for option in options:
                        if option.get("isRight"):
                            answers.append(option["id"])
                    question["answers"] = answers
                    question["userAnswer"] = answers
                submit_exam(exam_info)


if __name__ == '__main__':
    auto_exam()
