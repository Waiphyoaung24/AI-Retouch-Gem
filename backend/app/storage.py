import json
from pathlib import Path
from typing import List, Dict, Any, TypeVar, Generic

T = TypeVar("T")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

class JSONStorage(Generic[T]):
    def __init__(self, filename: str, model_cls: T):
        self.file_path = DATA_DIR / filename
        self.model_cls = model_cls
        self.data: Dict[str, T] = {}
        self.load()

    def load(self):
        if self.file_path.exists():
            with self.file_path.open("r") as f:
                try:
                    raw_data = json.load(f)
                    self.data = {k: self.model_cls(**v) for k, v in raw_data.items()}
                except json.JSONDecodeError:
                    self.data = {}
        else:
            self.data = {}

    def save(self):
        with self.file_path.open("w") as f:
            json.dump({k: v.model_dump() for k, v in self.data.items()}, f, default=str)

    def get_all(self) -> List[T]:
        return list(self.data.values())

    def get(self, id: str) -> T:
        return self.data.get(id)

    def add(self, item: T):
        self.data[item.id] = item
        self.save()

    def delete(self, id: str):
        if id in self.data:
            del self.data[id]
            self.save()
