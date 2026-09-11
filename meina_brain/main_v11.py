import numpy as np
import json
import os

print("めいなブレイン v1.1 起動")

# 0=あいさつ 1=質問 2=感謝 3=命令 4=雑談
data = [
    ("こんにちは", 0),
    ("おはよう", 0),
    ("こんばんは", 0),
    ("やあ", 0),
    ("どうも", 0),

    ("元気？", 1),
    ("名前は？", 1),
    ("好きなゲームは？", 1),
    ("好きなゲーム教えて", 1),
    ("ゲーム何が好き", 1),

    ("ありがとう", 2),
    ("ありがと", 2),
    ("助かった", 2),
    ("サンキュー", 2),

    ("メモ帳を開いて", 3),
    ("メモ帳開いて", 3),
    ("メモ帳を起動して", 3),
    ("ブラウザを開いて", 3),
    ("ゲームを起動して", 3),

    ("今日は暇だね", 4),
    ("最近どう？", 4),
    ("ゲーム楽しいね", 4),
    ("暇だな", 4),
]

names = ["あいさつ", "質問", "感謝", "命令", "雑談"]

# =========================
# 記憶
# =========================

memory_file = "brain_memory.json"

if os.path.exists(memory_file):
    with open(memory_file, "r", encoding="utf-8") as f:
        memories = json.load(f)
else:
    memories = {}


# =========================
# 文字をベクトル化
# =========================

vocab = sorted(set(c for text, _ in data for c in text))
char_to_id = {c: i for i, c in enumerate(vocab)}

def text_to_vector(text):
    x = np.zeros(len(vocab))

    for c in text:
        if c in char_to_id:
            x[char_to_id[c]] = 1

    return x


X = np.array([text_to_vector(text) for text, _ in data])
Y = np.array([label for _, label in data])


# =========================
# ニューラルネットワーク
# =========================

input_size = len(vocab)
hidden_size = 32
output_size = 5

W1 = np.random.randn(input_size, hidden_size) * 0.1
b1 = np.zeros(hidden_size)

W2 = np.random.randn(hidden_size, output_size) * 0.1
b2 = np.zeros(output_size)


def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=1, keepdims=True)


# =========================
# 学習
# =========================

for epoch in range(10000):

    hidden = X @ W1 + b1
    hidden = np.maximum(hidden, 0)

    scores = hidden @ W2 + b2
    probs = softmax(scores)

    error = probs.copy()
    error[np.arange(len(Y)), Y] -= 1

    dW2 = hidden.T @ error / len(Y)
    db2 = np.mean(error, axis=0)

    dhidden = error @ W2.T
    dhidden[hidden <= 0] = 0

    dW1 = X.T @ dhidden / len(Y)
    db1 = np.mean(dhidden, axis=0)

    learning_rate = 0.1

    W1 -= learning_rate * dW1
    b1 -= learning_rate * db1

    W2 -= learning_rate * dW2
    b2 -= learning_rate * db2


print("学習完了！")
print("記憶数：", len(memories))


# =========================
# 会話
# =========================

while True:

    text = input("あなた：")

    # 終了
    if text == "終了":
        print("めいな：終了します。")
        break


    # =====================
    # 学習モード
    # =====================

    if text.startswith("覚えて:"):

        content = text.replace("覚えて:", "", 1).strip()

        if "=>" in content:

            question, answer = content.split("=>", 1)

            question = question.strip()
            answer = answer.strip()

            memories[question] = answer

            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(
                    memories,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print("めいな：覚えました！")

        else:

            print(
                "めいな："
                "『覚えて: 質問 => 答え』"
                "の形で教えてください。"
            )

        continue


    # =====================
    # 記憶を検索
    # =====================

    found_answer = None
    best_score = 0

    for question, answer in memories.items():

        # 共通している文字
        common = sum(
            1 for c in text
            if c in question
        )

        # 質問側の文字数
        unique_question = len(set(question))

        if unique_question > 0:
            score = common / unique_question
        else:
            score = 0

        if score > best_score:
            best_score = score
            found_answer = answer


    # 十分似ていたら記憶を使う
    if found_answer is not None and best_score >= 0.3:

        print("めいな：", found_answer)
        continue


    # =====================
    # AI判断
    # =====================

    x = text_to_vector(text).reshape(1, -1)

    hidden = x @ W1 + b1
    hidden = np.maximum(hidden, 0)

    scores = hidden @ W2 + b2
    probs = softmax(scores)[0]

    index = np.argmax(probs)

    print("AIの判断：", names[index])
    print("確信度：", round(float(probs[index]), 3))


    # =====================
    # 返事
    # =====================

    responses = {
        0: "こんにちは！",
        1: "それについて考えます！",
        2: "どういたしまして！",
        3: "了解しました！",
        4: "そうですね！"
    }

    print("めいな：", responses[index])