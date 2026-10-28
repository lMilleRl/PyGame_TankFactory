import json
import tempfile
import unittest
from pathlib import Path

from py_bot import analytics, session
from py_bot.session import BotState


class AnalyticsTests(unittest.TestCase):
    def test_validate_layout_accepts_cbs_symbols(self):
        text = "#####\n#DCS#\n#B>N#\n#####\n"
        ok, msg = analytics.validate_layout_text(text)
        self.assertTrue(ok, msg)

    def test_validate_layout_rejects_bad_char(self):
        ok, msg = analytics.validate_layout_text("#####\n#DZX#\n#..S#\n#####\n")
        self.assertFalse(ok)
        self.assertIn("Недопустимые", msg)

    def test_top_sorts_by_efficiency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.csv"
            path.write_text(
                "timestamp,player_name,turns,parts_assembled,efficiency\n"
                "t1,A,30,3,0.1\n"
                "t2,B,20,3,0.15\n"
                "t3,C,10,1,0.1\n",
                encoding="utf-8",
            )
            top = analytics.top_by_efficiency(2, path)
            self.assertEqual(top[0]["player_name"], "B")
            self.assertEqual(len(top), 2)

    def test_player_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.csv"
            path.write_text(
                "timestamp,player_name,turns,parts_assembled,efficiency\n"
                "t1,Mark,40,3,0.075\n"
                "t2,Mark,30,3,0.1\n",
                encoding="utf-8",
            )
            info = analytics.player_stats("Mark", path)
            self.assertTrue(info["found"])
            self.assertEqual(info["games"], 2)
            self.assertEqual(info["best_turns"], 30)

    def test_save_stats_efficiency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "factory_save.json"
            path.write_text(
                json.dumps({"turn_count": 20, "assembly_stack": [0, 1, 2], "status": "won", "drone": {}}),
                encoding="utf-8",
            )
            stats = analytics.load_save_stats(path)
            self.assertTrue(stats["exists"])
            self.assertEqual(stats["efficiency"], 0.15)


class SessionTests(unittest.TestCase):
    def test_session_roundtrip_and_watchers(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            data = session.load_session(42, base)
            self.assertEqual(data["state"], BotState.MENU.value)
            data["watch"] = True
            data["player_name"] = "Mark"
            session.save_session(42, data, base)
            session.set_state(7, BotState.UPLOAD, base)
            watchers = session.list_watchers(base)
            self.assertEqual(watchers, [42])
            again = session.load_session(42, base)
            self.assertEqual(again["player_name"], "Mark")


class ImportTests(unittest.TestCase):
    def test_bot_module_imports(self):
        from py_bot import bot as bot_module

        self.assertTrue(hasattr(bot_module, "create_dispatcher"))
        self.assertTrue(hasattr(bot_module, "format_top"))


if __name__ == "__main__":
    unittest.main()
