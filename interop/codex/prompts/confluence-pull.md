---
description: "Trae a tu carpeta local (docs/) el estado actual de Confluence, sin git. Sentido inverso de la publicación: baja Confluence → docs/, preservando tu frontmatter y avisando de conflictos antes de escribir. Pensado para PMs que no usan git. Usa la skill confluence-pull."
argument-hint: "(opcional) subcarpeta a traer, p. ej. 'roadmap'"
---
<!-- GENERADO por scripts/export-interop.py desde commands/confluence-pull.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/confluence-pull.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: se delega pidiéndolo en lenguaje natural y nombrando al agente (`reviewer`, `implementer`…), y los agentes custom se copian a `.codex/agents/`.
> Las skills se invocan mencionándolas con `$nombre`. Todo lo demás (puertas, artefactos, ledger) no cambia.

# /confluence-pull — poner al día tus docs desde Confluence

Para trabajar sin git: baja a tu carpeta lo que otros han actualizado en Confluence. Es un
asistente guiado que **previsualiza y pide confirmación** antes de tocar tus ficheros. Objetivo
opcional (limitar a una subcarpeta): **$ARGUMENTS**.

## Pasos
1. Invoca la skill **`confluence-pull`**. Ella comprueba conexión y config, respeta el opt-in del proyecto y usa el mapeo página↔fichero de `.claude/confluence-state.json`.
2. Si el proyecto **nunca** se sincronizó (sin `.claude/confluence.json`), no hay de dónde bajar: dilo y remite a **`/... publicar en Confluence`** (skill `confluence-publish`) para el alta.
3. Muestra el resumen de la skill (a actualizar / a crear / conflictos / sin cambios) y **espera el "sí"** antes de escribir en local.
4. Tras aplicar, si hay `docs/roadmap/`, la skill regenera el dashboard local. Resume qué se trajo y lista cualquier conflicto para que el usuario decida.

## Notas
- **Solo baja; no publica.** Para subir tus cambios, usa la publicación a Confluence (o deja que el hook la dispare). `pull` y `publish` comparten memoria (`.claude/confluence-state.json`), así que no duplican.
- **No pisa tu trabajo sin avisar:** si editaste algo en local y también cambió en Confluence, lo marca como conflicto y conserva lo tuyo por defecto.
- Nunca baja `docs/security-scan/`.
