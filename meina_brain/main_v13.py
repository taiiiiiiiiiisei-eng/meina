import numpy as np
import json
import os

print("めいなブレイン v1.3 起動")

# =========================
# めいなの基本知識
# =========================

knowledge = {
    "めいなって何": "私はあなたが作っているAIアシスタント、めいなです！",
    "めいなとは": "私はあなたが作っているAIアシスタント、めいなです！",
    "あなたは誰": "私はめいなです！",
    "名前は": "私の名前はめいなです！",
    "誰": "私はめいなです！",
    "何ができる": "今は会話、分類、記憶ができます。これからもっと進化します！",
}

# =========================
# AI分類データ
# =========================

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
# 長期記憶
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
print("長期記憶：", len(memories))
print("知識：", len(knowledge))


# =========================
# 会話
# =========================

last_user = ""
last_meina = ""

while True:

    text = input("あなた：").strip()

    if text == "終了":
        print("めいな：終了します。")
        break


    # =====================
    # 学習
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
            print("めいな：")
            print("『覚えて: 質問 => 答え』")
            print("の形で教えてください。")

        continue


    # =====================
    # 文脈を使った簡単な応答
    # =====================

    if text in ["それ", "それは？", "さっきの", "さっきのやつ"]:

        if last_user:
            print("めいな：さっきの話ですね。")
            print("めいな：", last_meina)
        else:
            print("めいな：まだ前の話がありません。")

        continue


    # =====================
    # 基本知識
    # =====================

    knowledge_answer = None

    for question, answer in knowledge.items():

        common = sum(1 for c in text if c in question)

        if common >= 3:
            knowledge_answer = answer
            break

    if knowledge_answer is not None:

        print("めいな：", knowledge_answer)

        last_user = text
        last_meina = knowledge_answer

        continue


    # =====================
    # 長期記憶検索
    # =====================

    found_answer = None
    best_score = 0

    for question, answer in memories.items():

        common = sum(
            1 for c in text
            if c in question
        )

        unique_question = len(set(question))

        if unique_question > 0:
            score = common / unique_question
        else:
            score = 0

        if score > best_score:
            best_score = score
            found_answer = answer

    if found_answer is not None and best_score >= 0.3:

        print("めいな：", found_answer)

        last_user = text
        last_meina = found_answer

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

    confidence = float(probs[index])

    print("AIの判断：", names[index])
    print("確信度：", round(confidence, 3))


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

    answer = responses[index]

    print("めいな：", answer)

    last_user = text
    last_meina = answer