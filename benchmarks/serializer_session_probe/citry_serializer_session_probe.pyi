class Session:
    def __init__(self, placeholder_attr: str) -> None: ...
    def add_frame(
        self,
        key: str,
        parent_key: str | None,
        html: str,
        own_plain: list[str],
        own_valued: list[str],
        has_children: bool,
        placeholder_map: dict[str, str],
    ) -> None: ...
    def frame_count(self) -> int: ...
    def finish(self) -> str: ...
