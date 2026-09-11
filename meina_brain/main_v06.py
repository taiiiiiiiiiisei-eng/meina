import numpy as np

print("めいなブレイン v0.6 起動")

# 日本語を数字に変換
def text_to_numbers(text):
    numbers = []

    for char in text:
        numbers.append(ord(char) % 1000)

    return numbers


# 学習データ
texts = [
    "こんにちは",
    "おはよう",
    "好きなゲーム",
    "名前は"
]

labels = [0, 0, 1, 1]

# AIに入力できる形にする
X = []

for text in texts:
    nums = text_to_numbers(text)
    nums = nums[:10]

    while len(nums) < 10:
        nums.append(0)

    X.append(nums)

X = np.array(X, dtype=float)

# 数値を小さくする
X = X / 1000.0

Y = np.array(labels).reshape(-1, 1)

# ニューラルネットワーク
W = np.random.randn(10, 1) * 0.1
b = np.zeros((1,))


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# 学習
for i in range(10000):
    z = X @ W + b
    pred = sigmoid(z)

    error = pred - Y

    dW = X.T @ error / len(X)
    db = np.mean(error)

    W -= 0.5 * dW
    b -= 0.5 * db

print("学習完了！")


while True:
    text = input("あなた：")

    if text == "終了":
        print("めいな：終了します。")
        break

    nums = text_to_numbers(text)
    nums = nums[:10]

    while len(nums) < 10:
        nums.append(0)

    x = np.array([nums], dtype=float) / 1000.0

    result = sigmoid(x @ W + b)[0][0]

    print("AIの判断値：", round(float(result), 3))

    if result > 0.5:
        print("めいな：質問・会話ですね！")
    else:
        print("めいな：あいさつですね！")