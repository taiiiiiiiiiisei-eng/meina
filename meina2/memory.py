import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MEMORY_FILE = os.path.join(
    BASE_DIR,
    "memory.json"
)


def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return []

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

            return []

    except Exception:
        return []


def save_memory(text):

    memories = load_memory()

    memories.append({
        "text": text,
        "date": datetime.now().isoformat()
    })

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memories,
            f,
            ensure_ascii=False,
            indent=2
        )

    return "覚えておきます。"


def search_memory(query):

    memories = load_memory()

    if not memories:
        return "まだ記憶していることはありません。"

    results = []

    for item in memories:

        text = item.get(
            "text",
            ""
        )

        if query in text:
            results.append(text)

    if not results:

        return (
            "そのことについての"
            "記憶は見つかりませんでした。"
        )

    return "「" + "」「".join(
        results[-5:]
    ) + "」"


def clear_memory():

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            [],
            f,
            ensure_ascii=False,
            indent=2
        )

    return "記憶を削除しました。"