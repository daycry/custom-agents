# Seguridad de contratos y cierre verificable — S073–S074

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Los dos cuerpos completos suman **10.530 bytes y 293 líneas**. S073 no entrega
recursos locales; S074 entrega un hook, leído completo: **7.826 bytes y 220
líneas**. [security-delivery-reading-evidence.json](security-delivery-reading-evidence.json)
registra ocho fuentes, 19 contrapartes propias y 12 contrastes oficiales; separa
un HTTP 404 y dos errores del lector web de las lecturas válidas.
Los nombres y rutas originales quedan en el mapa privado.
El ledger canónico sigue siendo [tasks.md](../tasks.md), T-03.

Son **propuestas para T-08**, sin código de producción integrado. Se leyeron
cuerpos, recurso, consumidores, manifiestos y contratos actuales. No se ejecutaron
código o tests del corpus, instalaciones, compiladores Solidity, analizadores,
fuzzers, modelos ni hooks de cierre. Los casos siguientes son criterios estáticos
preparados; su ejecución nativa corresponde a T-09/T-14.

## S073 — Seguridad de contratos Solidity y pools

**Identidad y alcance.** SHA-256
`06f662a81b1faebb9930118302d88d649dbc5bcbf7dfe87c3780ddc72f2d6516`,
5.390 bytes, 167 líneas, cuerpo completo, cero recursos locales. Los consumidores
por nombre encontrados son empaquetado, módulo de seguridad y exclusiones de
otro perfil de runtime; no se encontró un agente/comando canónico que lo invoque.
Eso no acredita uso cero ni obliga a excluir la especialidad de nuestro catálogo.

**Contrato y valor único.** Lista controles de entrypoints que mantienen activos:
withdraw/deposit, mint/burn y swaps. Conserva CEI y reentrancia, transferencias
ERC-20, contabilidad de shares y donaciones, oráculos, límites del swap, precisión
y privilegios. La salida es un análisis con invariantes, hallazgos por ubicación
y pruebas reproducibles del proyecto consumidor. No implica operar una cartera,
firmar, desplegar contratos o ejecutar transacciones en una red pública.

**Comparación propia.** La lectura de `cybersecurity` se limita al mapa 1–90 y a
`references/recon-and-scope.md` completo: aporta scope, fronteras, secretos,
dependencias, lógica y formato de auditoría; no desarrolla shares, TWAP o AMM.
Su enumeración de lenguajes no incluye `.sol` y el directorio actual de patrones
no contiene una referencia Solidity. Es un gap de ese recorrido, no prueba de
incapacidad de todo el auditor. `nemesis` 1–95 conserva el informe y sus límites
de auditoría activa. `unit-tests` y la revisión adversarial conservan métodos
transversales; no se declara soporte nativo de cobertura Solidity por esa relación.

**Correcciones necesarias.**

| Sección leída | Delta que conserva la intención y evita una garantía falsa |
|---|---|
| Withdraw con CEI, SafeERC20 y guard | El fragmento omite contexto de contrato, herencia e imports necesarios; identificar llamadas externas y estado observable entre funciones. Importar el guard no aplica el modificador a todas las entradas |
| Depósito con `_totalAssets` interno y `received` | Conservar medición recibida; definir shares de cada usuario, mint/burn, retiradas, fees, rebases y sincronización. El fragmento solo aumenta totales y no demuestra atribuir propiedad al depositante |
| División de shares | Probar supply existente con assets cero, depósito que redondea a cero y producto que desborda. Contabilidad interna reduce una vía de donación, pero no demuestra por sí sola seguridad o cumplimiento ERC-4626 |
| Ventana TWAP fija y conversión de tick | Corregir redondeo de ticks negativos con resto; validar historial disponible, ventana, liquidez, pool y denominación. Una ventana de 30 minutos no acredita resistencia universal a manipulación |
| Swap valida `_calculateOut` antes de ejecutar | Verificar resultado realmente liquidado, tokens y ruta, además de plazo y límites del usuario. Una cotización interna no prueba qué recibe el destinatario |
| FullMath y controles administrativos | Fijar compilador, librerías y target; constructor inicial de ownership, aceptación, límites de fee y privilegios. No mezclar APIs de versiones incompatibles |
| Pause y herramientas obligatorios | Definir recuperación y autoridad según protocolo; no añadir un administrador/pausa a un diseño que decidió ser inmutable. Reportar cobertura, exclusiones y fallos de herramientas, sin convertir un resultado limpio en prueba total |

