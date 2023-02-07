from functools import wraps
from json import loads, dumps
from os import getpid
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from typing import Callable, Optional


@staticmethod
def requires_lsp(f):
    @wraps(f)
    def decorator(*args):
        if args[0].file.lsp is not None:
            return f(*args)
    return decorator


class LSPClient(Thread):

    def __init__(self, server_executable: list[str]) -> None:
        super().__init__()
        self.process: Optional[Popen] = Popen(server_executable, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        self.message_id: int = 0
        self.opened_document: Optional[Path] = None
        self.document_version: int = 0
        self.listeners: list[Callable[[dict], None]] = []
        self.running: bool = True
        self.start()

    def run(self) -> None:
        while self.running:
            content = loads(self.__read_response())
            for listener in self.listeners:
                listener(content)

    def register_listener(self, listener: Callable[[dict], None]) -> None:
        self.listeners.append(listener)

    def __build_message(self, method: str, param: Optional[dict]) -> bytes:
        obj = {"jsonrpc": "2.0", "id": self.message_id, "method": method, "params": param}
        text = dumps(obj)
        return bytes(
            "Content-Length: {length}\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n{text}".format(
                length=len(text), text=text), "utf-8")

    def __send_message(self, message: bytes) -> None:
        self.process.stdin.write(message)
        self.process.stdin.flush()

    def __read_response(self) -> str:
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
        return content

    def initialize(self, capabilities: dict) -> None:
        message = self.__build_message("initialize",
                                       {"processId": getpid(), "clientInfo": {"client": "babi", "version": "1.0"},
                                        "locale": "en", "capabilities": capabilities, "trace": "verbose",
                                        "workspaceFolders": None})
        self.message_id += 1
        self.__send_message(message)

    def open_document(self, file: Path) -> None:
        message = self.__build_message("textDocument/didOpen", {
            "textDocument": {"uri": file.resolve().as_uri(), "languageId": "python", "version": self.message_id,
                             "text": file.read_text()}})
        self.message_id += 1
        self.opened_document = file.resolve()
        self.document_version = 0
        self.__send_message(message)

    def change_document(self, content: str) -> None:
        message = self.__build_message("textDocument/didChange",
                                       {"textDocument": {"version": self.document_version, "uri": self.opened_document.as_uri()},
                                        "contentChanges": [{"text": content, }]})
        self.message_id += 1
        self.__send_message(message)

    def close_document(self) -> None:
        message = self.__build_message("textDocument/didClose", {"textDocument": {"uri": self.opened_document.as_uri()}})
        self.message_id += 1
        self.__send_message(message)

    def initialized(self) -> None:
        message = self.__build_message("initialized", {})
        self.message_id += 1
        self.__send_message(message)

    def get_definition(self, cursor_row: int, cursor_column: int) -> None:
        message = self.__build_message("textDocument/definition", {"textDocument": {"uri": self.opened_document.as_uri()},
                                                                   "position": {"line": cursor_row,
                                                                                "character": cursor_column},
                                                                   "workDoneToken": None, "partialResultToken": None})
        self.message_id += 1
        self.__send_message(message)

    def get_autocompletion(self, row: int, column: int) -> None:
        message = self.__build_message("textDocument/completion", {
            "textDocument": {"uri": self.opened_document.as_uri()},
            "position": {"line": row, "character": column}, "workDoneToken": None, "partialResultToken": None})
        self.message_id += 1
        self.__send_message(message)

    def get_diagnostics(self) -> None:
        message = self.__build_message("textDocument/diagnostic", {
            "textDocument": {"uri": self.opened_document.as_uri()},
            "identifier": None, "previousResultId": None, "workDoneToken": None, "partialResultToken": None})
        self.message_id += 1
        self.__send_message(message)

    def shutdown(self) -> None:
        self.running = False
        self.__send_message(self.__build_message("shutdown", None))
        self.__send_message(self.__build_message("exit", None))
