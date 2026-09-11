import json
import os
import numpy as np

print("めいなブレイン v2.4 起動")
print("文章意味＋語順＋役割スロット学習システム：ON")
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
    "何ができる": "会話、記憶、分類、文脈理解、文章ベクトルなどを扱えます。"
}

# =========================================================
# 分類データ
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
    ("雑談", "暇だな")
]

names = ["あいさつ", "質問", "感謝", "命令", "雑談"]

# =========================================================
# 文章意味学習用コーパス
# =========================================================

corpus_texts = [
    "ゲーム 楽しい 好き",
    "ゲーム 面白い 楽しい",
    "ゲーム 遊ぶ 好き",
    "ゲーム 起動 開く",
    "ゲーム プレイ 遊ぶ",
    "メモ帳 開く 起動",
    "メモ帳 使う 書く",
    "メモ帳 書く 使う",
    "ブラウザ 開く 起動",
    "ブラウザ 検索 インターネット",
    "こんにちは おはよう こんばんは",
    "こんにちは やあ どうも",
    "ありがとう 助かった",
    "名前 めいな",
    "めいな AI アシスタント",
    "AI 学習 賢い"
]

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
    "プレイ", "検索", "インターネット", "めいな", "AI",
    "アシスタント", "学習", "賢い", "今日", "どう", "です",
    "ね", "よ", "を", "は", "が", "に", "の", "って",
    "何が好き"
]

for sentence in corpus_texts:
    for word in sentence.split():
        if word not in base_words:
            base_words.append(word)


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

for sentence in corpus_texts:
    for word in tokenize(sentence):
        all_words.add(word)

for word in base_words:
    all_words.add(word)

vocab = sorted(all_words)

word_to_id = {
    word: i for i, word in enumerate(vocab)
}

id_to_word = {
    i: word for word, i in word_to_id.items()
}

print("語彙数：", len(vocab))
print("")


# =========================================================
# v2.1 単語ベクトル
# =========================================================

VECTOR_SIZE = 32
WINDOW_SIZE = 2
NEGATIVE_SAMPLES = 4
VECTOR_EPOCHS = 1000
VECTOR_LR = 0.02

rng = np.random.default_rng(42)

input_vectors = rng.normal(
    0,
    0.08,
    (len(vocab), VECTOR_SIZE)
)

output_vectors = np.zeros(
    (len(vocab), VECTOR_SIZE),
    dtype=np.float64
)


def sigmoid(x):
    x = np.clip(x, -15, 15)
    return 1.0 / (1.0 + np.exp(-x))


# =========================================================
# Skip-gram 学習ペア
# =========================================================

corpus = []

for sentence in corpus_texts:
    words = tokenize(sentence)

    ids = [
        word_to_id[word]
        for word in words
        if word in word_to_id
    ]

    if len(ids) >= 2:
        corpus.append(ids)


positive_pairs = []

for sentence_ids in corpus:

    for center_pos, center_id in enumerate(sentence_ids):

        start = max(
            0,
            center_pos - WINDOW_SIZE
        )

        end = min(
            len(sentence_ids),
            center_pos + WINDOW_SIZE + 1
        )

        for context_pos in range(start, end):

            if context_pos == center_pos:
                continue

            context_id = sentence_ids[context_pos]

            positive_pairs.append(
                (center_id, context_id)
            )


freq = np.ones(
    len(vocab),
    dtype=np.float64
)

for sentence_ids in corpus:
    for word_id in sentence_ids:
        freq[word_id] += 1

negative_prob = freq ** 0.75
negative_prob /= negative_prob.sum()

print("文章数：", len(corpus))
print("文脈ペア数：", len(positive_pairs))
print("")

print("v2.4 単語・文脈・役割・語順学習開始...")


