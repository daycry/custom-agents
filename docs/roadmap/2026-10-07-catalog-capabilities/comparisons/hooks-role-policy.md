# Comparación de despacho y política previa

Lectura estática del corpus fijado ef648e01899ba3e8dc6371642deaaf64b4477775:
19 cuerpos completos y rangos concretos de un helper. Los hashes, rangos,
registros y dependencias están en
[role-hook-reading-evidence.json](role-hook-reading-evidence.json).
No se ejecuta código, tests, UI ni instaladores de origen. Esta lectura no
cierra T-06 ni demuestra eficacia o integración de sus políticas.

| IDs y rangos | Diferencia concreta | Decisión propia |
|---|---|---|
| R-a48aec12c9dd:1–91; R-fe000d2a37ea:1–18 | Registro previo global en un runtime; el segundo adaptador registra solo inicio de sesión | No acredita paridad ni selección por rol. Conectar nuestra política única a metadata nativa de cada runtime, con IDs exactos y límites verificados |
| R-77bd5a7d0997:1–42; R-efb8d4bfbbf4:22–52,123–173 | Cadena ordenada de políticas y perfiles de activación | Mantener configuración por regla y decisiones del evaluador existente; no duplicar servicios ni ampliar deny global al resto de agentes |
| R-424b793579f1:134–253,291–744; R-6c19f2bf0c4c:1–406 | Detección de bypass de verificación Git, overrides de hooksPath, configuración literal por entorno y wrappers | Implementado en la regla compartida `git` para IDs propios exactos de implementer y architect. Reconoce flags efectivos de commit, overrides explícitos y wrappers literales; preserva mensajes, rutas, `--verify` posterior y opt-out. Límites y entrega del bloque 12 en [design.md](../design.md) |
| R-b1af87280da8:23–229 | Protección de configuración de calidad e ignore existentes; creación inicial permitida | Candidato opt-in sujeto al contrato de calidad del proyecto y excepciones autorizadas. No bloquear cambios legítimos por defecto. El lector solo toma path superior aunque el matcher incluye MultiEdit; nuestra integración debe recorrer todos los targets |
| R-391f040a5518:1513–1529,1802–1809,1863–1912 | Marca paths antes del primer deny, permite retry sin validar hechos y omite comprobación de archivos de todos los subagentes | Descartar esas semánticas: un retry no concede autorización y la política por rol debe persistir dentro del subagente |
| R-391f040a5518:970–1122,1240–1309,1914–1954 | Clasificación ampliada de Git, shell, SQL y PowerShell | Evaluar cobertura adicional después de conectar identidad. El helper PowerShell solo se ha leído parcialmente; no se promete análisis completo ni se copia el parser |
| R-61e1f84b6de2:28–57,88–167,344–517 | Heurísticas staged y linters disponibles; amend omite comprobaciones | No sustituir nuestros gates de evidencia por heurísticas de commit. Staged y worktree son snapshots distintos |
| R-564ee7b92148:7–62; R-1f1eff6fddd0:94–115; R-e609074b9619:27–71,246–299 | Input acotado con indicación de truncado, control de errores y salida sin echo del evento bruto | Conservar contrato nativo y redacción. La integración debe tratar identidad reconocida/input incompleto sin bloquear indiscriminadamente agentes ajenos |

El diseño de identidad está en [design.md](../design.md), bloque 3. Las
[pruebas nativas propias](../native-role-contract-evidence.json) prueban el
mecanismo del host; no son pruebas de ejecución de estas piezas de origen.
La fila de verificación Git describe la implementación propia del bloque 12.
Las demás decisiones conservan sus destinos y requisitos pendientes. No
se dan de alta skills, agentes, comandos ni paquetes técnicos en este bloque.

La protección de verificación Git reutiliza el dispatcher y el evaluador
existentes; no añade una política global para agentes ajenos. La gramática
literal no expande variables ni analiza scripts, aliases o configuración
Git externa. El dispatcher reconoce la tool PowerShell; sus asignaciones y
scripts quedan fuera de esa gramática. Conserva el límite de recursión de
shell y el opt-out por regla.
La protección de configuración de calidad queda como candidato opcional hasta
definir alcance y excepciones por proyecto. La política de degradación se
preserva; cambiar el tratamiento de input incompleto requiere una decisión
y tests propios. La revisión y aceptación de este bloque se registran en
el ledger, sin extrapolar las pruebas anteriores del host a esta regla nueva.

Lectura pendiente: R-e6c33a7553a7, líneas 251–1883; solo 1–250 y 1884–2096
se han revisado. Quedan 24 cuerpos inmediatos sin leer y 16 descendientes
identificados por metadata del catálogo, sin hash local comprobado. Los
registros diferencian esos límites de los 19 cuerpos completos. La tarea de
hooks, tools y workflows y su comparación global continúan abiertas.
