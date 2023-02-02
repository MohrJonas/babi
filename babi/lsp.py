from json import loads, dumps
from os import getpid
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT


class LSPClient:
    opened_document: Path | None
    process: Popen[bytes]
    message_id: int

    def __init__(self, server_executable: str):
        self.process = Popen([server_executable, "-v"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        self.message_id = 0
        self.opened_document = None

    def build_message(self, method: str, param: dict | None) -> bytes:
        obj = {"jsonrpc": "2.0", "id": self.message_id, "method": method, "params": param}
        text = dumps(obj)
        return bytes(
            "Content-Length: {length}\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n{text}".format(
                length=len(text), text=text), "utf-8")

    def initialize(self, capabilities: dict) -> dict:
        message = self.build_message("initialize",
                                     {"processId": getpid(), "clientInfo": {"client": "babi", "version": "1.0"},
                                      "locale": "en", "capabilities": capabilities, "trace": "verbose",
                                      "workspaceFolders": None})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def send_message(self, message: bytes):
        self.process.stdin.write(message)
        self.process.stdin.flush()

    def read_response(self) -> str:
        while True:
            content_size = None
            while True:
                line = self.process.stdout.readline().decode("utf-8").strip()
                if not line:
                    if not content_size:
                        raise ValueError("Content-Length header not found")
                    else:
                        break
                if "Content-Length" in line:
                    content_size = int(line.split(": ")[1])
            content = self.process.stdout.read(content_size).decode("utf-8")
            if "$/progress" in content or loads(content).get("method") == "textDocument/publishDiagnostics":
                pass
            else:
                break
        return content

    def open_document(self, file: Path) -> dict:
        message = self.build_message("textDocument/didOpen", {
            "textDocument": {"uri": file.as_uri(), "languageId": "python", "version": self.message_id,
                             "text": file.read_text()}})
        self.message_id += 1
        self.opened_document = file
        self.send_message(message)
        return loads(self.read_response())

    def change_document(self, version: int, content: str) -> dict:
        message = self.build_message("textDocument/didChange",
                                     {"textDocument": {"version": version, "uri": self.opened_document.as_uri()},
                                      "contentChanges": [{"text": content, }]})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def close_document(self):
        message = self.build_message("textDocument/didClose", {"textDocument": {"uri": self.opened_document.as_uri()}})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def initialized(self) -> dict:
        message = self.build_message("initialized", {})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def get_definition(self, cursor_row: int, cursor_column: int) -> dict:
        message = self.build_message("textDocument/definition", {"textDocument": {"uri": self.opened_document.as_uri()},
                                                                 "position": {"line": cursor_row,
                                                                              "character": cursor_column},
                                                                 "workDoneToken": None, "partialResultToken": None})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def get_autocompletion(self, cursor_row: int, cursor_column: int) -> dict:
        message = self.build_message("textDocument/completion", {
            "textDocument": {"uri": self.opened_document.as_uri()},
            "position": {"line": cursor_row, "character": cursor_column}, "workDoneToken": None,
            "partialResultToken": None})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def get_diagnostics(self) -> dict:
        message = self.build_message("textDocument/diagnostic", {
            "textDocument": {"uri": Path("/home/jonas/Development/babi/lsp/test.py").as_uri()},
            "identifier": None, "previousResultId": None, "workDoneToken": None, "partialResultToken": None})
        self.message_id += 1
        self.send_message(message)
        return loads(self.read_response())

    def shutdown(self) -> int:
        self.send_message(self.build_message("shutdown", None))
        self.send_message(self.build_message("exit", None))
        return self.process.wait()
