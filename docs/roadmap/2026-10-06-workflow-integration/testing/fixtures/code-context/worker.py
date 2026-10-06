def normalize_name(name: str) -> str:
    return name.strip().lower()


def process_order(name: str) -> str:
    return normalize_name(name)
