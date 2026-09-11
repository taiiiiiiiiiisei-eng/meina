import unittest

import command_router


class CommandRouterTests(unittest.TestCase):
    def setUp(self):
        self.frame = {"confidence": 0.95}

    def test_app_aliases(self):
        cases = {
            "メモ帳を開いて": "notepad",
            "Discordを開いて": "Discord",
            "Steamを起動して": "Steam",
            "Chromeを開いて": "Chrome",
            "OBSを起動して": "OBS",
            "VALORANTを開いて": "VALORANT",
        }
        for text, target in cases.items():
            with self.subTest(text=text):
                result = command_router.route_command(text, self.frame)
                self.assertIsNotNone(result)
                self.assertEqual(result["kind"], "app_open")
                self.assertEqual(result["target"], target)

    def test_web_search(self):
        result = command_router.route_command(
            "GoogleでVALORANTについて検索して", self.frame
        )
        self.assertEqual(result["kind"], "web_search")
        self.assertEqual(result["target"], "google")
        self.assertEqual(result["query"], "valorant")

        result = command_router.route_command(
            "YouTubeでVALORANTの動画を検索して", self.frame
        )
        self.assertEqual(result["kind"], "web_search")
        self.assertEqual(result["target"], "youtube")
        self.assertEqual(result["query"], "valorantの動画")

    def test_reject_low_confidence(self):
        result = command_router.route_command(
            "メモ帳を開いて", {"confidence": 0.69}
        )
        self.assertIsNone(result)

    def test_reject_unknown_command(self):
        result = command_router.route_command("意味不明な命令", self.frame)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
