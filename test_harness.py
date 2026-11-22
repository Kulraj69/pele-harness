import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import harness


class RunTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = SimpleNamespace(final_message="", log=AsyncMock(), usage=AsyncMock())
        self.run = harness.Run(self.session, "fixture")

    async def emit(self, reason="stop", text="", tools=False):
        blocks = [{"type": "text", "text": text}]
        if tools:
            blocks.append({"type": "toolCall", "id": "1", "name": "read", "arguments": {}})
        await self.run.on_event({"type": "message_end", "message": {
            "role": "assistant", "stopReason": reason, "content": blocks,
            "usage": {"input": 2, "output": 3, "cacheRead": 5, "cacheWrite": 7},
        }})

    async def test_completed_verification_replaces_summary(self):
        await self.emit(text="first summary")
        await self.emit(text="verified summary")
        self.assertEqual(self.session.final_message, "verified summary")
        self.assertEqual(self.run.replies, 2)
        self.session.usage.assert_awaited_with("fixture", input_tokens=14, output_tokens=3, cache_read_tokens=5)

    async def test_tool_turn_preserves_completed_summary(self):
        await self.emit(text="main summary")
        await self.emit("toolUse", "checking files", tools=True)
        self.assertEqual(self.session.final_message, "main summary")

    async def test_initial_tool_turn_can_supply_fallback(self):
        await self.emit("toolUse", "working", tools=True)
        self.assertEqual(self.session.final_message, "working")

    async def test_failed_turns_neither_count_nor_replace_summary(self):
        for reason in ("error", "aborted"):
            with self.subTest(reason=reason):
                self.session.final_message = "completed summary"
                await self.emit(reason, "partial verification")
                self.assertEqual(self.run.replies, 0)
                self.assertEqual(self.session.final_message, "completed summary")

    async def test_empty_and_failed_first_turns_leave_no_summary(self):
        await self.emit("error", "partial answer")
        await self.emit("aborted", "partial answer")
        self.assertEqual(self.run.replies, 0)
        self.assertEqual(self.session.final_message, "")
        await self.emit()
        self.assertEqual(self.session.final_message, "")

    async def test_non_assistant_and_invalid_lines_are_ignored(self):
        await self.run.on_line(b"not json")
        await self.run.on_line(b"[]")
        await self.run.on_event({"type": "message_end", "message": {"role": "user"}})
        self.assertEqual(self.run.replies, 0)


class SolveBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_deadline_and_shared_process_budget(self):
        for remaining, expected in ((None, "0"), (500, "1410000"), (20, "1000000")):
            with self.subTest(remaining=remaining):
                session = SimpleNamespace(time_left=lambda: remaining, workdir="/app", instruction="fixture",
                                          final_message="", log=AsyncMock(), usage=AsyncMock())
                relay = SimpleNamespace(env=lambda: {})
                context = AsyncMock()
                context.__aenter__.return_value = relay

                async def process(argv, current, **kwargs):
                    self.assertEqual(kwargs["env"]["TASK_VERIFICATION_DEADLINE_MS"], expected)
                    self.assertEqual(kwargs["stop_before_sec"], harness.STOP_BEFORE_SEC)
                    await kwargs["on_line"](json.dumps({"type": "message_end", "message": {
                        "role": "assistant", "stopReason": "stop", "content": [{"type": "text", "text": "done"}],
                    }}).encode())
                    return SimpleNamespace(code=0, stderr="")

                with patch.object(harness.taskbridge, "Relay", return_value=context), \
                     patch.object(harness, "configure", return_value=("fixture", "fixture")), \
                     patch.object(harness.taskbridge, "run_process", side_effect=process), \
                     patch.object(harness.time, "time", return_value=1000):
                    self.assertEqual(await harness.solve(session), "done")


if __name__ == "__main__":
    unittest.main()
