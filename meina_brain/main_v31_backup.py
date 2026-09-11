import json
import os
import numpy as np

print("めいなブレイン v3.1 起動")
print("文章意味・語順・単語役割＋役割推論＋役割自己学習システム：ON")
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

# =========================================================
# v3.0 自己学習データ
# =========================================================

LEARNED_CORPUS_FILE = "learned_corpus.json"

if os.path.exists(LEARNED_CORPUS_FILE):
    try:
        with open(LEARNED_CORPUS_FILE, "r", encoding="utf-8") as f:
            learned_corpus = json.load(f)
        if not isinstance(learned_corpus, list):
            learned_corpus = []
    except Exception:
        learned_corpus = []
else:
    learned_corpus = []

# 保存済みの学習文を、起動時の学習コーパスへ追加する。
for learned_sentence in learned_corpus:
    if isinstance(learned_sentence, str) and learned_sentence.strip():
        if learned_sentence not in corpus_texts:
            corpus_texts.append(learned_sentence)

def save_learned_corpus():
    with open(LEARNED_CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(learned_corpus, f, ensure_ascii=False, indent=2)


# =========================================================
# v3.1 役割自己学習データ
# =========================================================

LEARNED_ROLE_FILE = "learned_role_data.json"

if os.path.exists(LEARNED_ROLE_FILE):
    try:
        with open(LEARNED_ROLE_FILE, "r", encoding="utf-8") as f:
            learned_role_data = json.load(f)
        if not isinstance(learned_role_data, list):
            learned_role_data = []
    except Exception:
        learned_role_data = []
else:
    learned_role_data = []


def save_learned_role_data():
    with open(LEARNED_ROLE_FILE, "w", encoding="utf-8") as f:
        json.dump(learned_role_data, f, ensure_ascii=False, indent=2)


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
print("保存済み自己学習文：", len(learned_corpus))
print("保存済み役割学習：", len(learned_role_data))
print("文脈ペア数：", len(positive_pairs))
print("")

print("v3.1 単語・文脈・意味・語順・単語役割・役割推論・役割自己学習開始...")


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
    weights = []

    for i in range(len(words) - 1):

        a = word_vectors[word_to_id[words[i]]]
        b = word_vectors[word_to_id[words[i + 1]]]

        # v2.5：前→後の「方向」を強く保持する。
        # 順番を逆にすると、この成分は反対方向になる。
        relation = b - a

        # 文の前半の関係を少し強くする。
        weight = 1.0 + (0.25 * (1.0 - i / max(len(words) - 2, 1)))

        relations.append(relation * weight)
        weights.append(weight)

    relation_vector = np.sum(relations, axis=0) / max(np.sum(weights), 1e-8)

    return normalize_vector(relation_vector)


def order_direction_vector(words):

    # v2.5：単純な平均とは別に、先頭から末尾へ進む方向を作る。
    # 「A B」と「B A」では基本的に符号が反転するため、
    # 語順そのものを比較に反映しやすい。
    if len(words) < 2:
        return np.zeros(VECTOR_SIZE)

    direction = np.zeros(VECTOR_SIZE)

    for i in range(len(words) - 1):

        a = word_vectors[word_to_id[words[i]]]
        b = word_vectors[word_to_id[words[i + 1]]]

        pair_direction = b - a

        # 中央付近の関係も残しつつ、全体の方向を保持する。
        pair_weight = 1.0 + (0.5 / max(len(words) - 1, 1))
        direction += pair_direction * pair_weight

    return normalize_vector(direction)


def build_word_role_affinity():
    """各単語がコーパス中でどの役割に現れやすいかを学習する。

    役割は位置だけで決めず、各単語の出現位置から3スロットの確率を作る。
    0=主体/話題、1=対象/状態、2=動作/結果。
    """
    counts = {
        word: np.ones(3, dtype=float) * 0.05
        for word in word_to_id
    }

    for text in corpus_texts:
        words = [w for w in tokenize(text) if w in word_to_id]
        if not words:
            continue

        length = len(words)
        for i, word in enumerate(words):
            if length == 1:
                slot = 0
            elif i == 0:
                slot = 0
            elif i == length - 1:
                slot = 2
            else:
                slot = 1
            counts[word][slot] += 1.0

    # v3.1:
    # ユーザーが「学習」として追加した文章は、通常のコーパスより
    # 少し強く役割情報へ反映する。これにより、学習した例が
    # 次回起動後だけでなく、現在のセッションでも役割推定に効く。
    for example in learned_role_data:
        if not isinstance(example, dict):
            continue

        words = example.get("words", [])
        roles = example.get("roles", [])

        if not isinstance(words, list) or not isinstance(roles, list):
            continue

        for word, slot in zip(words, roles):
            if word not in counts:
                continue
            if isinstance(slot, int) and 0 <= slot < 3:
                counts[word][slot] += 2.0

    affinity = {}
    for word, values in counts.items():
        affinity[word] = values / np.sum(values)

    return affinity


def word_role_affinity(word):
    affinity = build_word_role_affinity()
    return affinity.get(word, np.array([1/3, 1/3, 1/3], dtype=float))


def role_prototypes():
    """役割ごとの単語ベクトル代表値。表示・補助評価用。"""
    slots = [[], [], []]

    for text in corpus_texts:
        words = [w for w in tokenize(text) if w in word_to_id]
        if not words:
            continue

        for i, word in enumerate(words):
            if len(words) == 1:
                slot = 0
            elif i == 0:
                slot = 0
            elif i == len(words) - 1:
                slot = 2
            else:
                slot = 1
            slots[slot].append(word_vectors[word_to_id[word]])

    prototypes = []
    for vectors in slots:
        if vectors:
            prototypes.append(normalize_vector(np.mean(vectors, axis=0)))
        else:
            prototypes.append(np.zeros(VECTOR_SIZE))

    return prototypes


def sentence_role_signature(text):
    """文章を「各スロットにどんな役割の単語が入っているか」で表す。"""
    words = [w for w in tokenize(text) if w in word_to_id]
    signature = np.zeros((3, 3), dtype=float)

    if not words:
        return signature.reshape(-1)

    length = len(words)
    for i, word in enumerate(words):
        if length == 1:
            slot = 0
        elif i == 0:
            slot = 0
        elif i == length - 1:
            slot = 2
        else:
            slot = 1

        # 単語自身が学習した役割分布を、その単語が入ったスロットへ入れる。
        signature[slot] += word_role_affinity(word)

    # 単語数で正規化し、長い文だけが強くならないようにする。
    signature /= max(length, 1)
    return signature.reshape(-1)


def role_score(text):
    """文章内の単語が、学習した役割とどれだけ一致するか。"""
    words = [w for w in tokenize(text) if w in word_to_id]
    if not words:
        return np.zeros(3)

    scores = np.zeros(3)
    length = len(words)

    for i, word in enumerate(words):
        if length == 1:
            slot = 0
        elif i == 0:
            slot = 0
        elif i == length - 1:
            slot = 2
        else:
            slot = 1

        affinity = word_role_affinity(word)
        scores[slot] = float(affinity[slot])

    return scores


def predict_word_role(word, slot_index=None):
    """学習済みの単語役割傾向から、その単語の役割を推定する。
    0=主体/話題、1=対象/状態、2=動作/結果。
    """
    affinity = word_role_affinity(word).astype(float)
    if slot_index is not None and 0 <= slot_index < 3:
        position = np.zeros(3, dtype=float)
        position[slot_index] = 1.0
        affinity = 0.75 * affinity + 0.25 * position
    total = affinity.sum()
    if total <= 0:
        affinity = np.ones(3) / 3.0
    else:
        affinity = affinity / total
    return affinity


def infer_roles(text):
    """未知の文章について、各単語の役割を推定する。"""
    words = [w for w in tokenize(text) if w in word_to_id]
    results = []
    role_names = ["主体/話題", "対象/状態", "動作/結果"]
    for i, word in enumerate(words):
        if len(words) == 1:
            slot = 0
        elif i == 0:
            slot = 0
        elif i == len(words) - 1:
            slot = 2
        else:
            slot = 1
        probs = predict_word_role(word, slot)
        role_id = int(np.argmax(probs))
        results.append((word, role_names[role_id], float(probs[role_id]), probs))
    return results


def role_comparison_score(text_a, text_b):
    """単語の役割分布と役割スロットを合わせて比較する。"""
    words_a = [w for w in tokenize(text_a) if w in word_to_id]
    words_b = [w for w in tokenize(text_b) if w in word_to_id]

    if not words_a or not words_b:
        return 0.0

    sig_a = sentence_role_signature(text_a)
    sig_b = sentence_role_signature(text_b)

    # 同じ役割スロットに同じタイプの単語が入っているか。
    structural = (cosine_similarity(sig_a, sig_b) + 1.0) / 2.0

    # 実際の配置そのものも比較する。逆順なら低くなる。
    def slots(words):
        result = [None, None, None]
        length = len(words)
        for i, word in enumerate(words):
            if length == 1:
                slot = 0
            elif i == 0:
                slot = 0
            elif i == length - 1:
                slot = 2
            else:
                slot = 1
            result[slot] = word
        return result

    a = slots(words_a)
    b = slots(words_b)
    placement = []
    for slot in range(3):
        if a[slot] is not None and b[slot] is not None:
            placement.append(
                (cosine_similarity(
                    word_vectors[word_to_id[a[slot]]],
                    word_vectors[word_to_id[b[slot]]]
                ) + 1.0) / 2.0
            )
        elif a[slot] is None and b[slot] is None:
            placement.append(1.0)
        else:
            placement.append(0.0)

    placement_score = float(np.mean(placement))

    # 役割分布を主役にし、配置一致を補助にする。
    return max(0.0, min(1.0, 0.65 * structural + 0.35 * placement_score))


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

    # ④ v2.5：さらに強い語順方向成分
    order_component = order_direction_vector(valid_words)

    # ⑤ v2.4：役割スロット
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

    # ⑥ v2.5：意味だけでなく「向き」を大きく評価する。
    # 同じ単語でも順番が逆なら方向成分が変わる。
    combined = (
        0.20 * semantic_component
        + 0.15 * position_component
        + 0.20 * relation_component
        + 0.20 * order_component
        + 0.25 * role_components
    )

    return normalize_vector(combined)


def semantic_sentence_vector(text):

    words = [w for w in tokenize(text) if w in word_to_id]

    if not words:
        return np.zeros(VECTOR_SIZE)

    vectors = [word_vectors[word_to_id[w]] for w in words]
    return normalize_vector(np.mean(vectors, axis=0))


def order_sentence_vector(text):

    words = [w for w in tokenize(text) if w in word_to_id]

    if len(words) < 2:
        return np.zeros(VECTOR_SIZE)

    # 「前の単語から次の単語へ」という方向だけを別チャンネルで保持する。
    # A→B と B→A は反対方向になるため、語順を平均意味ベクトルから分離できる。
    relations = []

    for i in range(len(words) - 1):
        a = word_vectors[word_to_id[words[i]]]
        b = word_vectors[word_to_id[words[i + 1]]]
        relations.append(b - a)

    return normalize_vector(np.mean(relations, axis=0))


def role_sentence_vector(text):
    # 3役割×3役割分布をそのまま役割ベクトルとして使う。
    return normalize_vector(sentence_role_signature(text))


def semantic_similarity(text_a, text_b):
    return cosine_similarity(
        semantic_sentence_vector(text_a),
        semantic_sentence_vector(text_b)
    )


def order_similarity(text_a, text_b):
    vector_a = order_sentence_vector(text_a)
    vector_b = order_sentence_vector(text_b)

    if np.linalg.norm(vector_a) == 0 or np.linalg.norm(vector_b) == 0:
        return 0.5

    raw = cosine_similarity(vector_a, vector_b)
    return (raw + 1.0) / 2.0


def role_similarity(text_a, text_b):
    return role_comparison_score(text_a, text_b)


def sentence_similarity(text_a, text_b):
    # 通常の文章類似度は「意味」だけを見る。
    return semantic_similarity(text_a, text_b)


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

    # =========================================================
    # v3.0 自己学習
    # =========================================================

    if text.startswith("学習 "):

        target = text[3:].strip()

        if not target:
            print("めいな：学習する文章を入力してください。例：学習 ゲーム 起動")
            continue

        # 既存データとの重複を避ける。
        if target in learned_corpus:
            print("めいな：その文章はすでに学習データにあります。")
            continue

        learned_corpus.append(target)
        save_learned_corpus()

        words = [w for w in tokenize(target) if w]

        # 文章内の位置から初期役割を作る。
        # 0=主体/話題、1=対象/状態、2=動作/結果
        roles = []
        length = len(words)

        for i, word in enumerate(words):
            if length <= 1:
                slot = 0
            elif i == 0:
                slot = 0
            elif i == length - 1:
                slot = 2
            else:
                slot = 1
            roles.append(slot)

        learned_role_data.append({
            "sentence": target,
            "words": words,
            "roles": roles
        })
        save_learned_role_data()

        print("めいな：文章を学習データに追加しました。")
        print("文章：", target)
        print("認識した単語：", words)
        print("初期役割：", [
            ["主体/話題", "対象/状態", "動作/結果"][r]
            for r in roles
        ])
        print("学習データ数：", len(learned_corpus))
        print("役割学習データ数：", len(learned_role_data))
        print("めいな：この文章の役割情報も保存しました。")
        continue

    if text == "学習一覧":

        print("めいな：現在の自己学習データ")

        if not learned_corpus:
            print("（まだありません）")
        else:
            for i, sentence in enumerate(learned_corpus, 1):
                print(str(i) + ".", sentence)

                # 同じ番号の役割学習データがあれば表示する。
                if i <= len(learned_role_data):
                    example = learned_role_data[i - 1]
                    if isinstance(example, dict):
                        words = example.get("words", [])
                        roles = example.get("roles", [])
                        labels = ["主体/話題", "対象/状態", "動作/結果"]
                        if words and len(words) == len(roles):
                            print("   役割：", [
                                labels[r] if isinstance(r, int) and 0 <= r < 3 else "不明"
                                for r in roles
                            ])

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

        meaning = semantic_similarity(sentence_a, sentence_b)
        ordering = order_similarity(sentence_a, sentence_b)
        # 意味50%＋語順50%。語順を独立評価するので、逆順を同一視しにくい。
        score = 0.50 * ((meaning + 1.0) / 2.0) + 0.50 * ordering

        print("めいな：意味と語順を分けて文章を比較します。")
        print("A：", sentence_a)
        print("B：", sentence_b)
        print("意味成分：", round(meaning, 4))
        print("語順成分：", round(ordering, 4))
        print("語順込み類似度：", round(score, 4))

        continue

    # -------------------------
    # 役割確認
    # -------------------------

    if text.startswith("役割知識 "):

        target = text[5:].strip()

        words = [w for w in tokenize(target) if w in word_to_id]

        if not words:
            print("めいな：登録されている単語が見つかりません。")
            continue

        print("めいな：学習した役割傾向を確認します。")
        print("単語：", target)

        labels = ["主体/話題", "対象/状態", "動作/結果"]

        for word in words:
            probs = word_role_affinity(word)
            best = int(np.argmax(probs))

            print(
                word,
                "→",
                labels[best],
                "信頼度：",
                round(float(probs[best]), 4),
                "分布：",
                np.round(probs, 4)
            )

        continue

    if text.startswith("役割推定 "):

        target = text[5:].strip()
        results = infer_roles(target)

        if not results:
            print("めいな：登録されている単語が見つかりません。")
            continue

        print("めいな：文章から単語の役割を推定します。")
        print("文章：", target)

        for word, role, confidence, probs in results:
            print(
                word, "→", role,
                "信頼度：", round(confidence, 4),
                "分布：", np.round(probs, 3)
            )

        continue

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

        score = role_comparison_score(
            sentence_a,
            sentence_b
        )

        print("Aの役割適合度：", [round(x, 4) for x in role_score(sentence_a)])
        print("Bの役割適合度：", [round(x, 4) for x in role_score(sentence_b)])
        print("役割込み類似度：", round(score, 4))
        print("Aの役割分布：", np.round(sentence_role_signature(sentence_a).reshape(3, 3), 3))
        print("Bの役割分布：", np.round(sentence_role_signature(sentence_b).reshape(3, 3), 3))

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
    # 語順方向の確認
    # -------------------------

    if text.startswith("方向 "):

        target = text[3:].strip()
        words = tokenize(target)
        valid_words = [w for w in words if w in word_to_id]

        if len(valid_words) < 2:
            print("めいな：2語以上の文章を指定してください。")
            continue

        direction = order_direction_vector(valid_words)

        print("めいな：「" + target + "」の語順方向")
        print("方向ベクトル強度：", round(float(np.linalg.norm(direction)), 4))
        print("先頭 → 末尾：", " → ".join(valid_words))

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
