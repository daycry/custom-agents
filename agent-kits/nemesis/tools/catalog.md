# Catálogo de herramientas opcionales de Nemesis

La fuente ejecutable del catálogo es `tools-lock.json`. `install-tools.sh` sólo localiza Python 3.10+ y llama a `install-tools.py`. No instala nada al cargar el plugin. El agente solicita autorización antes de instalar; los binarios quedan fuera de los repositorios, bajo `~/.claude/security-tools/` o `SECURITY_TOOLS_DIR`.

## Binarios fijados por plataforma

| Herramienta | Uso | Release fijada | Plataformas fijadas |
|---|---|---|---|
| nuclei | Plantillas de vulnerabilidades y exposición | v3.11.1 | Linux/macOS amd64 y arm64; Windows amd64 |
| httpx | Sondeo HTTP | v1.12.0 | Linux/macOS amd64 y arm64; Windows amd64 |
| ffuf | Descubrimiento y fuzzing autorizado | v2.3.0 | Linux/macOS/Windows amd64 y arm64 |
| gitleaks | Detección de secretos | v8.30.1 | Linux/macOS/Windows amd64 y arm64 |
| trivy | Dependencias y configuración | v0.76.2 | Linux/macOS amd64 y arm64; Windows amd64 |
| hadolint | Dockerfiles | v2.15.1 | Linux/macOS amd64 y arm64; Windows amd64 |

No hay selección dinámica de releases ni fallback entre arquitecturas. `pick_asset.py` se conserva como utilidad de mantenimiento; el instalador utiliza exclusivamente las URLs y SHA-256 revisadas del lock. trivy y hadolint corren en `run-static.sh`, sobre archivos del proyecto. Sus datos posteriores, como la base CVE de trivy o las plantillas de nuclei, no forman parte de estos pins.

## Scripts de commits concretos

| Herramienta | Fuente actual | Versión | Runtime |
|---|---|---|---|
| testssl | testssl/testssl.sh | v3.2.5 | Bash y OpenSSL |
| sqlmap | sqlmapproject/sqlmap | 1.10 | Python; ejecución activa con opt-in |
| nikto | sullo/nikto | 2.6.1 | Perl |

El lock fija también el commit completo y el SHA-256 del archivo de código. El instalador valida archivos y crea un lanzador en `bin/` hacia una carpeta de versión propia. No ejecuta git clone ni git pull. El lanzador Python conserva `-I -B` y añade únicamente el árbol verificado a la búsqueda de módulos para que SQLmap cargue sus módulos hermanos.

## Paquetes Python

wafw00f 2.4.2 y sus seis dependencias usan wheels universales de PyPI, fijados en `wafw00f-requirements.txt`. pip usa hashes obligatorios, no resuelve dependencias nuevas, no construye código fuente y escribe en un destino privado. Los requisitos conservan LF para que su hash sea estable en Windows. No se modifican paquetes globales ni se ejecuta la herramienta durante la instalación.

## Mantener o ampliar el catálogo

1. Verifica el proyecto upstream, su licencia, release y runtime; justifica la necesidad de la herramienta.
2. Actualiza `tools-lock.json`: versión, URL de procedencia, assets por plataforma, commit para scripts y SHA-256 de cada descarga. No uses hashes resueltos durante la instalación.
3. Para paquetes Python, fija todos los wheels y dependencias en `wafw00f-requirements.txt` y renueva su hash y procedencia en el lock. Un backend Python distinto requiere su implementación y sus pruebas; cambiar el nombre del paquete no basta.
4. Añade pruebas sintéticas de integridad, plataforma, formato y lanzador; revisa el diff y esta tabla. No ejecutes herramientas externas para verificar su versión durante la instalación.
5. Consulta `python3 install-tools.py --list`; instala sólo la selección autorizada con `--only nombre1,nombre2`.

`--force` reemplaza únicamente una instalación gestionada intacta. Conserva archivos desconocidos o modificados. Para migrar una instalación anterior usa una carpeta nueva. Los fallos dejan un aviso y código no cero sin impedir el trabajo general del plugin; el agente continúa con cobertura parcial.

[Guía de seguridad, recuperación y límites](../../../docs/guides/nemesis-remediation.md). Si un antivirus pone un archivo en cuarentena, revisa la alerta y su procedencia; no desactives la protección ni añadas una exclusión general por recomendación automática del plugin.
