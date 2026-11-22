import unittest

from server import reply


class ScriptTests(unittest.TestCase):
    def test_empty_probe(self):
        self.assertEqual(reply({}), ([{"type": "text", "text": "OK"}], "end_turn"))

    def test_smoke_then_finish(self):
        body = {"messages": [{"role": "user", "content": "Create hello.txt"}], "tools": [{"name": "write"}]}
        blocks, stop = reply(body)
        self.assertEqual(stop, "tool_use")
        self.assertEqual(blocks[0]["input"], {"path": "/app/hello.txt", "content": "HELLO\n"})
        body["messages"] += [{"role": "assistant", "content": blocks}, {"role": "user", "content": [{"type": "tool_result", "content": "success"}]}]
        self.assertEqual(reply(body)[1], "end_turn")

    def test_mcp_word_is_from_result(self):
        body = {"messages": [{"role": "user", "content": "Create mcp.txt"}], "tools": [{"name": "apps_secret_word"}, {"name": "write"}]}
        blocks, _ = reply(body)
        self.assertEqual(blocks[0]["name"], "apps_secret_word")
        body["messages"] += [{"role": "assistant", "content": blocks}, {"role": "user", "content": [{"type": "tool_result", "content": "MCP-AB1234"}]}]
        self.assertEqual(reply(body)[0][0]["input"]["content"], "MCP-AB1234\n")

    def test_missing_tool(self):
        with self.assertRaises(ValueError):
            reply({"messages": [{"role": "user", "content": "Create hello.txt"}]})

    def test_deferred_mcp_discovery(self):
        blocks, stop = reply({"messages": [{"role": "user", "content": "Create mcp.txt"}], "tools": [{"name": "codemode"}]})
        self.assertEqual(stop, "tool_use")
        self.assertEqual(blocks[0]["name"], "codemode")
        self.assertIn('searchTools("secret_word")', blocks[0]["input"]["code"])

    def test_verification_followup_reads_output_then_finishes(self):
        body = {"messages": [{"role": "user", "content": "Create hello.txt"}, {"role": "assistant", "content": [{"type": "text", "text": "done"}]}, {"role": "user", "content": "Final engineering verification pass:"}], "tools": [{"name": "read"}]}
        blocks, stop = reply(body)
        self.assertEqual(stop, "tool_use")
        self.assertEqual(blocks[0]["name"], "read")
        self.assertEqual(blocks[0]["input"], {"path": "/app/hello.txt"})
        body["messages"] += [{"role": "assistant", "content": blocks}, {"role": "user", "content": [{"type": "tool_result", "content": "HELLO"}]}]
        self.assertEqual(reply(body), ([{"type": "text", "text": "done"}], "end_turn"))

    def test_tool_error(self):
        with self.assertRaises(ValueError):
            reply({"messages": [{"role": "user", "content": [{"type": "tool_result", "is_error": True}]}]})


if __name__ == "__main__":
    unittest.main()
