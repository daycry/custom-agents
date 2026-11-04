# Reconocimiento de deuda técnica

Lee en P2 cuando el usuario pida salud de código o el repositorio supere unos 200 ficheros de código. Limita el informe al paquete afectado cuando esté identificado y declara ese alcance.

**Salud del código (opt-in):** si el usuario lo pide o el repo tiene más de ~200 ficheros de código, ejecuta la skill `code-health` (`CHSKILL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*skills/code-health' 2>/dev/null | head -1)"; python3 "$CHSKILL/scripts/code-health.py" . --exclude-tests`, informe determinista: duplicados, funciones largas, hotspots, TODO viejos) y usa sus cifras para **subir complejidad/riesgo** de las `C-XX` que toquen ficheros duplicados o hotspots, citándolas en «Riesgos» («hotspot: 8 cambios/90 d, 600 líneas»); sin `python3`/git degrada con aviso y sigues.
