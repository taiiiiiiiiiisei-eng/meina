import json
import os
import numpy as np

print("めいなブレイン v2.0 起動")
print("文脈学習型単語ベクトル：ON")
print("")

# =========================================================
# 知識
# =========================================================

knowledge = {
    "めいなって何": "私はめいなブレインです。少しずつ自分で学習できるAIを目指しています。",
    "めいなとは": "私はめいなブレインです。",
    "あなたは誰": "私はめいなです。",
    "名前は": "私の名前はめいなです。",
    "誰": "私はめいなです。",
    "何ができる": "会話、記憶、分類、文脈理解、単語ベクトルなどを扱えます。"
}

# =========================================================
# 学習データ
# =========================================================

data = [
    ("あいさつ", "こんにちは"),
    ("あいさつ", "おはよう"),
    ("あいさつ", "こんばんは"),
    ("あいさつ", "やあ"),
    ("あいさつ", "どうも"),

    ("質問", "元気？"),
    ("質問", "名前は？"),
    ("質問", "好きなゲームは？"),
    ("質問", "好きなゲーム教えて"),
    ("質問", "ゲーム何が好き"),

    ("感謝", "ありがとう"),
    ("感謝", "ありがと"),
    ("感謝", "助かった"),
    ("感謝", "サンキュー"),

    ("命令", "メモ帳を開いて"),
    ("命令", "メモ帳開いて"),
    ("命令", "メモ帳を起動して"),
    ("命令", "ブラウザを開いて"),
    ("命令", "ゲームを起動して"),

    ("雑談", "今日は暇だね"),
    ("雑談", "最近どう？"),
    ("雑談", "ゲーム楽しいね"),
    ("雑談", "暇だな"),

    # v2.0 文脈学習用コーパス
    ("学習", "ゲーム 楽しい 好き"),
    ("学習", "ゲーム 面白い 楽しい"),
    ("学習", "ゲーム 遊ぶ 好き"),
    ("学習", "ゲーム 起動 開く"),
    ("学習", "メモ帳 開く 起動"),
    ("学習", "メモ帳 使う 書く"),
    ("学習", "ブラウザ 開く 起動"),
    ("学習", "こんにちは おはよう こんばんは"),
    ("学習", "ありがとう 助かった"),
    ("学習", "名前 めいな"),
]

names = ["あいさつ", "質問", "感謝", "命令", "雑談"]

# =========================================================
# 長期記憶
# =========================================================

MEMORY_FILE = "brain_memory.json"

if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            brain_memory = json.load(f)
    except Exception:
        brain_memory = {}
else:
    brain_memory = {}


def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(brain_memory, f, ensure_ascii=False, indent=2)


# =========================================================
# 会話履歴
# =========================================================

conversation_history = []
MAX_HISTORY = 10


def add_history(user_text, meina_text, is_context=False):
    conversation_history.append({
        "user": user_text,
        "meina": meina_text,
        "is_context": is_context
    })

    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)


# =========================================================
# 文脈
# =========================================================

context_words = {
    "それ", "それは？", "それって？", "さっきの", "さっきの話",
    "さっきのやつ", "前の話", "前のやつ", "これ", "これは？",
    "どういう意味？", "どういう意味", "なんで？", "なんで",
    "どうして？", "どうして", "理由は？", "理由は",
    "もう一回", "もう一度", "詳しく", "詳しく教えて"
}


def get_topic():
    for item in reversed(conversation_history):
        if not item["is_context"] and item["user"] not in context_words:
            return item
    return None


# =========================================================
# 単語分解
# =========================================================

base_words = [
    "こんにちは", "おはよう", "こんばんは", "やあ", "どうも",
    "元気", "名前", "好き", "ゲーム", "教えて", "何",
    "ありがとう", "ありがと", "助かった", "サンキュー",
    "メモ帳", "開いて", "開く", "起動", "ブラウザ",
    "暇", "最近", "楽しい", "面白い", "遊ぶ", "使う", "書く",
    "めいな", "今日", "どう", "です", "ね", "よ", "を", "は",
    "が", "に", "の", "って", "何が好き"
]

# 学習コーパスに使う単語
for _, sentence in data:
    for token in sentence.replace("？", "").replace("。", "").split():
        if token not in base_words:
            base_words.append(token)


