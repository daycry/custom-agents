---
name: code-health
description: >
  Informe DETERMINISTA y agnóstico de lenguaje de la salud de un árbol de código, con el script
  `code-health.py` (sin modelo, con tests): (1) duplicados por shingles de tokens normalizados entre
  ficheros con pares `fichero:línea`, (2) tamaño y complejidad aproximada (líneas, anidamiento,
  funciones largas), (3) hotspots — ficheros grandes Y que cambian mucho según `git log` — y
  (4) TODO/FIXME/HACK con su antigüedad por `git blame`. Salida Markdown legible o `--json`, y
  `--baseline` para ver si mejora o empeora. Lo usa `evaluator` para ajustar riesgo/complejidad de
  una spec y `planner` para abrir tareas de deuda; `/roadmap-brief` puede incluir el resumen. NO
  refactoriza (eso es `quick-implement`/`implementer`) ni busca vulnerabilidades (eso es
  `nemesis`/`cybersecurity`). Úsala cuando el usuario diga "salud del código", "informe de
  deuda técnica", "dónde hay código duplicado", "qué ficheros son hotspots", "cuántos TODO viejos
  hay", "mide la complejidad del repo", o cuando `evaluator` necesite fundamentar el riesgo de una
  spec sobre un repo grande.
---

# code-health — medir la salud del código antes de opinar sobre ella

Cuatro medidas **deterministas** (regex y tokens, sin modelo) sobre un árbol de código, para que
`evaluator` fundamente complejidad y riesgo con números y `planner` abra deuda con `fichero:línea`,
en vez de «el código está sucio». Todas son **heurísticas honestas**: sirven para ordenar y comparar
(hoy vs. baseline), no para juzgar una línea concreta — el informe lo dice en su cabecera.

> **Regla.** El script decide los números; la prosa decide qué hacer con ellos. Nunca «estimes» un
> porcentaje de duplicado: ejecuta el script y pega la salida.

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):

```bash
CHSKILL="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/code-health' 2>/dev/null | head -1)"
python3 "$CHSKILL/scripts/code-health.py" <ruta> [--json] [--exclude-tests] [--baseline informe.json]
```

## Cuándo NO usarla

| Parece esto, pero es… | Pieza correcta |
|---|---|
| «Refactoriza este fichero / quita el duplicado» (cambiar código) | `quick-implement` (vía rápida de `/dev-cycle`) o `implementer` con ledger |
| «Busca vulnerabilidades / secretos / dependencias con CVE» | `nemesis` (skill `cybersecurity`); dependencias desactualizadas → `dependency-upgrade` |
| «Corre los tests y dime si pasa» | `qa` (`qa-gate.py`) |
| «Por qué falla esto» | `debug-root-cause` |
| «Cuánto costaría la iniciativa X» | `evaluator` (que puede llamar a esta skill como insumo, no al revés) |

## Las 4 medidas (qué mide cada una y cómo leerla)

