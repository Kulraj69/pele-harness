"""Scripted local plumbing fixture; not a model or competition submission."""
import argparse
import json
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def reply(body):
    messages = body.get("messages", [])
    latest = messages[-1].get("content", "") if messages else ""
    first = str(next((m.get("content", "") for m in messages if m.get("role") == "user"), ""))
    tools = {t["name"]: t for t in body.get("tools", [])}
    results = [b for b in latest if isinstance(b, dict) and b.get("type") == "tool_result"] if isinstance(latest, list) else []
    if any(b.get("is_error") for b in results):
        raise ValueError("scripted tool failed: " + str(results))
    if results:
        previous = next((m for m in reversed(messages[:-1]) if m.get("role") == "assistant"), {})
        calls = [b for b in previous.get("content", []) if isinstance(b, dict) and b.get("type") == "tool_use"]
        if calls and ("secret_word" in calls[-1]["name"] or calls[-1]["name"] == "codemode"):
            word = re.search(r"MCP-[A-Z0-9]+", str(results))
            if not word:
                raise ValueError("MCP tool returned no secret word")
            name, args = "write", {"path": "/app/mcp.txt", "content": word[0] + "\n"}
        else:
            return [{"type": "text", "text": "done"}], "end_turn"
    elif "Final engineering verification pass:" in str(latest):
        name = "read"
        args = {"path": "/app/hello.txt" if "hello.txt" in first else "/app/mcp.txt"}
    elif "mcp.txt" in first:
        name = next((n for n in tools if "secret_word" in n), "")
        if not name and "codemode" in tools:
            name = "codemode"
            args = {"code": 'const found = searchTools("secret_word"); if (!found.length) throw new Error("No MCP secret_word tool"); console.log(JSON.stringify(await tools[found[0].name]({})));'}
        elif not name:
            raise ValueError("no secret_word tool advertised; available: " + str(list(tools)))
        else:
            args = {}
    elif "hello.txt" in first:
        name, args = "write", {"path": "/app/hello.txt", "content": "HELLO\n"}
    else:
        return [{"type": "text", "text": "OK"}], "end_turn"
    if name not in tools:
        raise ValueError("tool not advertised: " + name)
    return [{"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex, "name": name, "input": args}], "tool_use"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            if self.path.split("?")[0] == "/v1/chat/completions":
                return self.send_json(200, {"id": "mock-probe", "object": "chat.completion", "model": body.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
            if self.path.split("?")[0] != "/v1/messages":
                return self.send_json(404, {"error": "unknown endpoint"})
            content, stop = reply(body)
            print(json.dumps({"path": self.path, "tools": [t["name"] for t in body.get("tools", [])], "response": content}), flush=True)
            message = {"id": "msg_" + uuid.uuid4().hex, "type": "message", "role": "assistant", "model": body.get("model", "mock"), "content": content, "stop_reason": stop, "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}
            if not body.get("stream"):
                return self.send_json(200, message)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.event("message_start", {"message": {**message, "content": [], "stop_reason": None, "usage": {"input_tokens": 1, "output_tokens": 0}}})
            for i, block in enumerate(content):
                tool = block["type"] == "tool_use"
                self.event("content_block_start", {"index": i, "content_block": {**block, "input": {}} if tool else {"type": "text", "text": ""}})
                delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])} if tool else {"type": "text_delta", "text": block["text"]}
                self.event("content_block_delta", {"index": i, "delta": delta})
                self.event("content_block_stop", {"index": i})
            self.event("message_delta", {"delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 1}})
            self.event("message_stop", {})
        except (ValueError, KeyError, TypeError) as exc:
            self.send_json(400, {"type": "error", "error": {"type": "invalid_request_error", "message": str(exc)}})

    def event(self, kind, data):
        self.wfile.write(("event: " + kind + "\ndata: " + json.dumps({"type": kind, **data}) + "\n\n").encode())
        self.wfile.flush()

    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=4000)
    args = parser.parse_args()
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
