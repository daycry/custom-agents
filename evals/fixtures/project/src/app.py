"""demo-app: aplicación mínima de fixture (sin dependencias)."""


def saludo(nombre: str) -> str:
    return f"Hola, {nombre}"


def exportar_csv(filas):
    """Devuelve las filas como CSV simple (sin comillas ni escapes: fixture)."""
    return "\n".join(",".join(str(c) for c in fila) for fila in filas)