| # | Medida | Cómo se calcula | Cómo leerla |
|---|---|---|---|
| 1 | **Duplicados** | Ventanas de `--window` (8) líneas de código normalizadas (identificadores → `id`, números/cadenas → `num`/`str`, sin comentarios) iguales entre ficheros DISTINTOS; ventanas solapadas se colapsan en un bloque | `% duplicado` global y pares `A:línea ↔ B:línea` ordenados por tamaño. > 5 % o bloques > 20 líneas = candidato a extraer función/módulo |
| 2 | **Tamaño y complejidad** | Líneas de código por fichero, anidamiento máx. (llaves en JS/PHP/Go/Java/C#/Kt/Rs; sentencias compuestas en Py/Rb) y funciones con más de `--min-lines`×5 líneas (cabecera por regex por lenguaje) | Ficheros > 400 líneas o anidamiento > 5 y funciones > 30 líneas concentran el riesgo de cambio; **aproximación**, no un parser |
| 3 | **Hotspots** | `git log --since N days --name-only` × tamaño: `cambios × log2(líneas+1)` | Los grandes Y que cambian mucho: ahí van los tests y la revisión primero. Sin git: omitido con aviso |
| 4 | **TODO/FIXME/HACK/XXX** | Regex por línea (la palabra seguida de `:`/`(`/`-` o abriendo el comentario — así «TODO» como palabra castellana en medio de una frase no cuenta) + `git blame -L` para la antigüedad en días | Un TODO de 400 días es deuda olvidada o decisión no tomada: pregúntalo, no lo ignores. Sin git: solo recuento |

Extensiones por defecto: `py js ts tsx jsx php go java rb cs kt rs` (`--langs`). Siempre fuera:
`vendor/ node_modules/ dist/ build/ .git/ __pycache__/ target/`; con `--exclude-tests` también
`tests/`, `test_*.py`, `*.spec.*`/`*.test.*`.

## Proceso

1. **Ejecuta** sobre la raíz del repo (o la carpeta que toque la spec): `python3 "$CHSKILL/scripts/code-health.py" . --exclude-tests`
   (añade `--json > docs/roadmap/<inic>/code-health.json` si quieres guardar baseline). Exit 0 siempre;
   2 solo por ruta inexistente o baseline ilegible. Sin git en la ruta, el informe lo avisa.
2. **Lee la cabecera** (una línea con los totales) y las tablas top-10. Traduce a decisiones, con la
   cita del informe: duplicados → «extraer X (A:12 ↔ B:40, 25 líneas)»; hotspots → «tests primero
   en Y (8 cambios/90 d, 600 líneas)»; TODO viejos → «decidir Z (TODO de 400 días en W:88)».
3. **Cierra según quién te invoque:**
   - `evaluator` (P2 recon, opt-in: si el usuario lo pide o el repo tiene > 200 ficheros de código):
     usa `% duplicado`, hotspots y funciones largas para **subir complejidad/riesgo** de las `C-XX`
     que tocan esos ficheros y cítalo en «Riesgos» («hotspot: 8 cambios/90 d»). No cambia horas por
     sí solo; justifica un margen.
   - `planner` (P3): abre **tareas de deuda** solo si están en el alcance de la spec (o propón una
     iniciativa aparte); cada tarea cita `fichero:línea` del informe y su `Verificación` es volver a
     ejecutar el script con `--baseline` → «↓ mejora» en la métrica tocada.
   - `/roadmap-brief`: una fila «Salud del código» con la cabecera del informe (opcional).
   - A demanda: entrega el MD tal cual (o la sección que pidan) sin adornos.

## Guardrails

- **Solo lectura.** El script no toca ningún fichero del proyecto; si guardas el JSON, hazlo bajo
  `docs/roadmap/<inic>/` (Confluence lo publicaría: si no quieres, `docs/roadmap/<inic>/testing/`).
- **No inventes cifras** ni «redondees» las del informe; pega la cabecera literal.
- **Repos grandes:** limita con `--langs` o pasa una subcarpeta; el shingling es O(líneas) pero la
  antigüedad hace un `git blame -L` por marcador (todos, para poder ordenarlos): con cientos de TODO
  tarda — acota la ruta antes que esperar.
- **Degradación:** sin `python3` no hay skill (dilo y sigue); sin git faltan 3 y la edad de 4 (el
  informe lo declara).

## Qué NO hace

No refactoriza, no propone el diseño del refactor (eso es `architect`/`implementer`), no mide
cobertura de tests (`qa`), no detecta vulnerabilidades ni dependencias inseguras (`nemesis`,
`cybersecurity`), no versiona dependencias (`dependency-upgrade`) y no es un linter de estilo.

## Scripts propios

| Fichero | Qué es |
|---|---|
| `scripts/code-health.py` | El informe (MD/JSON, `--baseline`, `--exclude-tests`, `--langs`, `--window`, `--min-lines`, `--since`, `--top`); exit 0 · 2 uso |
| Tests (junto al script; no viajan en el paquete portable) | 14 casos con fixture multi-lenguaje (py/js/php) generada en tmp y git real si está: `python3 -m pytest -q skills/code-health/scripts` |
