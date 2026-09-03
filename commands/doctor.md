---
description: Diagnóstico de la instalación del plugin en este proyecto — herramientas (python3, git, jq, node, Playwright), plugin y hooks registrados, statusline, configs de .claude (rates, dev, jira, confluence) y estado del trabajo (marcadores de medición huérfanos, iniciativas en progreso, journal, evals), con veredicto ✅/⚠️/❌ y el arreglo concreto de cada línea. Solo lee; no toca nada y no usa red. Úsalo cuando el usuario diga "¿está bien instalado?", "diagnostica el plugin", "por qué no funciona el hook", "comprueba mi configuración", "doctor".
argument-hint: "(opcional) --json para la salida en JSON"
---

# /doctor — ¿está todo en su sitio?

Primera parada cuando algo "no salta": el hook que no aparece, la statusline que no se ve, el
coste que sale a 0, la skill que no encuentra su script. Comprueba la instalación **sin tocar
nada** y sin red: cada línea lleva su veredicto y, si algo falla, **qué comando lo arregla**.

## Pasos
1. Localiza el script del kit compartido y ejecútalo:

   ```bash
   DOC="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*agent-kits/shared/doctor.py' 2>/dev/null | head -1)"
   python3 "$DOC"            # informe Markdown · exit 0 sin ❌, 1 con ❌
   python3 "$DOC" --json     # lo mismo para consumo por script
   ```

2. Presenta el informe tal cual y **resume en 2-3 líneas**: cuántos ✅/⚠️/❌ y, si hay ❌, el
   primero con su arreglo. No repitas la tabla en prosa.
3. Si hay ❌ o ⚠️ que el usuario quiera resolver ahora, ofrece el arreglo que indica la propia
   línea (normalmente `/setup`, `rates-verify`, o un `chmod +x`); no lo apliques sin su OK.

## Notas
- **Qué es cada símbolo**: ✅ correcto · ⚠️ funciona pero a medias (opt-in a medio configurar,
  precio de tokens sin verificar, hook no ejecutable) · ❌ roto (config corrupta, valor fuera de
  vocabulario, script que falta) · ℹ️ informativo (opcional no instalado, opt-in apagado a
  propósito, estado del trabajo) — las ℹ️ **no** hay que arreglarlas.
- **Sin red por diseño**: `/doctor` no consulta el marketplace, así que no puede decir si hay una
  versión más nueva del plugin; solo informa de la versión instalada.
- **No confundir con `/setup`**: `/doctor` diagnostica lo que ya hay (solo lectura); `/setup`
  configura y escribe (`rates.json`, `dev.json`, opt-ins de Jira/Confluence, statusline).
