import numpy as np

print("めいなブレイン v0.7 起動")

# 0=あいさつ  1=質問  2=感謝  3=命令  4=雑談
data = [
    ("こんにちは", 0),
    ("おはよう", 0),
    ("こんばんは", 0),
    ("元気？", 1),
    ("名前は？", 1),
    ("好きなゲームは？", 1),
    ("ありがとう", 2),
    ("助かった", 2),
    ("メモ帳を開いて", 3),
    ("ブラウザを開いて", 3),
    ("ゲームを起動して", 3),
    ("今日は暇だね", 4),
    ("最近どう？", 4),
    ("ゲーム楽しいね", 4),
]

def text_to_numbers(text):
    nums = [ord(c) % 1000 for c in text[:20]]
    while len(nums) < 20:
        nums.append(0)
    return nums

X = np.array([text_to_numbers(t) for t, _ in data]) / 1000.0
Y = np.array([y for _, y in data])

# 出力5個のニューラルネットワーク
W = np.random.randn(20, 5) * 0.1
b = np.zeros(5)

def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=1, keepdims=True)

# 学習
for i in range(20000):
    scores = X @ W + b
    probs = softmax(scores)

    error = probs.copy()
    error[np.arange(len(Y)), Y] -= 1

    dW = X.T @ error / len(X)
    db = np.mean(error, axis=0)

    W -= 0.5 * dW
    b -= 0.5 * db

print("学習完了！")

names = ["あいさつ", "質問", "感謝", "命令", "雑談"]

while True:
    text = input("あなた：")

    if text == "終了":
        print("めいな：終了します。")
        break

    x = np.array([text_to_numbers(text)]) / 1000.0

    scores = x @ W + b
    probs = softmax(scores)[0]

    index = np.argmax(probs)

    print("AIの判断：", names[index])
    print("確信度：", round(float(probs[index]), 3))