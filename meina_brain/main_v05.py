import numpy as np

print("めいなブレイン v0.5 起動")

# 入力データ
X = np.array([
    [1, 0],
    [0, 1],
    [1, 1],
    [0, 0]
], dtype=float)

# 正解データ
Y = np.array([
    [1],
    [1],
    [1],
    [0]
], dtype=float)

# 重み
W = np.random.randn(2, 1)
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

    if text == "テスト1":
        x = np.array([[1, 0]])
    elif text == "テスト2":
        x = np.array([[0, 1]])
    elif text == "テスト3":
        x = np.array([[1, 1]])
    else:
        print("めいな：まだ分かりません。")
        continue

    result = sigmoid(x @ W + b)[0][0]

    if result > 0.5:
        print("めいな：YES")
    else:
        print("めいな：NO")