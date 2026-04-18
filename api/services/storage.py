import json
import os
from typing import List, Optional, Type, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')


class StorageService(Generic[T]):
    def __init__(self, storage_path: str, model_class: Type[T]):
        self.storage_path = storage_path
        self.model_class = model_class
        os.makedirs(storage_path, exist_ok=True)

    def _get_file_path(self, item_id: str) -> str:
        return os.path.join(self.storage_path, f"{item_id}.json")

    def _list_files(self) -> List[str]:
        if not os.path.exists(self.storage_path):
            return []
        return [f[:-5] for f in os.listdir(self.storage_path) if f.endswith('.json')]

    def save(self, item: T) -> T:
        item.updated_at = datetime.now()
        file_path = self._get_file_path(item.id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(item.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
        return item

    def get(self, item_id: str) -> Optional[T]:
        file_path = self._get_file_path(item_id)
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.model_class(**data)

    def list(self) -> List[T]:
        items = []
        for item_id in self._list_files():
            item = self.get(item_id)
            if item:
                items.append(item)
        return items

    def delete(self, item_id: str) -> bool:
        file_path = self._get_file_path(item_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def exists(self, item_id: str) -> bool:
        return os.path.exists(self._get_file_path(item_id))