def tokenize(text):
    text = text.strip()

    if not text:
        return []

    split_words = text.split()
    if len(split_words) > 1:
        return split_words

    remaining = text
    words = []

    sorted_words = sorted(base_words, key=len, reverse=True)

    while remaining:
        found = False

        for word in sorted_words:
            if remaining.startswith(word):
                words.append(word)
                remaining = remaining[len(word):]
                found = True
                break

        if not found:
            # 記号を単語にしない
            if remaining[0] not in "？?！!。、，,":
                words.append(remaining[0])
            remaining = remaining[1:]

    return words


# =========================================================
# 語彙
# =========================================================

all_words = set()

for _, sentence in data:
    for word in tokenize(sentence):
        all_words.add(word)

for word in base_words:
    all_words.add(word)

vocab = sorted(all_words)
word_to_id = {word: i for i, word in enumerate(vocab)}
id_to_word = {i: word for word, i in word_to_id.items()}

print("語彙数：", len(vocab))
print("")


# =========================================================
# v2.0 Skip-gram風 単語ベクトル学習
# 「同じ文章だから全部近づける」をやめ、
# 近くに出る単語を予測できるように学習する
# =========================================================

VECTOR_SIZE = 32
WINDOW_SIZE = 2
NEGATIVE_SAMPLES = 3
VECTOR_EPOCHS = 800
VECTOR_LR = 0.025

rng = np.random.default_rng(42)

input_vectors = (
    rng.normal(0, 0.08, (len(vocab), VECTOR_SIZE))
)

output_vectors = np.zeros(
    (len(vocab), VECTOR_SIZE),
    dtype=np.float64
)


def sigmoid(x):
    x = np.clip(x, -15, 15)
    return 1.0 / (1.0 + np.exp(-x))


# 学習用文章だけを作る
corpus = []

for _, sentence in data:
    words = tokenize(sentence)
    ids = [word_to_id[w] for w in words if w in word_to_id]
    if len(ids) >= 2:
        corpus.append(ids)


# 正例：(中心語, 近くの語)
positive_pairs = []

for sentence_ids in corpus:
    for center_pos, center_id in enumerate(sentence_ids):
        start = max(0, center_pos - WINDOW_SIZE)
        end = min(len(sentence_ids), center_pos + WINDOW_SIZE + 1)

        for context_pos in range(start, end):
            if context_pos == center_pos:
                continue

            context_id = sentence_ids[context_pos]
            positive_pairs.append((center_id, context_id))


# 負例を作るための単語確率
freq = np.ones(len(vocab), dtype=np.float64)

for sentence_ids in corpus:
    for word_id in sentence_ids:
        freq[word_id] += 1

negative_prob = freq ** 0.75
negative_prob /= negative_prob.sum()

print("文脈ペア数：", len(positive_pairs))
print("単語ベクトル学習開始...")


for epoch in range(VECTOR_EPOCHS):
    rng.shuffle(positive_pairs)

    for center_id, context_id in positive_pairs:

        # -------------------------
        # 正例
        # -------------------------
        center = input_vectors[center_id].copy()
        context = output_vectors[context_id].copy()

        score = np.dot(center, context)
        p = sigmoid(score)

        # loss = -log(sigmoid(score))
        grad = p - 1.0

        input_vectors[center_id] -= VECTOR_LR * grad * context
        output_vectors[context_id] -= VECTOR_LR * grad * center

        # -------------------------
        # 負例
        # -------------------------
        negative_ids = rng.choice(
            len(vocab),
            size=NEGATIVE_SAMPLES,
            p=negative_prob
        )

        for negative_id in negative_ids:

            if negative_id == context_id:
                continue

            center = input_vectors[center_id].copy()
            negative = output_vectors[negative_id].copy()

            score = np.dot(center, negative)
            p = sigmoid(score)

            # 負例の目標値は0
            grad = p

            input_vectors[center_id] -= VECTOR_LR * grad * negative
            output_vectors[negative_id] -= VECTOR_LR * grad * center


# 最終的な単語ベクトルは入力側を使用
word_vectors = input_vectors.copy()

print("単語ベクトル学習完了！")
print("")


