from typing import Any, Dict, List, Optional


def _backend_name() -> str:
    return "phase2"


def _backend():
    from modules import crud_phase2

    return crud_phase2


def get_backend_name() -> str:
    return _backend_name()


def get_storage_path() -> str:
    return _backend().get_storage_path()


def initialize() -> None:
    backend = _backend()
    if hasattr(backend, "initialize"):
        backend.initialize()


def create(record_data: Dict[str, Any], package_id: str, author: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    return _backend().create(record_data, package_id, author, date_str)


def read_day(date_str: str) -> List[Dict[str, Any]]:
    return _backend().read_day(date_str)


def search(query: str, month_year: str) -> List[Dict[str, Any]]:
    return _backend().search(query, month_year)


def update(record_id: str, date_str: str, data: Dict[str, Any]) -> bool:
    return _backend().update(record_id, date_str, data)


def delete(record_id: str, date_str: str) -> bool:
    return _backend().delete(record_id, date_str)


def load_encounter(record_id: str) -> Optional[Dict[str, Any]]:
    backend = _backend()
    if hasattr(backend, "load_encounter"):
        return backend.load_encounter(record_id)

    return None


def mark_all_synced() -> None:
    backend = _backend()
    if hasattr(backend, "mark_all_synced"):
        backend.mark_all_synced()