for epoch in range(VECTOR_EPOCHS):

    rng.shuffle(positive_pairs)

    for center_id, context_id in positive_pairs:

        # -------------------------
        # 正例
        # -------------------------

        center = input_vectors[center_id].copy()
        context = output_vectors[context_id].copy()

        score = np.dot(center, context)
        probability = sigmoid(score)

        gradient = probability - 1.0

        input_vectors[center_id] -= (
            VECTOR_LR * gradient * context
        )

        output_vectors[context_id] -= (
            VECTOR_LR * gradient * center
        )

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
            probability = sigmoid(score)

            gradient = probability

            input_vectors[center_id] -= (
                VECTOR_LR * gradient * negative
            )

            output_vectors[negative_id] -= (
                VECTOR_LR * gradient * center
            )


word_vectors = input_vectors.copy()

print("単語・文脈学習完了！")
print("")


# =========================================================
# コサイン類似度
# =========================================================

def cosine_similarity(a, b):

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(
        np.dot(a, b)
        /
        (norm_a * norm_b)
    )


# =========================================================
# 文ベクトル
# =========================================================

def normalize_vector(vector):

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm


def role_relation_vector(words):

    if len(words) < 2:
        return np.zeros(VECTOR_SIZE)

    relations = []

    for i in range(len(words) - 1):

        a = word_vectors[word_to_id[words[i]]]
        b = word_vectors[word_to_id[words[i + 1]]]

        # 前の単語から次の単語への方向を特徴として使う
        relations.append(b - a)

    return np.mean(relations, axis=0)


def sentence_to_vector(text):

    words = tokenize(text)

    valid_words = [
        word for word in words
        if word in word_to_id
    ]

    if not valid_words:
        return np.zeros(VECTOR_SIZE)

    vectors = [
        word_vectors[word_to_id[word]]
        for word in valid_words
    ]

    # ① 文全体の意味
    semantic_component = np.mean(vectors, axis=0)

    # ② 位置を含む意味
    positional_vectors = []
    length = len(vectors)

    for i, vector in enumerate(vectors):

        position_weight = 1.0 + (
            0.5 * (1.0 - i / max(length - 1, 1))
        )

        positional_vectors.append(
            vector * position_weight
        )

    position_component = np.mean(
        positional_vectors, axis=0
    )

    # ③ 順方向の関係
    relation_component = role_relation_vector(valid_words)

    # ④ v2.4：役割スロット
    # 先頭・中央・末尾を別々の「役割」として扱う。
    role_components = np.zeros(VECTOR_SIZE)

    if len(vectors) == 1:
        role_components += vectors[0]
    else:
        for i, vector in enumerate(vectors):
            if i == 0:
                weight = 1.00
            elif i == len(vectors) - 1:
                weight = 1.15
            else:
                weight = 0.70

            role_components += vector * weight

        role_components /= len(vectors)

    # ⑤ 意味＋位置＋関係＋役割を合成
    combined = (
        0.35 * semantic_component
        + 0.20 * position_component
        + 0.20 * relation_component
        + 0.25 * role_components
    )

    return normalize_vector(combined)


def sentence_similarity(text_a, text_b):

    vector_a = sentence_to_vector(text_a)
    vector_b = sentence_to_vector(text_b)

    return cosine_similarity(
        vector_a,
        vector_b
    )


# =========================================================
# 学習後確認
# =========================================================

print("【単語ベクトル確認】")

for word in [
    "ゲーム",
    "楽しい",
    "好き",
    "メモ帳",
    "開く",
    "ブラウザ"
]:

    if word in word_to_id:

        vector = word_vectors[
            word_to_id[word]
        ]

        print(
            word,
            "→",
            np.round(vector[:6], 3),
            "..."
        )

print("")


# =========================================================
# 分類ニューラルネットワーク
# =========================================================

INPUT_SIZE = VECTOR_SIZE
HIDDEN_SIZE = 32
OUTPUT_SIZE = len(names)

W1 = rng.normal(
    0,
    0.1,
    (INPUT_SIZE, HIDDEN_SIZE)
)

b1 = np.zeros(HIDDEN_SIZE)

W2 = rng.normal(
    0,
    0.1,
    (HIDDEN_SIZE, OUTPUT_SIZE)
)

b2 = np.zeros(OUTPUT_SIZE)


def softmax(x):

    x = x - np.max(x)

    exp_x = np.exp(x)

    return exp_x / np.sum(exp_x)