# =========================================================
# コサイン類似度
# =========================================================

def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


# =========================================================
# ベクトル確認
# =========================================================

print("【v2.0 学習後の単語ベクトル】")

for word in ["ゲーム", "楽しい", "メモ帳", "開く", "こんにちは", "めいな"]:
    if word in word_to_id:
        vector = word_vectors[word_to_id[word]]
        print(word, "→", np.round(vector[:8], 3), "...")

print("")


# =========================================================
# ニューラルネットワーク
# =========================================================

INPUT_SIZE = VECTOR_SIZE
HIDDEN_SIZE = 32
OUTPUT_SIZE = len(names)

W1 = rng.normal(0, 0.1, (INPUT_SIZE, HIDDEN_SIZE))
b1 = np.zeros(HIDDEN_SIZE)

W2 = rng.normal(0, 0.1, (HIDDEN_SIZE, OUTPUT_SIZE))
b2 = np.zeros(OUTPUT_SIZE)


def softmax(x):
    x = x - np.max(x)
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x)


def relu(x):
    return np.maximum(0, x)


def relu_derivative(x):
    return (x > 0).astype(float)


def sentence_to_vector(text):
    words = tokenize(text)
    vectors = []

    for word in words:
        if word in word_to_id:
            vectors.append(word_vectors[word_to_id[word]])

    if not vectors:
        return np.zeros(VECTOR_SIZE)

    return np.mean(vectors, axis=0)


# 学習データは元の5分類だけ
classification_data = [
    (label, sentence)
    for label, sentence in data
    if label in names
]

training_data = []

for label, sentence in classification_data:
    x = sentence_to_vector(sentence)

    y = np.zeros(OUTPUT_SIZE)
    y[names.index(label)] = 1

    training_data.append((x, y))


learning_rate = 0.05
epochs = 3000

for epoch in range(epochs):
    for x, y in training_data:

        z1 = np.dot(x, W1) + b1
        h = relu(z1)

        z2 = np.dot(h, W2) + b2
        pred = softmax(z2)

        dz2 = pred - y

        dW2 = np.outer(h, dz2)
        db2 = dz2

        dh = np.dot(W2, dz2)
        dz1 = dh * relu_derivative(z1)

        dW1 = np.outer(x, dz1)
        db1 = dz1

        W2 -= learning_rate * dW2
        b2 -= learning_rate * db2

        W1 -= learning_rate * dW1
        b1 -= learning_rate * db1

print("ニューラルネットワーク学習完了！")
print("")


# =========================================================
# AI分類
# =========================================================

def classify(text):
    x = sentence_to_vector(text)

    z1 = np.dot(x, W1) + b1
    h = relu(z1)

    z2 = np.dot(h, W2) + b2
    pred = softmax(z2)

    index = int(np.argmax(pred))
    confidence = float(pred[index])

    return names[index], confidence


# =========================================================
# 記憶検索
# =========================================================

def memory_search(text):
    if not brain_memory:
        return None

    best_key = None
    best_score = 0

    for key in brain_memory:

        a = set(text)
        b = set(key)

        if not a or not b:
            continue

        score = len(a & b) / len(a | b)

        if score > best_score:
            best_score = score
            best_key = key

    if best_score >= 0.3:
        return brain_memory[best_key]

    return None


# =========================================================
# メインループ
# =========================================================