**Contraste por versión.** OpenZeppelin 5.x documenta `initialOwner` y
transferencia aceptada; el ejemplo administrativo carece de ese constructor.
El guard leído en **5.4.0** requiere Solidity `^0.8.20`; las librerías V3 leídas
declaran `<0.8.0`. No se pueden asumir compilables juntas bajo un único
compilador. El proyecto debe elegir una implementación compatible y verificarla.
[Ownership](https://docs.openzeppelin.com/contracts/5.x/access-control),
[guard 5.4.0](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.4.0/contracts/utils/ReentrancyGuard.sol),
[FullMath V3](https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/FullMath.sol).

La implementación oficial de `consult` resta uno al promedio negativo con resto;
la división del cuerpo no lo hace. También proporciona historial más antiguo,
liquidez y cotización orientada por tokens. La adopción necesita pruebas con
decimales y extremos; aquí no se ejecutó ningún contrato.
[OracleLibrary](https://github.com/Uniswap/v3-periphery/blob/main/contracts/libraries/OracleLibrary.sol).

OpenZeppelin describe pérdidas por redondeo, shares virtuales/offset y coherencia
de previews, fees y eventos. Es material para elegir y probar una defensa adecuada
al vault; no valida el fragmento del cuerpo ni exige que todo pool sea ERC-4626.
[Guía ERC-4626](https://docs.openzeppelin.com/contracts/5.x/erc4626).

Slither requiere hoy Python 3.10+ y compilación/dependencias del proyecto;
`--exclude-dependencies` filtra resultados exclusivamente de dependencias, no
acredita haberlas auditado. Echidna documenta `echidna ... --contract ... --config
...`; detectar versión/binario y propiedades antes de adoptar el comando antiguo.
La fuente actual de Forge declara `fuzz_runs` y su override de configuración.
Las dos páginas que el lector web no abrió y la ruta de código HTTP 404 no se
cuentan como documentos leídos; la fuente vigente de CLI sí se leyó. Número de
runs, timeout y seed pertenecen al presupuesto y contrato de pruebas del proyecto.
[Slither](https://github.com/crytic/slither),
[filtro](https://github.com/crytic/slither/blob/master/slither/__main__.py),
[Echidna](https://github.com/crytic/echidna),
[Forge](https://github.com/foundry-rs/foundry/blob/master/crates/forge/src/cmd/test/mod.rs).

**Decisión y destino.** Conservar como especialidad opcional
`skills/solidity-security/SKILL.md`, con referencias `token-accounting.md`,
`oracle-swap-controls.md` y `audit-toolchain.md`. Extender recon y routing propios
para encontrar Solidity/toolchain; compartir el método de auditoría, TDD y gates,
sin otro agente permanente ni dependencias globales. `nemesis` conserva el
informe; implementer modifica el contrato del consumidor y qa verifica los casos.
Los runners y parsers realmente soportados se decidirán en T-12/T-14.

**Activación preparada.** Literal «Audita este pool Solidity»; paráfrasis
«Comprueba que los depósitos y retiros no permitan robar shares». Negativo
«Revisa permisos de mi API REST» → auditoría general. «Mi hook bloquea el cierre»
→ S074/contratos de runtime, sin cargar librerías de contratos financieros.

**Casos pendientes.** Callback reentrante y otra entrada sin guard; ERC-20 que
devuelve false/no data o cobra fee; supply cero, cero shares y assets cero;
donación y retirada después del depósito; enteros extremos; tick negativo con
resto; historial insuficiente; token order/decimales; diferencia entre quote y
transferencia final; ownership sin inicializar o sin aceptar; fee fuera de rango;
discovery vacío, compilación fallida y campaña abortada. Evidencia por versión,
invariante y seed, sin firmas ni redes públicas para este gate.

**Coste e impacto.** Cuerpo corto y referencias bajo demanda; tokens/latencia null.
Instalaciones y campañas dependen de disponibilidad y alcance autorizado del
consumidor. T-08/T-10 contenidos; T-11 routing/roles; T-12 herramientas;
T-14 pruebas y T-15 docs/exports. No se incorpora un paquete técnico ajeno al corpus.

## S074 — Evidencia mecánica antes de declarar entrega

**Identidad y recursos.** SHA-256
`147a971c26b7bf4f9fbc3e1f624ec7c888eb8d74911d8ffbbe0418d9aaaa9767`,
5.140 bytes, 126 líneas. Hook **R-5887f6d965a7**, SHA-256
`76aa0fe8c136be8a760ce74e614463ffb05fb16f1e165c5938daa86f516b87ef`,
7.826 bytes/220 líneas, leído completo, no ejecutado. Los manifiestos lo incluyen;
S119, leído solo en 113–128, lo relaciona con registrar aprendizaje. Sus otras
referencias de calidad y seguridad requieren la comparación completa posterior;
no se cuentan aquí como skills evaluadas.

**Contrato y valor.** Busca impedir una entrega prematura mediante checks
deterministas: capacidad del disco, captura de aprendizaje y señales textuales de
atajos. Se conserva la intención de obtener estado observable, razones y remedios
concretos. Regex y mtimes son señales, no pruebas de corrección, aprendizaje o
aprobación del conocimiento. El código no corre build, typecheck, lint o tests;
la afirmación del cuerpo sobre comprobaciones incorporadas no demuestra que se
hayan ejecutado para el cambio del consumidor.

**Comparación propia.** `qa-gate.py` ya exige evidencia Playwright no vacía y
clasifica fallos, flaky justificados, interrumpidos y errores del runner. Ese
parser no es un gate universal de todos los stacks. `dev-cycle` 90–131/190–205
conserva revisión, qa, ledger y retro de cierre con correcciones acotadas.
La memoria propia separa journal episódico de conocimiento curado, con umbral
de registro y estado `propuesta`; ausencia de una entrada nueva puede ser válida.
`doctor.py` 2266–2291/2394–2451 informa estados de memoria y cola, no decide
calidad por fecha. Estos dueños evitan un segundo gate que fuerce escribir doctrina.

**Diferencias entre cuerpo y recurso.**

| Evidencia estática | Consecuencia para la adaptación |
|---|---|
| El cuerpo promete que basta un archivo actualizado; el recurso bloquea con ≥3 stale o growth stale en tarea compleja | Growth actualizado y cuatro archivos stale bloquea; actualizar solo output-index también bloquea. Corregir contrato y ejemplos antes de anunciar comportamiento |
| El texto liga disco crítico a complejidad; `check_disk` se ejecuta antes de clasificar la tarea | Puede bloquear una petición simple; mide volumen de home, que puede diferir del workspace. Presupuesto de escritura y volumen relevante deben decidir la severidad |
| Umbrales publicados 50/15; código añade 30 y mide GiB enteros | Unidades, configuración y acciones deben coincidir. No imponer 15 GiB libres como condición universal para finalizar cualquier tarea |
| `count_edits` es regex en la transcripción completa | Citas de JSON o invocaciones fallidas cuentan; acumula tareas previas y omite tools de otros runtimes. Complejidad no equivale a tres coincidencias textuales |
| stdin, archivo de transcripción y recorrido del directorio sin presupuesto | La cola del hook puede crecer sin cota; fijar bytes/eventos/deadline, errores UTF-8 y permisos, scope de rutas y cancelación. No leer una sesión entera para cada Stop |
| Ruta de memoria derivada por sustituciones de cwd, con home fijo | No acredita el loader nativo, configuraciones personalizadas o identidad de proyecto. Usar roots/procedencia propios; los logs no deben revelar contexto privado innecesario |
| Compara día calendario del mtime; un touch pasa sin cambiar contenido | Medianoche, zona horaria o una sesión reanudada alteran el resultado. Una fecha no identifica evidencia de la tarea ni obliga a crear aprendizaje nuevo |
| Sin memoria avisa y permite, pero dibuja todos los indicadores como correctos | Mostrar «no verificable/no configurado», distinto de un check aprobado |
| No consulta `stop_hook_active`; el remedio exige actualizar archivos | Puede reiterar una condición que no tiene solución útil. Preservar retorno acotado y autoridad de cierre, sin fabricar entradas para salir del bucle |
| Instalación copia un basename que no está junto al cuerpo y usa timeout 5000 | Resolver el recurso entregado y binario por plataforma; los timeouts de configuración leídos están en segundos. No convertir ese número en un supuesto timeout de 5 s |

**Contratos de runtime.** Claude documenta Stop como feedback/continuación y
`stop_hook_active` para evitar repetición; su cap también depende de llamadas a
tools. SessionEnd no decide el cierre y descarta campos JSON. Tiene presupuesto
por defecto de 1,5 s, y un timeout de hook de plugin no lo eleva. El launcher propio
da 2,2 s a la captura y nuestro manifiesto declara 5 s: ambas declaraciones no
prueban completar dentro del presupuesto efectivo. T-09 debe resolver ese margen
y comprobar cancelación/captura durable; aquí no se cambió configuración del usuario.
[Claude hooks](https://code.claude.com/docs/en/hooks).

Codex documenta Stop con JSON stdout al salir 0, o exit 2 y razón stderr para
continuar; SessionEnd es advisory/síncrono con límite de hasta 3 s. El manifiesto
propio de Codex ya declara 3 s. No trasladar un exit code de Stop a teardown como
si impidiera terminar. Tampoco tratar un warning stderr con exit 0 como contexto
entregado al modelo sin verificar el contrato del evento.
[Codex hooks](https://learn.chatgpt.com/docs/hooks).

OpenCode V2 usa plugins y carga propia; no se instala el JSON Claude por analogía.
El [contraste nativo previo](../contracts.md#prueba-nativa-opencode-2012) acredita
fallo del adaptador V1 y carga/registro del control positivo V2, con dispatch aún
pendiente. La página actual de plugins acredita discovery/configuración, no un
callback Stop equivalente. Preservar política de cierre en el ciclo compartido y
usar eventos reales que T-09 pruebe.
[Plugins V2](https://opencode.ai/v2/docs/plugins/).

**Decisión y destinos.** Consolidar evidencia de entrega en `delivery-practices`
con `references/delivery-readiness.md` y el ciclo/qa propietarios. Retirar de la
propuesta el bloqueo universal por mtime y las cinco bibliotecas paralelas;
conservar avisos de captura solo cuando exista un requisito verificable de la
tarea. Los candidatos van a journal/curación conforme a su estado, no a doctrina
por touch. La tabla compartida de racionalizaciones mantiene el razonamiento;
una regex opcional únicamente puede avisar con contexto y posibles falsos positivos.

Capacidad de disco es un diagnóstico contextual de doctor y una precondición
de una operación de escritura declarada, con volumen/unidades/budget visibles.
Hooks informativos actuales conservan su contrato: el launcher termina sin
propagar el exit code del hijo como bloqueo. Añadir un futuro hook bloqueante
exige un transporte explícito y probado; no reciclar ese launcher y anunciar
enforcement. Captura durable/outbox permanece en su dueño y bajo los deadlines
efectivos. T-08 decide checks/estados, T-09 dispatch, T-12 diagnóstico, T-13 panel
y T-14 su ejecución. No crear otro motor de workflow ni nueva memoria por sesión.

**Activación preparada.** Literal «Impide cerrar sin evidencia de los checks
acordados»; paráfrasis «Distingue entrega lista, incompleta y no verificable».
Negativo «Audita slippage de un pool» → S073; «Guarda preferencias de estilo»
→ configuración/perfil nativo, sin forzar un log de aprendizaje o cierre de tarea.

**Casos pendientes.** Solo growth fresco; solo output-index fresco; tres stale;
tarea simple con poco espacio; proyecto en otro volumen; transcripción ausente,
UTF-8 inválido o demasiado grande; JSON citado y tool fallida; cambio de día;
otro proyecto, root personalizado, symlink y ruta fuera de scope; Stop ya activo;
hooks repetidos tras llamar una tool; hijo exit 2 bajo launcher informativo;
teardown cancelado antes/después de staging; evidencia vacía, stale o de otra
tarea; instalación parcial y cola pendiente. Confirmar outputs y efecto real por
runtime, sin confundir fixture, configuración o aviso con bloqueo efectivo.

**Carga y límites.** Un recurso Python stdlib no necesita modelo, pero sus
lecturas sin cota pueden exceder el evento. Tokens/latencia null: ni bytes del
cuerpo ni determinismo acreditan coste de contexto o durabilidad. T-10/T-11/T-15
actualizarán contenido, referencias, consumidores, exports y docs; T-07 conserva
la comparación de memoria y la fase posterior sus benchmarks. Cero integración
de producción en este bloque.