def relu(x):
    return np.maximum(0, x)


def relu_derivative(x):
    return (x > 0).astype(float)


classification_data = data

training_data = []

for label, sentence in classification_data:

    x = sentence_to_vector(sentence)

    y = np.zeros(OUTPUT_SIZE)

    y[names.index(label)] = 1

    training_data.append(
        (x, y)
    )


learning_rate = 0.05
epochs = 3000

print("分類ニューラルネットワーク学習開始...")

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

        dz1 = (
            dh *
            relu_derivative(z1)
        )

        dW1 = np.outer(x, dz1)
        db1 = dz1

        W2 -= learning_rate * dW2
        b2 -= learning_rate * db2

        W1 -= learning_rate * dW1
        b1 -= learning_rate * db1

print("分類学習完了！")
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

    index = int(
        np.argmax(pred)
    )

    confidence = float(
        pred[index]
    )

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

        score = (
            len(a & b)
            /
            len(a | b)
        )

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
    # 単語
    # -------------------------

    if text.startswith("単語 "):

        target = text[3:].strip()

        words = tokenize(target)

        print(
            "めいな：単語をベクトルに変換します。"
        )

        for word in words:

            if word in word_to_id:

                vector = word_vectors[
                    word_to_id[word]
                ]

                print(
                    word,
                    "→",
                    np.round(vector, 3)
                )

            else:

                print(
                    word,
                    "→ 未登録"
                )

        continue

    # -------------------------
    # 類似度：単語
    # -------------------------

    if text.startswith("類似度 "):

        parts = text[4:].strip().split()

        if len(parts) < 2:

            print(
                "めいな：「類似度 ゲーム 楽しい」のように入力してください。"
            )

            continue

        # 2つの文章として比較
        left = parts[0]
        right = " ".join(parts[1:])

        score = sentence_similarity(
            left,
            right
        )

        print(
            "めいな：文章・意味の類似度"
        )

        print(
            left,
            "↔",
            right
        )

        print(
            "類似度：",
            round(score, 4)
        )

        continue

    # -------------------------
    # 役割・関係確認
    # -------------------------

    if text.startswith("関係 "):

        query = text[3:].strip()
        words = [
            word for word in tokenize(query)
            if word in word_to_id
        ]

        if len(words) < 2:
            print("めいな：2語以上を指定してください。例：関係 ゲーム 楽しい")
            continue

        print("めいな：「" + query + "」の単語関係")

        for i in range(len(words) - 1):

            a = words[i]
            b = words[i + 1]

            va = word_vectors[word_to_id[a]]
            vb = word_vectors[word_to_id[b]]

            relation = normalize_vector(vb - va)
            strength = float(np.linalg.norm(vb - va))

            print(
                a, "→", b,
                "関係ベクトル強度：",
                round(strength, 4)
            )

        continue

    # -------------------------
    # 語順・役割比較
    # -------------------------

    if text.startswith("語順比較 "):

        parts = text[5:].strip().split("|")

        if len(parts) != 2:
            print(
                "めいな：「語順比較 ゲーム楽しい|楽しいゲーム」のように入力してください。"
            )
            continue

        sentence_a = parts[0].strip()
        sentence_b = parts[1].strip()

        score = sentence_similarity(
            sentence_a,
            sentence_b
        )

        print("めいな：語順と役割を含めて文章を比較します。")
        print("A：", sentence_a)
        print("B：", sentence_b)
        print("語順・役割込み類似度：", round(score, 4))

        continue

    # -------------------------
    # 役割確認
    # -------------------------

    if text.startswith("役割比較 "):

        parts = text[5:].strip().split("|")

        if len(parts) != 2:
            print(
                "めいな：「役割比較 ゲーム起動|起動ゲーム」のように入力してください。"
            )
            continue

        sentence_a = parts[0].strip()
        sentence_b = parts[1].strip()

        words_a = [w for w in tokenize(sentence_a) if w in word_to_id]
        words_b = [w for w in tokenize(sentence_b) if w in word_to_id]

        print("めいな：単語の役割位置を比較します。")
        print("A：", words_a)
        print("B：", words_b)
        print("先頭＝主体/話題、中央＝対象/状態、末尾＝動作/結果")

        score = sentence_similarity(
            sentence_a,
            sentence_b
        )

        print("役割込み類似度：", round(score, 4))

        continue

    # -------------------------
    # 文の意味比較
    # -------------------------

    if text.startswith("意味比較 "):

        parts = text[5:].strip().split("|")

        if len(parts) != 2:

            print(
                "めいな：「意味比較 ゲーム楽しい|ゲーム好き」のように入力してください。"
            )

            continue

        sentence_a = parts[0].strip()
        sentence_b = parts[1].strip()

        score = sentence_similarity(
            sentence_a,
            sentence_b
        )

        print("めいな：文章の意味を比較します。")
        print("A：", sentence_a)
        print("B：", sentence_b)
        print("意味類似度：", round(score, 4))

        continue

    # -------------------------
    # 近い単語
    # -------------------------

    if text.startswith("近い "):

        target = text[3:].strip()

        if target not in word_to_id:

            print(
                "めいな：その単語はまだ知りません。"
            )

            continue

        target_vector = word_vectors[
            word_to_id[target]
        ]

        results = []

        for word in vocab:

            if word == target:
                continue

            score = cosine_similarity(
                target_vector,
                word_vectors[word_to_id[word]]
            )

            results.append(
                (word, score)
            )

        results.sort(
            key=lambda x: x[1],
            reverse=True
        )

        print(
            "めいな：「"
            + target
            + "」に近い単語"
        )

        for word, score in results[:5]:

            print(
                word,
                "→",
                round(score, 4)
            )

        continue

    # -------------------------
    # 語彙
    # -------------------------

    if text == "語彙":

        print(
            "めいな：現在の語彙です。"
        )

        print(
            ", ".join(vocab)
        )

        continue

    # -------------------------
    # 履歴
    # -------------------------

    if text == "履歴":

        print(
            "めいな：会話履歴です。"
        )

        if not conversation_history:

            print(
                "履歴はありません。"
            )

        else:

            for item in conversation_history:

                print(
                    "あなた：",
                    item["user"]
                )

                print(
                    "めいな：",
                    item["meina"]
                )

        continue

    # -------------------------
    # 記憶
    # -------------------------

    if text.startswith("覚えて:"):

        content = text.replace(
            "覚えて:",
            "",
            1
        ).strip()

        if "=>" in content:

            key, value = content.split(
                "=>",
                1
            )

            key = key.strip()
            value = value.strip()

            brain_memory[key] = value

            save_memory()

            reply = "覚えました！"

        else:

            reply = (
                "「覚えて: 質問 => 答え」"
                "の形で教えてください。"
            )

        print(
            "めいな：" + reply
        )

        add_history(
            text,
            reply
        )

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
                "なんで？",
                "なんで",
                "どうして？",
                "どうして",
                "理由は？",
                "理由は"
            }:

                reply = (
                    "「"
                    + original
                    + "」についての理由ですね。"
                )

            elif text in {
                "詳しく",
                "詳しく教えて"
            }:

                reply = (
                    "「"
                    + original
                    + "」についてですね。"
                    "さっき私は「"
                    + previous_reply
                    + "」と答えました。"
                )

            elif text in {
                "もう一回",
                "もう一度"
            }:

                reply = previous_reply

            else:

                reply = (
                    "「"
                    + original
                    + "」についてですね。"
                )

        else:

            reply = "まだ話題がありません。"

        print(
            "めいな：" + reply
        )

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

        print(
            "めいな：" + knowledge_reply
        )

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

        print(
            "めいな：覚えています。"
        )

        print(
            "めいな：" + remembered
        )

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

        reply = (
            "質問ですね。"
            "もう少し詳しく教えてください。"
        )

    elif intent == "感謝":

        reply = "どういたしまして！"

    elif intent == "命令":

        reply = "命令を受け取りました。"

    elif intent == "雑談":

        reply = "そうですね！"

    else:

        reply = "まだよく分かりません。"

    print(
        "めいな：" + reply
    )

    add_history(
        text,
        reply
    )
