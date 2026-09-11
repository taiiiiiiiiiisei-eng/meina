import json
import os
import numpy as np

print("めいなブレイン v3.6 起動")
print("文章意味・語順・単語役割＋役割推論＋役割一般化＋文章意図推論＋日本語フレーズ＋文章構造解析＋対象動作抽出システム：ON")
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

names = [
    "あいさつ",
    "質問",
    "感謝",
    "命令",
    "雑談"
]


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

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            brain_memory = json.load(f)

    except Exception:

        brain_memory = {}

else:

    brain_memory = {}


def save_memory():

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            brain_memory,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# 会話履歴
# =========================================================

conversation_history = []

MAX_HISTORY = 10


def add_history(
    user_text,
    meina_text,
    is_context=False
):

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
    "それ",
    "それは？",
    "それって？",
    "さっきの",
    "さっきの話",
    "さっきのやつ",
    "前の話",
    "前のやつ",
    "これ",
    "これは？",
    "どういう意味？",
    "どういう意味",
    "なんで？",
    "なんで",
    "どうして？",
    "どうして",
    "理由は？",
    "理由は",
    "もう一回",
    "もう一度",
    "詳しく",
    "詳しく教えて"
}


def get_topic():

    for item in reversed(conversation_history):

        if (
            not item["is_context"]
            and item["user"] not in context_words
        ):

            return item

    return None


# =========================================================
# v3.0 自己学習データ
# =========================================================

LEARNED_CORPUS_FILE = "learned_corpus.json"

