class ProgressManager:

    def __init__(self) -> None:
        self.progresses: list[dict[str, tuple[str, bool]]] = []

    def add_progress(self, token: str, name: str) -> None:
        self.progresses.append({
            "token": token,
            "name": name,
            "completed": False,
        })

    def set_completed(self, token: str) -> None:
        for progress in self.progresses:
            if progress["token"] == token:
                progress["completed"] = True

    def as_string(self) -> str:
        " ".join([progress["name"] for progress in filter(lambda progress: progress["completed"] == False, self.progresses)])