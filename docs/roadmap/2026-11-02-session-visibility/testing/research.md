# Interfaces y prueba de hipótesis

Fecha: 2026-11-02. Lectura acotada, sin conversaciones crudas en artefactos.

| Alternativa | Evidencia | Decisión |
|---|---|---|
| Registro propio de la consola | SessionManager.list sólo lee sesiones propias; cero registros reales | Conservar para conexiones controlables, insuficiente para sesiones externas |
| Codex app-server thread/list | API oficial con filtro cwd y useStateDbOnly; consulta real devuelve cinco metadatos del proyecto e incluye la sesión actual | Adoptar el transporte existente, sin dependencia adicional |
| Escanear transcripciones personales | Exigiría parseo privado y permisos más amplios; no necesario para este caso | No usar |
| Hooks de actividad | Opt-in local desactivado; tras activarlo llegan eventos reales | Reutilizar capturador, sin inventar señales ni modificar instalación global |

Fuente primaria: [Codex App Server, listado y filtros](https://learn.chatgpt.com/docs/app-server#list-threads-with-pagination--filters).
La documentación distingue thread/list y thread/loaded/list; una nueva instancia
no acredita que una conversación externa esté ejecutándose en otro proceso.
Se descarta su status para la afirmación de liveness en el dashboard.

Se reutiliza código propio y el ejecutable instalado, sin copiar código externo
ni añadir SDKs. La compatibilidad se acredita con el ejecutable local además de
fixtures. Versiones y resultado final se anotan en report.md al terminar QA.