while True:

    text = input("あなた：").strip()

    if not text:
        continue

    # -------------------------
    # 終了
    # -------------------------

    if text == "終了":
        print("めいな：またね！")
        break

    # -------------------------
    # 単語ベクトル
    # -------------------------

    if text.startswith("単語 "):

        target = text[3:].strip()
        words = tokenize(target)

        print("めいな：単語をベクトルに変換します。")

        for word in words:

            if word in word_to_id:
                vector = word_vectors[word_to_id[word]]

                print(
                    word,
                    "→",
                    np.round(vector, 3)
                )
            else:
                print(word, "→ 未登録")

        continue

    # -------------------------
    # 類似度
    # -------------------------

    if text.startswith("類似度 "):

        parts = text[4:].strip().split()

        if len(parts) < 2:
            print(
                "めいな：「類似度 ゲーム 楽しい」のように入力してください。"
            )
            continue

        word_a = parts[0]
        word_b = parts[1]

        if word_a not in word_to_id or word_b not in word_to_id:
            print("めいな：どちらかの単語がまだ登録されていません。")
            continue

        score = cosine_similarity(
            word_vectors[word_to_id[word_a]],
            word_vectors[word_to_id[word_b]]
        )

        print("めいな：", word_a, "↔", word_b)
        print("類似度：", round(score, 4))

        continue

    # -------------------------
    # 近い単語
    # -------------------------

    if text.startswith("近い "):

        target = text[3:].strip()

        if target not in word_to_id:
            print("めいな：その単語はまだ知りません。")
            continue

        target_vector = word_vectors[word_to_id[target]]
        results = []

        for word in vocab:

            if word == target:
                continue

            score = cosine_similarity(
                target_vector,
                word_vectors[word_to_id[word]]
            )

            results.append((word, score))

        results.sort(key=lambda x: x[1], reverse=True)

        print("めいな：「" + target + "」に近い単語")

        for word, score in results[:5]:
            print(word, "→", round(score, 4))

        continue

    # -------------------------
    # 語彙
    # -------------------------

    if text == "語彙":

        print("めいな：現在の語彙です。")
        print(", ".join(vocab))
        continue

    # -------------------------
    # 履歴
    # -------------------------

    if text == "履歴":

        print("めいな：会話履歴です。")

        if not conversation_history:
            print("履歴はありません。")
        else:
            for item in conversation_history:
                print("あなた：", item["user"])
                print("めいな：", item["meina"])

        continue

    # -------------------------
    # 記憶
    # -------------------------

    if text.startswith("覚えて:"):

        content = text.replace("覚えて:", "", 1).strip()

        if "=>" in content:

            key, value = content.split("=>", 1)

            key = key.strip()
            value = value.strip()

            brain_memory[key] = value
            save_memory()

            reply = "覚えました！"

        else:
            reply = "「覚えて: 質問 => 答え」の形で教えてください。"

        print("めいな：" + reply)
        add_history(text, reply)

        continue

    # -------------------------
    # 文脈
    # -------------------------

    if text in context_words:

        topic = get_topic()

        if topic:

            original = topic["user"]
            previous_reply = topic["meina"]

            if text in {
                "なんで？", "なんで",
                "どうして？", "どうして",
                "理由は？", "理由は"
            }:
                reply = "「" + original + "」についての理由ですね。"

            elif text in {"詳しく", "詳しく教えて"}:
                reply = (
                    "「" + original + "」についてですね。"
                    "さっき私は「" + previous_reply + "」と答えました。"
                )

            elif text in {"もう一回", "もう一度"}:
                reply = previous_reply

            else:
                reply = "「" + original + "」についてですね。"

        else:
            reply = "まだ話題がありません。"

        print("めいな：" + reply)

        add_history(
            text,
            reply,
            is_context=True
        )

        continue

    # -------------------------
    # 知識
    # -------------------------

    knowledge_reply = None

    for key, value in knowledge.items():
        if key in text:
            knowledge_reply = value
            break

    if knowledge_reply:

        print("めいな：" + knowledge_reply)

        add_history(
            text,
            knowledge_reply
        )

        continue

    # -------------------------
    # 長期記憶
    # -------------------------

    remembered = memory_search(text)

    if remembered:

        print("めいな：覚えています。")
        print("めいな：" + remembered)

        add_history(
            text,
            remembered
        )

        continue

    # -------------------------
    # AI分類
    # -------------------------

    intent, confidence = classify(text)

    print(
        "AI判断：",
        intent,
        "信頼度：",
        round(confidence, 3)
    )

    # -------------------------
    # 返答
    # -------------------------

    if intent == "あいさつ":
        reply = "こんにちは！"

    elif intent == "質問":
        reply = "質問ですね。もう少し詳しく教えてください。"

    elif intent == "感謝":
        reply = "どういたしまして！"

    elif intent == "命令":
        reply = "命令を受け取りました。"

    elif intent == "雑談":
        reply = "そうですね！"

    else:
        reply = "まだよく分かりません。"

    print("めいな：" + reply)

    add_history(
        text,
        reply
    )
