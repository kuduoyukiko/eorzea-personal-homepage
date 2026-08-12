import json
import os
from flask import current_app


def read_json(filename):
    """读取data目录下的JSON文件，返回字典或列表"""
    filepath = os.path.join(current_app.config["DATA_PATH"], filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 若文件不存在，返回默认空结构
        if filename == "site_config.json":
            return {"views": 0, "navbar_bg": "", "navbar_logo": "", "body_bg": ""}
        elif filename == "home.json":
            return {
                "accounts": [
                    {
                        "id": "账号1ID",
                        "server": "服务器1",
                        "region": "大区1",
                        "avatar": "",
                        "standing_image": "",
                    },
                    {
                        "id": "账号2ID",
                        "server": "服务器2",
                        "region": "大区2",
                        "avatar": "",
                        "standing_image": "",
                    },
                ],
                "bg_images": [],
            }
        elif filename == "characters.json":
            return [
                {
                    "name": "角色名1",
                    "free_company": "部队名1",
                    "city": "主城1",
                    "start_date": "2020-01-01",
                    "badge_image": "",
                },
                {
                    "name": "角色名2",
                    "free_company": "部队名2",
                    "city": "主城2",
                    "start_date": "2020-02-01",
                    "badge_image": "",
                },
            ]
        elif filename == "jobs.json":
            # 预定义所有职业（后续可修改等级）
            return {
                "tanks": [
                    {"full_name": "战士", "abbr": "WAR", "level": 90, "icon": ""},
                    {"full_name": "骑士", "abbr": "PLD", "level": 90, "icon": ""},
                    {"full_name": "暗黑骑士", "abbr": "DRK", "level": 90, "icon": ""},
                    {"full_name": "枪刃师", "abbr": "GNB", "level": 90, "icon": ""},
                ],
                "healers": [
                    {"full_name": "白魔法师", "abbr": "WHM", "level": 90, "icon": ""},
                    {"full_name": "学者", "abbr": "SCH", "level": 90, "icon": ""},
                    {"full_name": "占星术士", "abbr": "AST", "level": 90, "icon": ""},
                    {"full_name": "贤者", "abbr": "SGE", "level": 90, "icon": ""},
                ],
                "melee": [
                    {"full_name": "武僧", "abbr": "MNK", "level": 90, "icon": ""},
                    {"full_name": "龙骑士", "abbr": "DRG", "level": 90, "icon": ""},
                    {"full_name": "忍者", "abbr": "NIN", "level": 90, "icon": ""},
                    {"full_name": "武士", "abbr": "SAM", "level": 90, "icon": ""},
                    {"full_name": "钐镰客", "abbr": "RPR", "level": 90, "icon": ""},
                ],
                "ranged_physical": [
                    {"full_name": "吟游诗人", "abbr": "BRD", "level": 90, "icon": ""},
                    {"full_name": "机工士", "abbr": "MCH", "level": 90, "icon": ""},
                    {"full_name": "舞者", "abbr": "DNC", "level": 90, "icon": ""},
                ],
                "ranged_magic": [
                    {"full_name": "黑魔法师", "abbr": "BLM", "level": 90, "icon": ""},
                    {"full_name": "召唤师", "abbr": "SMN", "level": 90, "icon": ""},
                    {"full_name": "赤魔法师", "abbr": "RDM", "level": 90, "icon": ""},
                ],
                "crafters": [
                    {"full_name": "铸甲匠", "abbr": "ARM", "level": 90, "icon": ""},
                    {"full_name": "锻铁匠", "abbr": "BSM", "level": 90, "icon": ""},
                    {"full_name": "雕金匠", "abbr": "GSM", "level": 90, "icon": ""},
                    {"full_name": "制革匠", "abbr": "LTW", "level": 90, "icon": ""},
                    {"full_name": "裁衣匠", "abbr": "WVR", "level": 90, "icon": ""},
                    {"full_name": "炼金术士", "abbr": "ALC", "level": 90, "icon": ""},
                    {"full_name": "厨师", "abbr": "CUL", "level": 90, "icon": ""},
                    {"full_name": "刻木匠", "abbr": "CRP", "level": 90, "icon": ""},
                ],
                "gatherers": [
                    {"full_name": "采矿工", "abbr": "MIN", "level": 90, "icon": ""},
                    {"full_name": "园艺工", "abbr": "BTN", "level": 90, "icon": ""},
                    {"full_name": "捕鱼人", "abbr": "FSH", "level": 90, "icon": ""},
                ],
            }
        elif filename == "social.json":
            return {
                "shizhijia": "",
                "shizhijia_image": "",
                "steam": "",
                "steam_image": "",
                "oopz": "",
                "oopz_image": "",
                "qq": "",
                "qq_image": "",
                "bilibili": "",
                "bilibili_image": "",
                "bilibili_live": "",
                "bilibili_live_image": "",
            }
        elif filename == "messages.json":
            return []
        elif filename == "music.json":
            return {
                "defaultSource": "local",
                "sources": [
                    {"id": "local", "name": "本地", "icon": "fa-solid fa-music", "playlist": []},
                    {"id": "netease", "name": "网易云", "icon": "fa-brands fa-napster", "embedType": "playlist", "embedId": "", "autoPlay": False},
                    {"id": "qqmusic", "name": "QQ音乐", "icon": "fa-brands fa-qq", "embedType": "song", "embedId": "", "autoPlay": False}
                ]
            }
        elif filename == "gallery.json":
            return []
        elif filename == "intro.json":
            return {"content": "这里是我的个人介绍，可以填写一些关于自己的信息。"}
        else:
            return {}  # 默认空字典


def write_json(filename, data):
    """写入数据到JSON文件"""
    filepath = os.path.join(current_app.config["DATA_PATH"], filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
