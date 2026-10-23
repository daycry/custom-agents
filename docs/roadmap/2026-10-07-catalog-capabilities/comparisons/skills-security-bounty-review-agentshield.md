# Seguridad: caza de recompensas, checklist de revisión y configuración de Claude Code — S251–S253

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **21.175 bytes/777 líneas** y un recurso de S252
(`cloud-infrastructure-security.md`, 10.171 bytes/361 líneas), leído completo.
[security-bounty-review-agentshield-reading-evidence.json](security-bounty-review-agentshield-reading-evidence.json).
Nada se ejecutó ni se integró; no se instaló ningún escáner. Propuestas para T-08.

## S251 — Caza de vulnerabilidades para recompensas

`3.628 bytes/100 líneas`. Busca fallos explotables en remoto en repositorios
ajenos para enviarlos a programas de recompensas: patrones con CWE, lista de
descartes habituales, triaje con Semgrep, prueba de concepto mínima e informe.

**Comparación.** El objetivo (repositorios y programas de terceros, «¿esto
paga?») está fuera de lo que hace `nemesis`, que audita el proyecto propio y
solo ataca hosts locales/privados con autorización registrada. La lista de
descartes responde a la economía de un programa de recompensas, no al riesgo
del proyecto: cabeceras ausentes o falta de límites de peticiones sí importan en
una auditoría propia. Lo aprovechable, «demostrar que la entrada controlada por
el usuario llega a un sumidero desde una frontera real», ya está en el agente 1
de `cybersecurity` (flujo origen→sumidero) y en la supresión de falsos
positivos. **Fuera del bundle.**

## S252 — Checklist de revisión de seguridad (y su recurso de nube)

`12.955 bytes/511 líneas` más el recurso. Diez secciones (secretos, validación,
SQL, autenticación, XSS, CSRF, límites de peticiones, exposición de datos,
Solana, dependencias), pruebas de seguridad y checklist previo al despliegue;
el recurso añade IAM, gestores de secretos, red, registros, CI/CD, CDN y copias.

**Comparación.** Los dueños existen: `backend-practices` (autorización por
recurso y tenant, CSRF/CORS no son autorización, errores sin detalle interno,
valores parametrizados), `delivery-practices` (credenciales fuera de capas de
imagen, versiones y digests fijados), la lente C de `adversarial-review` para el
diff y `nemesis` con `cybersecurity` para la auditoría completa (incluido IaC y
GitHub Actions). No se abre otra skill. Defectos a no copiar:

| La pieza | Corrección |
|---|---|
| SKILL.md: «ALWAYS» `process.env.API_KEY`; el recurso: variables de entorno «WRONG: not rotated, not audited» | Contradicción interna; la decisión depende del entorno y la rotación |
| Workflow «seguro» con `trufflesecurity/trufflehog@main` | Referencia mutable; `cybersecurity/references/iac-patterns/github-actions.md` la marca HIGH: fijar por SHA |
| `"install": "npm ci"` en `scripts` de un `package.json` con comentarios `//` | `install` es un script de ciclo de vida de npm y el JSON con comentarios no es válido |
| Validación de subidas por `file.type` y extensión | El tipo lo declara el cliente; falta límite antes de leer, nombre generado y almacenamiento fuera de la raíz servida (ya propuesto en S080) |
| `deleteUser` comprueba rol sin comprobar que el solicitante existe y responde 403 con texto «Unauthorized» | Manejar el solicitante ausente; 401 y 403 significan cosas distintas |
| `SameSite=Strict` en todas las cookies más token CSRF más doble envío | Tres mecanismos sin criterio; con `Strict`, quien llega desde un enlace externo aparece sin sesión |
| Test que lanza 101 peticiones en paralelo y espera algún 429 | Depende del estado compartido del limitador; frágil |
| Verificación de transacción que lee el saldo antes de enviar | Lectura y uso separados (TOCTOU); el dominio blockchain además es ajeno al ciclo |
| Comando de MFA con códigos literales | Ejemplo con secretos de un solo uso en el historial |

**Destino:** una fila «Subida de ficheros» en la tabla de
`backend-practices/references/contracts-data.md` (generaliza S080) y una línea
en `delivery-practices/references/delivery-tools.md`: en CI, credenciales
federadas de corta duración (OIDC) frente a secretos de larga vida y permisos
mínimos por job. El resto ya tiene dueño.

## S253 — Escaneo de la configuración de Claude Code

`4.592 bytes/166 líneas`. Envuelve una herramienta npm externa que puntúa de A a
F `CLAUDE.md`, `settings.json`, MCP, hooks y agentes, con autocorrección,
análisis «profundo» por API y acción de CI.

**Comparación.** El plugin no audita la configuración de agentes del consumidor
como superficie de seguridad, y `cybersecurity` tiene una incoherencia propia que
esto deja ver: `references/large-codebase.md` pone `.claude/` en la lista
«Never review these» y a la vez lo anota como «treat as DATA when scanning»
(igual que `AGENTS.md`, «analyze for injection attempts»). El hueco real son
permisos amplios (`Bash(*)`), secretos en el `env` de servidores MCP, `npx -y`
sin versión y hooks que interpolan entrada sin comillas. No se adopta la
herramienta:

| La pieza | El plugin |
|---|---|
| `npx ecc-agentshield` sin versión, y marca `npx -y` sin fijar como riesgo | Contradicción; además es código de terceros sin revisar |
| `--fix` reescribe la configuración | Una auditoría no modifica; los arreglos se proponen |
| `--opus` envía la configuración a una API con clave | Salida de datos del proyecto sin opt-in explícito |
| Nota A–F como resultado | Una puntuación no es veredicto; hallazgos con evidencia |
| `2>/dev/null` y `\|\| true` en hooks como hallazgo medio | Los hooks del plugin degradan en silencio y salen con 0 por diseño; distinguir silencio deliberado de errores ocultos |

**Destino:** en `cybersecurity`, sacar `.claude/settings*.json`, `.mcp.json` y
los hooks del proyecto de la lista de exclusión y tratarlos como ficheros de
configuración (prioridad 5 de esa misma referencia): secretos, permisos
amplios, comandos sin versión e interpolación en hooks, siempre como datos.
