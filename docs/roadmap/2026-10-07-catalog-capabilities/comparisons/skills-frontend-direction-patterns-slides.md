# Dirección de diseño, patrones React y presentaciones HTML — S107–S109

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Evaluadas S107 y S108 (cuerpos completos, **19.792 bytes/750 líneas**). S109 queda
**parcial**: cuerpo y dos scripts leídos (`export-pdf.sh`, `extract-pptx.py`), cuatro
recursos de estilo sin leer (`STYLE_PRESETS.md`, `html-template.md`,
`animation-patterns.md`, `viewport-base.css`); no cuenta como evaluada.
[frontend-direction-patterns-slides-reading-evidence.json](frontend-direction-patterns-slides-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S107 — Dirección de diseño de la interfaz

`4.360 bytes/93 líneas`. Fijar propósito, audiencia, tono, un detalle memorable y
restricciones antes de programar; reglas de implementación, antipatrones y checklist.

**Comparación.** `frontend-quality` cubre teclado, foco, formularios, estados y
rendimiento; no cubre dirección visual. En esta sesión hay disponible una skill
de diseño externa (`frontend-design`) y el bloque S075–S077 propuso ampliar
frontend-quality con sistema visual derivado y procedencia de tokens. S107 encaja
ahí: «usar componentes y tokens existentes antes de crear un sistema nuevo»,
«herramientas de uso diario: densas y escaneables», «sin dependencias por
adorno» y «el texto cabe en móvil y escritorio» son criterios verificables.
**Destino:** sección «dirección visual» de frontend-quality junto a la de S075–S077.

## S108 — Patrones de React y Next.js

`15.432 bytes/657 líneas`. Composición, componentes compuestos, render props,
hooks propios, Context+reducer, memoización, división de código, virtualización,
formularios, Error Boundary, animación y accesibilidad.

**Comparación.** stack-practices/react cubre estado y efectos;
frontend-quality, interacción. Correcciones:

| Ejemplo | Adaptación |
|---|---|
| `DataLoader` y `useQuery` caseros con `fetch` en `useEffect` | Sin cancelación: carreras al cambiar `url` y `setState` tras desmontar; preferir la librería de datos del proyecto o `AbortController` |
| `useQuery` deja `data` del key anterior al cambiar el key | Mostrar datos ajenos a la consulta actual; reiniciar o mostrar estado de carga |
| `.then(r => r.json())` sin comprobar `r.ok` | Un 500 se trata como datos |
| `markets!` en el render prop | Datos nulos sin error ni carga producen fallo en ejecución |
| Pestañas sin `role="tablist"`/`tab`/`tabpanel` ni flechas | Patrón WAI incompleto (ver S106) |
| `useMemo`/`useCallback`/`React.memo` como «PASS» genérico | Medir antes; frontend-quality ya prohíbe prescribirlos por regla |
| Error Boundary muestra `error.message` al usuario | Puede exponer detalles internos; mensaje propio |
| Animaciones con `framer-motion` sin `prefers-reduced-motion` | Respetar la preferencia (lo exige S106) |
| Formulario sin etiquetas, solo `placeholder` | Contradice frontend-quality |

**Destino.** Ejemplos corregidos de carga de datos con cancelación en
stack-practices/react; el resto ya está cubierto.

## S109 — Presentaciones HTML animadas (parcial)

`6.559 bytes/185 líneas` + scripts. Generar presentaciones de un solo fichero,
conversión desde PPTX y exportación a PDF por capturas.

**Lectura parcial.** El plugin tiene `to-pdf` (Markdown/HTML/Word a PDF con
Chromium y tema propio). Hallazgos en lo leído:

- `export-pdf.sh` instala Playwright y Chromium **en cada ejecución** (sin versión
  fijada), espera con `networkidle` y temporizadores fijos, y al final abre el PDF
  con el visor del sistema sin preguntar. El servidor local sí está bien confinado
  (solo loopback, rechaza rutas que escapan del directorio).
- El PDF sale de capturas: el texto no es seleccionable ni accesible.
- `extract-pptx.py` sobrescribe `assets/` y `extracted-slides.json` sin comprobar
  si existen, y usa el número mágico 13 para imágenes en vez de la constante de la librería.

Decisión provisional: no adoptar; la exportación a PDF ya tiene dueño (`to-pdf`).
Falta leer los recursos de estilo antes de cerrar la ficha.