if os.path.exists(LEARNED_CORPUS_FILE):

    try:

        with open(
            LEARNED_CORPUS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            learned_corpus = json.load(f)

        if not isinstance(
            learned_corpus,
            list
        ):

            learned_corpus = []

    except Exception:

        learned_corpus = []

else:

    learned_corpus = []


for learned_sentence in learned_corpus:

    if (
        isinstance(
            learned_sentence,
            str
        )
        and learned_sentence.strip()
    ):

        if learned_sentence not in corpus_texts:

            corpus_texts.append(
                learned_sentence
            )


def save_learned_corpus():

    with open(
        LEARNED_CORPUS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            learned_corpus,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# v3.1 役割自己学習データ
# =========================================================

LEARNED_ROLE_FILE = "learned_role_data.json"

if os.path.exists(LEARNED_ROLE_FILE):

    try:

        with open(
            LEARNED_ROLE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            learned_role_data = json.load(f)

        if not isinstance(
            learned_role_data,
            list
        ):

            learned_role_data = []

    except Exception:

        learned_role_data = []

else:

    learned_role_data = []


def save_learned_role_data():

    with open(
        LEARNED_ROLE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            learned_role_data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# 基本語
# =========================================================

base_words = [

    # 会話
    "こんにちは",
    "おはよう",
    "こんばんは",
    "やあ",
    "どうも",

    # 質問
    "元気",
    "名前",
    "好き",
    "ゲーム",
    "教えて",
    "何",
    "何が好き",

    # 感謝
    "ありがとう",
    "ありがと",
    "助かった",
    "サンキュー",

    # PC操作
    "メモ帳",
    "電卓",
    "計算機",
    "エクスプローラー",
    "Explorer",
    "ファイル",

    # ブラウザ
    "ブラウザ",
    "Google",
    "グーグル",
    "Chrome",
    "クローム",
    "Edge",
    "エッジ",

    # Web
    "YouTube",
    "ユーチューブ",

    # アプリ
    "Discord",
    "ディスコード",
    "Steam",
    "スチーム",
    "OBS",
    "オービーエス",

    # ゲーム
    "VALORANT",
    "バロラント",

    # 動作
    "開いて",
    "開く",
    "起動",
    "起動して",
    "検索",
    "検索して",
    "実行",
    "閉じる",
    "使う",
    "書く",
    "調べる",
    "遊ぶ",
    "プレイ",

    # その他
    "暇",
    "最近",
    "楽しい",
    "面白い",
    "遊ぶ",
    "使う",
    "書く",
    "インターネット",
    "めいな",
    "AI",
    "アシスタント",
    "学習",
    "賢い",
    "今日",
    "どう",
    "です",
    "ね",
    "よ",

    # 助詞
    "を",
    "は",
    "が",
    "に",
    "の",
    "って"
]


# =========================================================
# コーパスから基本語を追加
# =========================================================

for sentence in corpus_texts:

    for word in sentence.split():

        if word not in base_words:

            base_words.append(word)


# =========================================================
# v3.4 日本語フレーズ認識
# =========================================================

PHRASE_WORDS = [

    # 疑問
    "なんで",
    "どうして",
    "なぜ",
    "どんな",
    "いつ",
    "どこ",
    "だれ",
    "誰",
    "どうやって",
    "どういう",

    # 開く
    "開いてください",
    "開いてくれ",
    "開いて",

    # 起動
    "起動してください",
    "起動して",

    # 検索
    "検索してください",
    "検索して",

    # 教える
    "教えてください",
    "教えて",

    # 調べる
    "調べてください",
    "調べて"
]


# =========================================================
# 正規化
# =========================================================

NORMALIZE_WORDS = {

    "開いてください": "開く",
    "開いてくれ": "開く",
    "開いて": "開く",

    "起動してください": "起動",
    "起動して": "起動",

    "検索してください": "検索",
    "検索して": "検索",

    "調べてください": "調べる",
    "調べて": "調べる",

    "教えてください": "教えて"
}


# =========================================================
# 句読点
# =========================================================

PUNCTUATION = "？?！!。、，,．."


# =========================================================
# 助詞
# =========================================================

PARTICLES = {
    "は",
    "が",
    "を",
    "に",
    "へ",
    "で",
    "と",
    "の",
    "も",
    "から",
    "まで",
    "より",
    "って"
}


# =========================================================
# 質問フレーズ
# =========================================================

QUESTION_PHRASES = {
    "なんで",
    "どうして",
    "なぜ",
    "どんな",
    "いつ",
    "どこ",
    "だれ",
    "誰",
    "どうやって",
    "どういう"
}


# =========================================================
# 動作語
# =========================================================

ACTION_WORDS = {
    "開く",
    "起動",
    "検索",
    "実行",
    "閉じる",
    "使う",
    "書く",
    "教えて",
    "調べる",
    "遊ぶ",
    "プレイ"
}


# =========================================================
# 状態語
# =========================================================

STATE_WORDS = {
    "楽しい",
    "面白い",
    "好き",
    "暇",
    "元気",
    "賢い"
}


# =========================================================
# ★ v3.6.1 アプリ・サービス名
#
# 未知語処理よりも先に認識させる。
# =========================================================

APP_WORDS = [

    # 日本語
    "メモ帳",
    "電卓",
    "計算機",
    "エクスプローラー",
    "ブラウザ",

    # Google系
    "Google",
    "グーグル",

    # ブラウザ
    "Chrome",
    "クローム",
    "Edge",
    "エッジ",

    # Web
    "YouTube",
    "ユーチューブ",

    # アプリ
    "Discord",
    "ディスコード",
    "Steam",
    "スチーム",
    "OBS",
    "オービーエス",

    # ゲーム
    "VALORANT",
    "バロラント"
]


# =========================================================
# ★ v3.6.1 トークナイザー
#
# 重要：
# 以前は未知語を1文字ずつ処理していた。
#
# 電卓
# ↓
# 電 / 卓
#
# Google
# ↓
# G / o / o / g / l / e
#
# これを修正。
# =========================================================

def tokenize(text):

    text = text.strip()

    if not text:
        return []


    # -----------------------------------------------------
    # 半角スペースで明示的に区切られている場合
    # -----------------------------------------------------

    chunks = text.split()

    if len(chunks) > 1:

        result = []

        for chunk in chunks:

            result.extend(
                tokenize(chunk)
            )

        return result


    # -----------------------------------------------------
    # 候補語
    #
    # 長い単語を先にする。
    # -----------------------------------------------------

    candidates = sorted(
        set(
            APP_WORDS
            + PHRASE_WORDS
            + base_words
        ),
        key=len,
        reverse=True
    )


    # 助詞も長い順
    particles = sorted(
        PARTICLES,
        key=len,
        reverse=True
    )


    remaining = text

    words = []


    # -----------------------------------------------------
    # メイン解析
    # -----------------------------------------------------

    while remaining:

        # -------------------------------------------------
        # 句読点
        # -------------------------------------------------

        if remaining[0] in PUNCTUATION:

            remaining = remaining[1:]

            continue


        found = False


        # -------------------------------------------------
        # 既知語・アプリ名・フレーズ
        # -------------------------------------------------

        for word in candidates:

            if remaining.startswith(word):

                normalized = NORMALIZE_WORDS.get(
                    word,
                    word
                )

                words.append(
                    normalized
                )

                remaining = remaining[
                    len(word):
                ]

                found = True

                break


        if found:
            continue


        # -------------------------------------------------
        # 助詞
        # -------------------------------------------------

        for particle in particles:

            if remaining.startswith(
                particle
            ):

                words.append(
                    particle
                )

                remaining = remaining[
                    len(particle):
                ]

                found = True

                break


        if found:
            continue


        # -------------------------------------------------
        # ★ 未知語処理
        #
        # ここが今回の重要修正。
        #
        # 次の既知語・助詞が出てくるところまで
        # まとめて1単語として扱う。
        #
        # 例：
        #
        # 電卓を開いて
        #
        # 電卓 → 既知語
        # を   → 助詞
        # 開いて → 開く
        #
        # Googleを開いて
        #
        # Google → 既知語
        # を     → 助詞
        # 開いて → 開く
        #
        # さらに未知アプリでも、
        #
        # Spotifyを開いて
        #
        # Spotify → 未知語
        # を      → 助詞
        # 開いて  → 開く
        #
        # とできる。
        # -------------------------------------------------

        boundary_positions = []


        # -------------------------------------------------
        # 助詞の位置
        # -------------------------------------------------

        for particle in particles:

            position = remaining.find(
                particle
            )

            if position > 0:

                boundary_positions.append(
                    position
                )


        # -------------------------------------------------
        # 既知語の位置
        # -------------------------------------------------

        for word in candidates:

            position = remaining.find(
                word
            )

            if position > 0:

                boundary_positions.append(
                    position
                )


        # -------------------------------------------------
        # 一番近い境界
        # -------------------------------------------------

        if boundary_positions:

            next_position = min(
                boundary_positions
            )

            unknown_word = remaining[
                :next_position
            ]

            if unknown_word:

                words.append(
                    unknown_word
                )

                remaining = remaining[
                    next_position:
                ]

                continue


        # -------------------------------------------------
        # 境界がない場合
        #
        # 残り全部を1単語にする。
        # -------------------------------------------------

        words.append(
            remaining
        )

        remaining = ""


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


for word in APP_WORDS:

    all_words.add(word)


vocab = sorted(all_words)


word_to_id = {
    word: i
    for i, word in enumerate(vocab)
}


id_to_word = {
    i: word
    for word, i in word_to_id.items()
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
    (
        len(vocab),
        VECTOR_SIZE
    )
)


output_vectors = np.zeros(
    (
        len(vocab),
        VECTOR_SIZE
    ),
    dtype=np.float64
)


# =========================================================
# sigmoid
# =========================================================

def sigmoid(x):

    x = np.clip(
        x,
        -15,
        15
    )

    return 1.0 / (
        1.0 + np.exp(-x)
    )


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

    for center_pos, center_id in enumerate(
        sentence_ids
    ):

        start = max(
            0,
            center_pos - WINDOW_SIZE
        )

        end = min(
            len(sentence_ids),
            center_pos
            + WINDOW_SIZE
            + 1
        )

        for context_pos in range(
            start,
            end
        ):

            if context_pos == center_pos:

                continue


            context_id = sentence_ids[
                context_pos
            ]


            positive_pairs.append(
                (
                    center_id,
                    context_id
                )
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

print(
    "保存済み自己学習文：",
    len(learned_corpus)
)

print(
    "保存済み役割学習：",
    len(learned_role_data)
)

print(
    "文脈ペア数：",
    len(positive_pairs)
)

print("")


print(
    "v3.6 単語・文脈・意味・語順・"
    "単語役割・役割推論・役割一般化・"
    "文章意図推論・日本語フレーズ・"
    "文章構造解析・対象動作抽出開始..."
)


# =========================================================
# Skip-gram 学習
# =========================================================

for epoch in range(
    VECTOR_EPOCHS
):

    rng.shuffle(
        positive_pairs
    )


    for center_id, context_id in positive_pairs:

        # -------------------------------------------------
        # 正例
        # -------------------------------------------------

        center = input_vectors[
            center_id
        ].copy()


        context = output_vectors[
            context_id
        ].copy()


        score = np.dot(
            center,
            context
        )


        probability = sigmoid(
            score
        )


        gradient = (
            probability - 1.0
        )


        input_vectors[
            center_id
        ] -= (
            VECTOR_LR
            * gradient
            * context
        )


        output_vectors[
            context_id
        ] -= (
            VECTOR_LR
            * gradient
            * center
        )


        # -------------------------------------------------
        # 負例
        # -------------------------------------------------

        negative_ids = rng.choice(
            len(vocab),
            size=NEGATIVE_SAMPLES,
            p=negative_prob
        )


        for negative_id in negative_ids:

            if negative_id == context_id:

                continue


            center = input_vectors[
                center_id
            ].copy()


            negative = output_vectors[
                negative_id
            ].copy()


            score = np.dot(
                center,
                negative
            )


            probability = sigmoid(
                score
            )


            gradient = probability


            input_vectors[
                center_id
            ] -= (
                VECTOR_LR
                * gradient
                * negative
            )


            output_vectors[
                negative_id
            ] -= (
                VECTOR_LR
                * gradient
                * center
            )


word_vectors = input_vectors.copy()


print(
    "単語・文脈学習完了！"
)

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
        (
            norm_a
            * norm_b
        )
    )


# =========================================================
# ベクトル正規化
# =========================================================

def normalize_vector(vector):

    norm = np.linalg.norm(
        vector
    )


    if norm == 0:

        return vector


    return vector / norm


# =========================================================
# 役割関係ベクトル
# =========================================================

def role_relation_vector(words):

    if len(words) < 2:

        return np.zeros(
            VECTOR_SIZE
        )


    relations = []

    weights = []


    for i in range(
        len(words) - 1
    ):

        a = word_vectors[
            word_to_id[words[i]]
        ]


        b = word_vectors[
            word_to_id[words[i + 1]]
        ]


        relation = b - a


        weight = (
            1.0
            + (
                0.25
                * (
                    1.0
                    -
                    i
                    /
                    max(
                        len(words) - 2,
                        1
                    )
                )
            )
        )


        relations.append(
            relation * weight
        )


        weights.append(
            weight
        )


    relation_vector = (
        np.sum(
            relations,
            axis=0
        )
        /
        max(
            np.sum(weights),
            1e-8
        )
    )


    return normalize_vector(
        relation_vector
    )


# =========================================================
# 語順方向ベクトル
# =========================================================

def order_direction_vector(words):

    if len(words) < 2:

        return np.zeros(
            VECTOR_SIZE
        )


    direction = np.zeros(
        VECTOR_SIZE
    )


    for i in range(
        len(words) - 1
    ):

        a = word_vectors[
            word_to_id[words[i]]
        ]


        b = word_vectors[
            word_to_id[words[i + 1]]
        ]


        pair_direction = b - a


        pair_weight = (
            1.0
            +
            (
                0.5
                /
                max(
                    len(words) - 1,
                    1
                )
            )
        )


        direction += (
            pair_direction
            * pair_weight
        )


    return normalize_vector(
        direction
    )


# =========================================================
# 単語役割学習
# =========================================================

def build_word_role_affinity():

    counts = {
        word:
        np.ones(
            3,
            dtype=float
        ) * 0.05

        for word in word_to_id
    }


    for text in corpus_texts:

        words = [
            w
            for w in tokenize(text)
            if w in word_to_id
        ]


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


    # -----------------------------------------------------
    # 自己学習役割データ
    # -----------------------------------------------------

    for example in learned_role_data:

        if not isinstance(
            example,
            dict
        ):

            continue


        words = example.get(
            "words",
            []
        )


        roles = example.get(
            "roles",
            []
        )


        if (
            not isinstance(
                words,
                list
            )
            or
            not isinstance(
                roles,
                list
            )
        ):

            continue


        for word, slot in zip(
            words,
            roles
        ):

            if word not in counts:

                continue


            if (
                isinstance(
                    slot,
                    int
                )
                and
                0 <= slot < 3
            ):

                counts[word][slot] += 2.0


    affinity = {}


    for word, values in counts.items():

        affinity[word] = (
            values
            /
            np.sum(values)
        )


    return affinity


# =========================================================
# 単語役割取得
# =========================================================

def word_role_affinity(word):

    affinity = build_word_role_affinity()

    return affinity.get(
        word,
        np.array(
            [
                1 / 3,
                1 / 3,
                1 / 3
            ],
            dtype=float
        )
    )


# =========================================================
# 役割プロトタイプ
# =========================================================

def role_prototypes():

    slots = [
        [],
        [],
        []
    ]


    for text in corpus_texts:

        words = [
            w
            for w in tokenize(text)
            if w in word_to_id
        ]


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


            slots[slot].append(
                word_vectors[
                    word_to_id[word]
                ]
            )


    prototypes = []


    for vectors in slots:

        if vectors:

            prototypes.append(
                normalize_vector(
                    np.mean(
                        vectors,
                        axis=0
                    )
                )
            )

        else:

            prototypes.append(
                np.zeros(
                    VECTOR_SIZE
                )
            )


    return prototypes


# =========================================================
# 文章役割シグネチャ
# =========================================================

def sentence_role_signature(text):

    words = [
        w
        for w in tokenize(text)
        if w in word_to_id
    ]


    signature = np.zeros(
        (
            3,
            3
        ),
        dtype=float
    )


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


        signature[slot] += (
            word_role_affinity(word)
        )


    signature /= max(
        length,
        1
    )


    return signature.reshape(-1)


# =========================================================
# 役割スコア
# =========================================================

def role_score(text):

    words = [
        w
        for w in tokenize(text)
        if w in word_to_id
    ]


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


        affinity = word_role_affinity(
            word
        )


        scores[slot] = float(
            affinity[slot]
        )


    return scores


# =========================================================
# 未知語の役割一般化
# =========================================================

def fallback_role_affinity(word):

    if word in word_to_id:

        return word_role_affinity(
            word
        ).copy()


    candidates = []


    for known in sorted(
        word_to_id.keys(),
        key=len,
        reverse=True
    ):

        if (
            len(known) >= 2
            and known in word
        ):

            candidates.append(
                known
            )


    if candidates:

        values = [
            word_role_affinity(w)
            for w in candidates[:5]
        ]


        result = np.mean(
            values,
            axis=0
        )


        total = result.sum()


        if total > 0:

            return (
                result
                /
                total
            )


    return np.ones(
        3,
        dtype=float
    ) / 3.0


# =========================================================
# 単語役割予測
# =========================================================

def predict_word_role(
    word,
    slot_index=None
):

    affinity = fallback_role_affinity(
        word
    ).astype(float)


    if (
        slot_index is not None
        and
        0 <= slot_index < 3
    ):

        position = np.zeros(
            3,
            dtype=float
        )


        position[
            slot_index
        ] = 1.0


        affinity = (
            0.75
            * affinity
            +
            0.25
            * position
        )


    total = affinity.sum()


    if total <= 0:

        affinity = np.ones(3) / 3.0

    else:

        affinity = (
            affinity
            /
            total
        )


    return affinity


# =========================================================
# 文章構造解析
# =========================================================

def parse_sentence_structure(text):

    raw_words = [
        w
        for w in tokenize(text)
        if w
        and
        w not in PUNCTUATION
    ]


    content = []

    relations = []

    pending_particle = None


    for word in raw_words:

        # 助詞
        if word in PARTICLES:

            pending_particle = word

            continue


        # 疑問
        if (
            word in QUESTION_PHRASES
            and
            not content
        ):

            relations.append(
                (
                    "疑問",
                    word
                )
            )

            continue


        content.append(
            word
        )


        if pending_particle:

            relations.append(
                (
                    "助詞",
                    pending_particle
                )
            )

            pending_particle = None


    roles = []


    for i, word in enumerate(
        content
    ):

        role = "対象/状態"


        if word in ACTION_WORDS:

            role = "動作/結果"

        elif word in STATE_WORDS:

            role = "対象/状態"

        elif i == 0:

            role = "主体/話題"


        # -------------------------------------------------
        # 直前助詞
        # -------------------------------------------------

        previous_particle = None


        for j in range(
            len(raw_words) - 1,
            -1,
            -1
        ):

            if raw_words[j] == word:

                if (
                    j > 0
                    and
                    raw_words[j - 1]
                    in PARTICLES
                ):

                    previous_particle = (
                        raw_words[j - 1]
                    )

                break


        if (
            previous_particle
            in {
                "を",
                "に",
                "へ",
                "で",
                "と"
            }
            and
            word not in ACTION_WORDS
        ):

            role = "対象/状態"


        roles.append(
            (
                word,
                role
            )
        )


    return (
        raw_words,
        content,
        roles,
        relations
    )


# =========================================================
# 対象＋動作フレーム抽出
# =========================================================

def extract_action_frame(text):

    (
        raw_words,
        content_words,
        structural_roles,
        relations
    ) = parse_sentence_structure(text)


    action = None

    action_index = None


    # -----------------------------------------------------
    # 動作を探す
    # -----------------------------------------------------

    for i, word in enumerate(
        content_words
    ):

        if word in ACTION_WORDS:

            action = word

            action_index = i

            break


    target = None

    target_index = None


    # -----------------------------------------------------
    # 動作がある場合
    # -----------------------------------------------------

    if action_index is not None:

        try:

            action_raw_index = (
                raw_words.index(action)
            )

        except ValueError:

            action_raw_index = None


        # -------------------------------------------------
        # 助詞の直前を対象にする
        # -------------------------------------------------

        if action_raw_index is not None:

            for j in range(
                action_raw_index - 1,
                -1,
                -1
            ):

                if raw_words[j] in PARTICLES:

                    if (
                        raw_words[j]
                        in {
                            "を",
                            "に",
                            "へ",
                            "で",
                            "と"
                        }
                        and
                        j > 0
                    ):

                        candidate = (
                            raw_words[j - 1]
                        )


                        if (
                            candidate
                            not in PARTICLES
                            and
                            candidate
                            not in QUESTION_PHRASES
                        ):

                            target = candidate


                            if (
                                candidate
                                in content_words
                            ):

                                target_index = (
                                    content_words.index(
                                        candidate
                                    )
                                )


                            break


        # -------------------------------------------------
        # 助詞がない場合
        # 動作直前の単語を対象にする
        # -------------------------------------------------

        if (
            target is None
            and
            action_index > 0
        ):

            for i in range(
                action_index - 1,
                -1,
                -1
            ):

                candidate = (
                    content_words[i]
                )


                if (
                    candidate
                    not in QUESTION_PHRASES
                ):

                    target = candidate

                    target_index = i

                    break


    # =====================================================
    # 状態・述語
    # =====================================================

    predicate = None


    if action is None:

        for word in content_words:

            if word in STATE_WORDS:

                predicate = word

                break


    # =====================================================
    # 助詞関係
    # =====================================================

    particle_relations = [
        value
        for kind, value in relations
        if kind == "助詞"
    ]


    # =====================================================
    # 疑問判定
    # =====================================================

    question = (
        any(
            kind == "疑問"
            for kind, _ in relations
        )
        or
        any(
            x in text
            for x in [
                "？",
                "?",
                "なぜ",
                "なんで",
                "どうして",
                "何"
            ]
        )
    )


    # =====================================================
    # 信頼度
    # =====================================================

    if (
        action is not None
        and
        target is not None
    ):

        confidence = 0.95

    elif action is not None:

        confidence = 0.70

    elif (
        predicate is not None
        and
        target is not None
    ):

        confidence = 0.75

    else:

        confidence = 0.25


    return {
        "target": target,
        "action": action,
        "predicate": predicate,
        "particles": particle_relations,
        "question": question,
        "target_index": target_index,
        "action_index": action_index,
        "confidence": confidence,
        "words": content_words
    }


# =========================================================
# 役割推論
# =========================================================

def infer_roles(text):

    (
        raw_words,
        words,
        structural_roles,
        relations
    ) = parse_sentence_structure(text)


    results = []


    role_names = [
        "主体/話題",
        "対象/状態",
        "動作/結果"
    ]


    role_to_id = {
        name: i
        for i, name in enumerate(
            role_names
        )
    }


    for i, (
        word,
        structural_role
    ) in enumerate(
        structural_roles
    ):

        slot = (
            0
            if structural_role == "主体/話題"
            else
            2
            if structural_role == "動作/結果"
            else
            1
        )


        learned = predict_word_role(
            word,
            slot
        )


        structural = np.zeros(
            3,
            dtype=float
        )


        structural[
            role_to_id[
                structural_role
            ]
        ] = 1.0


        probs = (
            0.70
            * structural
            +
            0.30
            * learned
        )


        probs /= max(
            probs.sum(),
            1e-9
        )


        best = int(
            np.argmax(probs)
        )


        results.append(
            (
                word,
                role_names[best],
                float(probs[best]),
                probs
            )
        )


    return results


# =========================================================
# 役割比較
# =========================================================

def role_comparison_score(
    text_a,
    text_b
):

    words_a = [
        w
        for w in tokenize(text_a)
        if w in word_to_id
    ]


    words_b = [
        w
        for w in tokenize(text_b)
        if w in word_to_id
    ]


    if (
        not words_a
        or
        not words_b
    ):

        return 0.0


    sig_a = sentence_role_signature(
        text_a
    )


    sig_b = sentence_role_signature(
        text_b
    )


    structural = (
        cosine_similarity(
            sig_a,
            sig_b
        )
        +
        1.0
    ) / 2.0


    # -----------------------------------------------------
    # スロット
    # -----------------------------------------------------

    def slots(words):

        result = [
            None,
            None,
            None
        ]


        length = len(words)


        for i, word in enumerate(
            words
        ):

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

        if (
            a[slot] is not None
            and
            b[slot] is not None
        ):

            placement.append(
                (
                    cosine_similarity(
                        word_vectors[
                            word_to_id[
                                a[slot]
                            ]
                        ],
                        word_vectors[
                            word_to_id[
                                b[slot]
                            ]
                        ]
                    )
                    +
                    1.0
                ) / 2.0
            )


        elif (
            a[slot] is None
            and
            b[slot] is None
        ):

            placement.append(
                1.0
            )

        else:

            placement.append(
                0.0
            )


    placement_score = float(
        np.mean(
            placement
        )
    )


    return max(
        0.0,
        min(
            1.0,
            0.65
            * structural
            +
            0.35
            * placement_score
        )
    )


# =========================================================
# 文ベクトル
# =========================================================

def sentence_to_vector(text):

    words = tokenize(text)


    valid_words = [
        word
        for word in words
        if word in word_to_id
    ]


    if not valid_words:

        return np.zeros(
            VECTOR_SIZE
        )


    vectors = [
        word_vectors[
            word_to_id[word]
        ]
        for word in valid_words
    ]


    # -----------------------------------------------------
    # ① 文全体の意味
    # -----------------------------------------------------

    semantic_component = np.mean(
        vectors,
        axis=0
    )


    # -----------------------------------------------------
    # ② 位置を含む意味
    # -----------------------------------------------------

    positional_vectors = []

    length = len(vectors)


    for i, vector in enumerate(
        vectors
    ):

        position_weight = (
            1.0
            +
            (
                0.5
                *
                (
                    1.0
                    -
                    i
                    /
                    max(
                        length - 1,
                        1
                    )
                )
            )
        )


        positional_vectors.append(
            vector
            *
            position_weight
        )


    position_component = np.mean(
        positional_vectors,
        axis=0
    )


    # -----------------------------------------------------
    # ③ 関係
    # -----------------------------------------------------

    relation_component = (
        role_relation_vector(
            valid_words
        )
    )


    # -----------------------------------------------------
    # ④ 語順
    # -----------------------------------------------------

    order_component = (
        order_direction_vector(
            valid_words
        )
    )


    # -----------------------------------------------------
    # ⑤ 役割
    # -----------------------------------------------------

    role_components = np.zeros(
        VECTOR_SIZE
    )


    if len(vectors) == 1:

        role_components += vectors[0]

    else:

        for i, vector in enumerate(
            vectors
        ):

            if i == 0:

                weight = 1.00

            elif i == len(vectors) - 1:

                weight = 1.15

            else:

                weight = 0.70


            role_components += (
                vector
                * weight
            )


        role_components /= len(
            vectors
        )


    # -----------------------------------------------------
    # 統合
    # -----------------------------------------------------

    combined = (

        0.20
        * semantic_component

        +

        0.15
        * position_component

        +

        0.20
        * relation_component

        +

        0.20
        * order_component

        +

        0.25
        * role_components
    )


    return normalize_vector(
        combined
    )


# =========================================================
# 意味ベクトル
# =========================================================

def semantic_sentence_vector(text):

    words = [
        w
        for w in tokenize(text)
        if w in word_to_id
    ]


    if not words:

        return np.zeros(
            VECTOR_SIZE
        )


    vectors = [
        word_vectors[
            word_to_id[w]
        ]
        for w in words
    ]


    return normalize_vector(
        np.mean(
            vectors,
            axis=0
        )
    )


# =========================================================
# 語順ベクトル
# =========================================================

def order_sentence_vector(text):

    words = [
        w
        for w in tokenize(text)
        if w in word_to_id
    ]


    if len(words) < 2:

        return np.zeros(
            VECTOR_SIZE
        )


    relations = []


    for i in range(
        len(words) - 1
    ):

        a = word_vectors[
            word_to_id[
                words[i]
            ]
        ]


        b = word_vectors[
            word_to_id[
                words[i + 1]
            ]
        ]


        relations.append(
            b - a
        )


    return normalize_vector(
        np.mean(
            relations,
            axis=0
        )
    )


# =========================================================
# 役割ベクトル
# =========================================================

def role_sentence_vector(text):

    return normalize_vector(
        sentence_role_signature(
            text
        )
    )


# =========================================================
# 類似度
# =========================================================

def semantic_similarity(
    text_a,
    text_b
):

    return cosine_similarity(

        semantic_sentence_vector(
            text_a
        ),

        semantic_sentence_vector(
            text_b
        )
    )


def order_similarity(
    text_a,
    text_b
):

    vector_a = order_sentence_vector(
        text_a
    )


    vector_b = order_sentence_vector(
        text_b
    )


    if (
        np.linalg.norm(vector_a)
        == 0
        or
        np.linalg.norm(vector_b)
        == 0
    ):

        return 0.5


    raw = cosine_similarity(
        vector_a,
        vector_b
    )


    return (
        raw + 1.0
    ) / 2.0


def role_similarity(
    text_a,
    text_b
):

    return role_comparison_score(
        text_a,
        text_b
    )


def sentence_similarity(
    text_a,
    text_b
):

    return semantic_similarity(
        text_a,
        text_b
    )


# =========================================================
# 学習後確認
# =========================================================

print(
    "【単語ベクトル確認】"
)


for word in [

    "ゲーム",
    "楽しい",
    "好き",
    "メモ帳",
    "電卓",
    "エクスプローラー",
    "ブラウザ",
    "Google",
    "YouTube",
    "Discord",
    "Steam",
    "Chrome",
    "VALORANT",
    "開く"

]:

    if word in word_to_id:

        vector = word_vectors[
            word_to_id[word]
        ]


        print(
            word,
            "→",
            np.round(
                vector[:6],
                3
            ),
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
    (
        INPUT_SIZE,
        HIDDEN_SIZE
    )
)


b1 = np.zeros(
    HIDDEN_SIZE
)


W2 = rng.normal(
    0,
    0.1,
    (
        HIDDEN_SIZE,
        OUTPUT_SIZE
    )
)


b2 = np.zeros(
    OUTPUT_SIZE
)


# =========================================================
# Softmax
# =========================================================

def softmax(x):

    x = x - np.max(x)

    exp_x = np.exp(x)

    return (
        exp_x
        /
        np.sum(exp_x)
    )


# =========================================================
# ReLU
# =========================================================

def relu(x):

    return np.maximum(
        0,
        x
    )


def relu_derivative(x):

    return (
        x > 0
    ).astype(float)


# =========================================================
# 分類学習データ
# =========================================================

classification_data = data


training_data = []


for label, sentence in (
    classification_data
):

    x = sentence_to_vector(
        sentence
    )


    y = np.zeros(
        OUTPUT_SIZE
    )


    y[
        names.index(label)
    ] = 1


    training_data.append(
        (
            x,
            y
        )
    )


learning_rate = 0.05

epochs = 3000


print(
    "分類ニューラルネットワーク学習開始..."
)


# =========================================================
# 分類ニューラルネット学習
# =========================================================

for epoch in range(
    epochs
):

    for x, y in training_data:

        z1 = (
            np.dot(
                x,
                W1
            )
            +
            b1
        )


        h = relu(
            z1
        )


        z2 = (
            np.dot(
                h,
                W2
            )
            +
            b2
        )


        pred = softmax(
            z2
        )


        dz2 = pred - y


        dW2 = np.outer(
            h,
            dz2
        )


        db2 = dz2


        dh = np.dot(
            W2,
            dz2
        )


        dz1 = (
            dh
            *
            relu_derivative(
                z1
            )
        )


        dW1 = np.outer(
            x,
            dz1
        )


        db1 = dz1


        W2 -= (
            learning_rate
            *
            dW2
        )


        b2 -= (
            learning_rate
            *
            db2
        )


        W1 -= (
            learning_rate
            *
            dW1
        )


        b1 -= (
            learning_rate
            *
            db1
        )


print(
    "分類学習完了！"
)

print("")


# =========================================================
# AI分類
# =========================================================

def classify(text):

    x = sentence_to_vector(
        text
    )


    z1 = (
        np.dot(
            x,
            W1
        )
        +
        b1
    )


    h = relu(
        z1
    )


    z2 = (
        np.dot(
            h,
            W2
        )
        +
        b2
    )


    pred = softmax(
        z2
    )


    index = int(
        np.argmax(
            pred
        )
    )


    confidence = float(
        pred[index]
    )


    return (
        names[index],
        confidence
    )


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


        if (
            not a
            or
            not b
        ):

            continue


        score = (
            len(
                a & b
            )
            /
            len(
                a | b
            )
        )


        if score > best_score:

            best_score = score

            best_key = key


    if best_score >= 0.3:

        return brain_memory[
            best_key
        ]


    return None


# =========================================================
# v3.3 文章意図推論
# =========================================================

INTENT_NAMES = [

    "質問",
    "命令",
    "雑談",
    "あいさつ",
    "感謝",
    "依頼",
    "情報要求"

]


INTENT_PROTOTYPES = {

    "質問": [
        "何",
        "なぜ",
        "なんで",
        "どうして",
        "教えて",
        "知りたい"
    ],

    "命令": [
        "開く",
        "起動",
        "閉じる",
        "検索",
        "実行"
    ],

    "雑談": [
        "楽しい",
        "好き",
        "ゲーム",
        "面白い"
    ],

    "あいさつ": [
        "こんにちは",
        "こんばんは",
        "おはよう",
        "やあ"
    ],

    "感謝": [
        "ありがとう",
        "助かった",
        "感謝"
    ],

    "依頼": [
        "お願い",
        "して",
        "やって",
        "頼む"
    ],

    "情報要求": [
        "調べて",
        "検索",
        "教えて",
        "情報"
    ]
}


# =========================================================
# 意図キーワードスコア
# =========================================================

def _intent_keyword_score(
    text,
    keywords
):

    score = 0.0


    for word in keywords:

        if word in text:

            score += 1.0


    return score


# =========================================================
# 意図推論
# =========================================================

def infer_intent(text):

    clean = text.strip()


    words = [
        w
        for w in tokenize(clean)
        if w
        and
        w not in "？?！!。、，,"
    ]


    if not words:

        return (
            "不明",
            0.0,
            [],
            []
        )


    # -----------------------------------------------------
    # ニューラルネット分類
    # -----------------------------------------------------

    base_intent, base_conf = classify(
        clean
    )


    # -----------------------------------------------------
    # 役割推定
    # -----------------------------------------------------

    role_results = infer_roles(
        clean
    )


    role_labels = [
        r[1]
        for r in role_results
    ]


    # -----------------------------------------------------
    # 意図スコア
    # -----------------------------------------------------

    scores = {
        name: 0.0
        for name in INTENT_NAMES
    }


    for (
        name,
        keywords
    ) in INTENT_PROTOTYPES.items():

        scores[name] += (
            _intent_keyword_score(
                clean,
                keywords
            )
        )


    # -----------------------------------------------------
    # 動作語
    # -----------------------------------------------------

    if role_results:

        last_role = (
            role_results[-1][1]
        )


        if last_role == "動作/結果":

            scores["命令"] += 0.8

            scores["依頼"] += 0.5


    # -----------------------------------------------------
    # 疑問
    # -----------------------------------------------------

    if any(
        x in clean
        for x in [
            "？",
            "?",
            "なぜ",
            "なんで",
            "どうして",
            "何"
        ]
    ):

        scores["質問"] += 2.0


    # -----------------------------------------------------
    # あいさつ
    # -----------------------------------------------------

    if any(
        x in clean
        for x in [
            "こんにちは",
            "こんばんは",
            "おはよう",
            "やあ"
        ]
    ):

        scores["あいさつ"] += 3.0


    # -----------------------------------------------------
    # 感謝
    # -----------------------------------------------------

    if any(
        x in clean
        for x in [
            "ありがとう",
            "助かった",
            "感謝"
        ]
    ):

        scores["感謝"] += 3.0


    # -----------------------------------------------------
    # 意味ベクトル
    # -----------------------------------------------------

    semantic_scores = {}


    for (
        name,
        prototype_words
    ) in INTENT_PROTOTYPES.items():

        sims = []


        for proto in prototype_words:

            if proto in word_to_id:

                s = semantic_similarity(
                    clean,
                    proto
                )


                sims.append(
                    (
                        s + 1.0
                    )
                    /
                    2.0
                )


        semantic_scores[name] = (
            float(
                np.mean(sims)
            )
            if sims
            else
            0.0
        )


    # -----------------------------------------------------
    # 意味スコアを補助
    # -----------------------------------------------------

    for name in scores:

        scores[name] += (
            semantic_scores.get(
                name,
                0.0
            )
            *
            0.8
        )


    # -----------------------------------------------------
    # ニューラルネット結果を補助
    # -----------------------------------------------------

    if base_intent in scores:

        scores[base_intent] += (
            0.6
            *
            base_conf
        )


    # -----------------------------------------------------
    # 最終意図
    # -----------------------------------------------------

    best_intent = max(
        scores,
        key=scores.get
    )


    raw = scores[
        best_intent
    ]


    total = sum(
        max(
            v,
            0.0
        )
        for v in scores.values()
    )


    confidence = (
        raw
        /
        total
        if total > 0
        else
        0.0
    )


    return (
        best_intent,
        float(confidence),
        role_results,
        semantic_scores
    )


# =========================================================
# 意図説明
# =========================================================

def explain_intent(text):

    (
        intent,
        confidence,
        roles,
        semantic_scores
    ) = infer_intent(text)


    print(
        "めいな：文章全体の意図を推論します。"
    )


    print(
        "文章：",
        text
    )


    print(
        "推定意図：",
        intent
    )


    print(
        "意図信頼度：",
        round(
            confidence,
            4
        )
    )


    # -----------------------------------------------------
    # フレーム
    # -----------------------------------------------------

    frame = extract_action_frame(
        text
    )


    print(
        "対象・動作フレーム："
    )


    print(
        "  対象：",
        frame["target"]
        if frame["target"]
        else
        "なし"
    )


    print(
        "  動作：",
        frame["action"]
        if frame["action"]
        else
        "なし"
    )


    if frame["predicate"]:

        print(
            "  状態・述語：",
            frame["predicate"]
        )


    print(
        "  フレーム信頼度：",
        round(
            frame["confidence"],
            4
        )
    )


    # -----------------------------------------------------
    # 役割
    # -----------------------------------------------------

    if roles:

        print(
            "単語役割："
        )


        for (
            word,
            role,
            role_conf,
            probs
        ) in roles:

            print(
                "  ",
                word,
                "→",
                role,
                "信頼度：",
                round(
                    role_conf,
                    4
                )
            )


    # -----------------------------------------------------
    # 意味候補
    # -----------------------------------------------------

    ranked = sorted(
        semantic_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )


    if ranked:

        print(
            "意味候補："
        )


        for (
            name,
            score
        ) in ranked[:3]:

            print(
                "  ",
                name,
                "→",
                round(
                    score,
                    4
                )
            )


    return (
        intent,
        confidence
    )


# =========================================================
# v3.6.1 動作フレーム簡易テスト
# =========================================================

print(
    "【対象・動作抽出テスト】"
)


_test_sentences = [

    "メモ帳を開いて",
    "電卓を開いて",
    "エクスプローラーを開いて",
    "Googleを開いて",
    "YouTubeを開いて",
    "Discordを開いて",
    "Steamを開いて",
    "Chromeを開いて",
    "VALORANTを開いて"

]


for _test in _test_sentences:

    _frame = extract_action_frame(
        _test
    )


    print(
        _test,
        "→",
        _frame["target"],
        "/",
        _frame["action"],
        "/",
        _frame["words"]
    )


print("")


# =========================================================
# CLI部分は削除済み
#
# brain_core.py は「脳」として import される。
# 実際の会話ループは meina_agent.py 側で行う。
# =========================================================