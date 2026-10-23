# Dirección creativa de vídeo, paquetes de estilo y VideoDB — S269–S272, S286–S287

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos: **85.023 bytes/1.784 líneas**. Recursos leídos completos:
la taxonomía de S269, los doce ficheros Fusion de S286 y los once de S287
(**137.679 bytes/3.900 líneas** en total). Los recursos de S270 (80 ficheros,
754.247 bytes) y S271 (14 ficheros, 174.981 bytes) son código, pruebas y fixtures:
de S270 se leyeron completos `SOURCE.md` y `workflows/README.md`, las primeras
80 líneas de `scripts/verify.py` y búsquedas puntuales en `taste/frames.py` y
`falapi.py`; se comprobó que tres pares de scripts compartidos entre S270 y S271
son idénticos byte a byte. El resto consta como **no leído** en
[taste-video-reading-evidence.json](taste-video-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## Decisión común

Las seis piezas pertenecen a la producción de vídeo (dirección de arte, gradación,
montaje, generación con proveedores de pago, indexado en un servicio externo).
Ningún rol del ciclo de desarrollo las consume. Coherente con S100 (generación
con fal.ai, [skills-errors-evals-providers.md](skills-errors-evals-providers.md)),
con Remotion (S236, [skills-nonconformance-remotion-returns.md](skills-nonconformance-remotion-returns.md))
y con la familia Itô de S141–S144: **Fuera del bundle**; extensión o persona de
proyecto si un consumidor produce vídeo. Se extraen solo criterios generales, y
casi todos ya tienen dueño.

## S269 — Dirección creativa («taste»)

`15.406 bytes/264 líneas` más la taxonomía de géneros (4.869 bytes). Vocabulario
de géneros visuales, paleta, gramática de montaje a ritmo de compás, presets de
prompt y un plan de planos para **un videoclip concreto** (138 BPM, si menor).

**Comparación.** Sin contraparte. La pieza no es reutilizable tal cual: mezcla el
método con los datos de un proyecto, y la propia S272 advierte que esa paleta
«no debe imponerse al brief actual». Remite a skills que no existen en el
plugin (composición con Remotion, `motion-*`, distribución). Contradicción
interna de la familia: sus recetas cortan con `-c copy`, que S270 prohíbe porque
el corte en copia de flujo solo cae en fotogramas clave.
**Fuera del bundle.**

## S270 y S271 — Destilar referencias en un paquete de estilo y aplicarlo

`19.794 bytes/352 líneas` y `9.133 bytes/200 líneas`. S271 mide vídeos de
referencia (gradación como LUT 3D por zonas de luminancia, distribución de
duraciones de plano, fotogramas y planchas de superposición); S270 genera tomas
contra ese paquete, gradúa, monta, verifica numéricamente y exporta línea de
tiempo editable (FCPXML/EDL), con llamadas de pago bajo `TASTE_FORGE_ALLOW_LIVE=1`.

**Comparación.** Dominio ajeno. Son, sin embargo, de las piezas mejor razonadas
del corpus sobre **medir en vez de describir**. Sus lecciones coinciden con
doctrina ya fijada:

| Idea de la pieza | Dónde vive ya en el plugin |
|---|---|
| Un buen error medio (MAE) convivió con un fotograma roto; verificar la forma de la distribución, no solo momentos | `outcome-evals`: «la media oculta fallos» en su tabla de racionalización |
| Un cero medido es dato; distinguirlo de un campo ausente | `outcome-evals/references/protocol.md`: métricas ausentes `null`, nunca inventadas |
| Un tiempo de espera ambiguo del proveedor no se reintenta como trabajo nuevo de pago | `backend-practices/references/contracts-data.md`, fila «Timeout después de aceptar la operación remota» |
| Prohibir palabras ambiguas «en código, no solo en el prompt» (el prompt falló una vez de cada tres) | Veredictos en scripts deterministas, no en prosa |
| Render terminado, proyecto guardado y aprobación creativa son estados distintos | Misma separación que `qa` verde frente a cierre y que los recibos de `/work-resume` |

Aporta una idea que el plugin no formula: **una descripción generada a partir de
las medidas ya no es una comprobación independiente de ellas** (S271, «Grounding
the VLM»). **Destino:** una línea en `outcome-evals/references/protocol.md` —un
juez que recibe la medida como contexto no la valida; el contraste necesita
fuente separada—. El resto, **fuera del bundle**.

Defectos y riesgos en lo leído: la tabla de endpoints y precios de un proveedor
se declara a sí misma propensa a quedar obsoleta; el entero de composición «5, no
22» de DaVinci Resolve depende de la versión del host; `workflows/README.md`
reconoce que las entradas compiladas pueden contener URLs privadas de medios.

## S272 — Motor offline y contrato de evidencia

`14.932 bytes/256 líneas`. Entrevista de gusto, validación de paquetes,
planificación de corte con semilla, exportación EDL/FCPXML y auditoría de
procedencia, todo local; la generación con proveedor «falla cerrada».

**Comparación.** El contrato de recibos (cada artefacto ligado por ruta, tamaño y
SHA-256; `provider_calls` como entero exacto, rechazando el booleano `false`;
campo ausente = rechazo, no valor por defecto; sin enlaces simbólicos ni ficheros
especiales) coincide con el que ya aplican `knowledge-curation.py`,
`knowledge-schema.py` (booleanos estrictos) y `local-read.py`. No aporta regla
nueva. **Fuera del bundle.**

## S286 — Edición de vídeo asistida

`11.754 bytes/337 líneas` más dos paquetes de preajustes Fusion con instalador
Lua idempotente (18.662 bytes). Capas: captura, organización por transcripción,
cortes con FFmpeg, composición con Remotion, recursos generados y pulido manual.

**Comparación.** Sin contraparte. Lo valioso coincide con lo ya fijado:
guardar y verificar un punto de control antes y después de tocar un proyecto
vivo, porque «una lectura por API prueba el estado en memoria, no que se
guardara»; no activar telemetría ni subida de datos como efecto lateral. El
instalador Lua es un buen ejemplo de idempotencia (rechaza bytes distintos ya
instalados y relee lo escrito), pero está fijado a rutas de macOS.

Defectos: los cortes por marca de tiempo usan `-c copy` (mismo problema que
S269); el ejemplo de ElevenLabs escribe `resp.content` sin comprobar el estado,
de modo que un error JSON acaba guardado como `.mp3`; llama a
`generate_voice(text=…, voice="alloy")` mientras la referencia de S287 documenta
el parámetro `voice_name`. **Fuera del bundle.**

## S287 — VideoDB

`14.004 bytes/375 líneas` más diez referencias y un oyente WebSocket
(114.148 bytes). SDK de un servicio externo: subir, indexar voz y escenas,
buscar, línea de tiempo, retransmisión, captura de escritorio y alertas.

**Comparación.** Producto de un proveedor; **Fuera del bundle**. Riesgos y
contradicciones concretas:

- Ordena no usar FFmpeg «cuando VideoDB soporte la operación», lo que convierte
  en predeterminado subir medios locales a un tercero. Choca con la regla ya
  fijada en S100: subir ficheros a un servicio externo requiere autorización
  explícita.
- La captura de escritorio graba pantalla, micrófono y audio del sistema con
  descripciones por IA y alertas («avisa cuando aparezca un campo de
  contraseña»). Es vigilancia de la sesión del usuario; fuera de cualquier rol.
- `reference/capture.md` sitúa eventos y PID en `/tmp/videodb_*`, mientras
  `SKILL.md`, `capture-reference.md` y `ws_listener.py` usan
  `~/.local/state/videodb` con permisos 0700. Dos ubicaciones para el mismo
  estado, una de ellas compartida.
- Para recuperar un índice de escenas existente propone extraer el ID del texto
  del mensaje de error con una expresión regular: contrato frágil.

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S269 | Dirección de arte ligada a un proyecto | Fuera del bundle |
| S270–S271 | Dominio ajeno; medición ejemplar | Línea de independencia en `outcome-evals/references/protocol.md` |
| S272 | Contrato ya cubierto por los validadores propios | Fuera del bundle |
| S286 | Flujo de edición; defectos en ejemplos | Fuera del bundle |
| S287 | SDK de proveedor; subida por defecto y vigilancia | Fuera del bundle |

Validación pendiente: la línea propuesta para `outcome-evals` necesita un caso
del corpus donde el juez reciba la medida, para comprobar que se marca como no
independiente.
