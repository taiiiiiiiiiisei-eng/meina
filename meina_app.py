import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import traceback
import os
import meina_agent


RUNTIME_LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "meina_runtime_error.log",
)


def log_runtime_error(context, error):
    """GUI実行時エラーをファイルへ保存する。"""
    try:
        with open(RUNTIME_LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 72 + "\n")
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("context: " + str(context) + "\n")
            f.write("error: " + repr(error) + "\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception as log_error:
        print("ログ保存エラー:", log_error)


class MeinaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("めいな - AI Assistant")
        self.root.geometry("760x620")
        self.root.minsize(620, 500)

        self.busy = False

        header = tk.Frame(root)
        header.pack(fill="x", padx=18, pady=(16, 8))

        tk.Label(
            header,
            text="🤖 めいな",
            font=("Yu Gothic UI", 22, "bold"),
        ).pack(side="left")

        self.status = tk.Label(
            header,
            text="準備中...",
            font=("Yu Gothic UI", 10),
        )
        self.status.pack(side="right", pady=8)

        self.chat = tk.Text(
            root,
            wrap="word",
            font=("Yu Gothic UI", 12),
            state="disabled",
            padx=12,
            pady=12,
        )
        self.chat.pack(fill="both", expand=True, padx=18, pady=8)

        # 入力エリア
        bottom = tk.Frame(root, height=58)
        bottom.pack(fill="x", padx=18, pady=(4, 18))
        bottom.pack_propagate(False)

        self.entry = tk.Entry(
            bottom,
            font=("Yu Gothic UI", 13),
            relief="solid",
            bd=1,
        )
        self.entry.pack(side="left", fill="both", expand=True, ipady=8)

        self.send_button = tk.Button(
            bottom,
            text="送信",
            font=("Yu Gothic UI", 11, "bold"),
            command=self.send_text,
            padx=16,
        )
        self.send_button.pack(side="left", fill="y", padx=(8, 4))

        self.mic_button = tk.Button(
            bottom,
            text="🎤 話す",
            font=("Yu Gothic UI", 11, "bold"),
            command=self.start_voice,
            padx=12,
        )
        self.mic_button.pack(side="left", fill="y", padx=(4, 0))

        self.entry.bind("<Return>", lambda event: self.send_text())
        self.root.after(300, self._focus_entry)

        self.add_message("めいな", "起動しています。少し待ってください。")
        threading.Thread(target=self._initialize, daemon=True).start()

    def _focus_entry(self):
        if not self.busy:
            self.entry.configure(state="normal")
            self.entry.focus_set()

    def add_message(self, speaker, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{speaker}：{text}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def set_busy(self, busy, status=None):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.send_button.configure(state=state)
        self.mic_button.configure(state=state)
        self.entry.configure(state=state)
        if status:
            self.status.configure(text=status)

    def _initialize(self):
        self.root.after(0, lambda: self.set_busy(False, "オンライン"))
        self.root.after(0, lambda: self.add_message("めいな", "起動しました。質問してください。"))

    def send_text(self):
        if self.busy:
            return

        text = self.entry.get().strip()
        if not text:
            return

        self.entry.delete(0, "end")
        self.add_message("あなた", text)
        self.set_busy(True, "考え中...")
        threading.Thread(target=self._process_text, args=(text,), daemon=True).start()

    def _process_text(self, text):
        try:
            result = meina_agent.process_command(text)
            if not result:
                result = "処理が完了しました。"
            self.root.after(0, lambda r=result: self.add_message("めいな", r))
        except Exception as e:
            print("GUI処理エラー:", e)
            log_runtime_error("text", e)
            self.root.after(
                0,
                lambda: self.add_message(
                    "めいな",
                    "すみません、処理中にエラーが発生しました。"
                    " 詳細はmeina_runtime_error.logに保存しました。",
                ),
            )
        finally:
            self.root.after(0, lambda: self.set_busy(False, "オンライン"))

    def start_voice(self):
        if self.busy:
            return

        self.set_busy(True, "🎤 聞いています...")
        threading.Thread(target=self._process_voice, daemon=True).start()

    def _process_voice(self):
        try:
            text = meina_agent.listen(duration=5.0)
            if not text:
                self.root.after(0, lambda: self.add_message("めいな", "うまく聞き取れませんでした。"))
                return

            self.root.after(0, lambda t=text: self.add_message("あなた", t))

            command = meina_agent.remove_wake_word(text) if meina_agent.contains_wake_word(text) else text
            if not command:
                self.root.after(0, lambda: self.add_message("めいな", "はい、どうしました？"))
                meina_agent.speak("はい、どうしました？")
                command = meina_agent.listen(duration=5.0)
                if not command:
                    self.root.after(0, lambda: self.add_message("めいな", "うまく聞き取れませんでした。"))
                    return
                self.root.after(0, lambda t=command: self.add_message("あなた", t))
                if meina_agent.contains_wake_word(command):
                    command = meina_agent.remove_wake_word(command)
                if not command:
                    return

            result = meina_agent.process_command(command)
            if not result:
                result = "処理が完了しました。"
            self.root.after(0, lambda r=result: self.add_message("めいな", r))
        except Exception as e:
            print("GUI音声エラー:", e)
            log_runtime_error("voice", e)
            self.root.after(
                0,
                lambda: self.add_message(
                    "めいな",
                    "音声処理中にエラーが発生しました。"
                    " 詳細はmeina_runtime_error.logに保存しました。",
                ),
            )
        finally:
            self.root.after(0, lambda: self.set_busy(False, "オンライン"))


def main():
    root = tk.Tk()
    app = MeinaApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
