# Comparación medida de recuperación local y contexto de código

El pase del 12 de octubre de 2026 ejecutó ambos lectores sobre las mismas doce
fuentes sintéticas y catorce preguntas, tres veces por pregunta. La comparación
usa el candidato con manifiesto `5694fd77e1f0b6ead217cc765f541614ac96e26440fd91aed7dc83e00c34ed33`
y el motor de referencia fijado a `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Se leyeron completos sus tres módulos antes de ejecutarlos en almacenes propios.
No se instalaron componentes en el plugin ni se enviaron inferencias.

| Medida sobre 36 consultas con fuentes esperadas | Lector local | Referencia |
|---|---:|---:|
| Consultas con todas sus fuentes entre los cinco primeros resultados | 36 | 33 |
| Consultas con todas sus fuentes en el primer resultado | 24 | 9 |
| Apariciones esperadas recuperadas entre los cinco primeros | 42/42 | 39/42 |
| Fuentes de otro proyecto | 0 | 0 |

La referencia omite una de las dos fuentes de Q07 entre los cinco primeros en
las tres repeticiones. Las dos preguntas con varias fuentes no pueden satisfacer
la métrica «todas en el primer resultado»; esa métrica no mide precisión global.
Ambos motores devolvieron candidatos para las dos preguntas sin fuente esperada:
no se ha probado abstención de respuestas. El lector local informó 21 resultados
parciales y 21 completos. No se ejecutó generación de respuestas, análisis de
instrucciones adversarias por un modelo ni evaluación humana.

El lector local conserva ID, versión y hash de los bytes de origen en todos los
resultados. La referencia tiene ID y confianza `unreviewed`, sin versión nativa;
el mapeo externo del ensayo no añade esas garantías a su formato. La ubicación
`approved` de la fixture tampoco acredita una aprobación real del curador.
Los dos proyectos estuvieron en raíces físicas separadas. No se acreditan aquí
aislamiento de un almacén compartido ni permisos entre usuarios reales.

No se compara velocidad: las medidas incluyen procesos nuevos con envolturas,
intérpretes y cargas diferentes. Los recibos originales conservan los tiempos.
Este corpus pequeño favorece comprobar hechos y procedencia, no estima utilidad
semántica en documentación extensa ni demuestra superioridad general.

El lector de contexto de código completó doce consultas sobre el artefacto AST
sintético existente: tres símbolos y uno ausente, tres repeticiones. Encontró
las relaciones de `accept`, `append` y las dos funciones llamadas `deadline`;
el símbolo ausente quedó como `no-match-in-artifact`. Todas las ubicaciones de
las citas existen en las fuentes de la fixture. No regeneró el grafo y conservó
`freshness: unverified`, `coverage: unknown`, `directed: false` y
`knowledge_status: unapproved-context`. Estas relaciones son pistas de descubrimiento;
no certifican vigencia, cobertura completa ni una dependencia dirigida actual.

La decisión se mantiene: memoria Markdown local siempre disponible, Kwipu opcional
para documentación y Graphify opcional para estructura de código. Graphiti sigue
opt-in fuera de la combinación recomendada por defecto. Este pase no repite las
pruebas reales anteriores de esos servicios y no convierte su disponibilidad en
ventaja de recuperación demostrada. No justifica sustituir el origen canónico.

Los hashes de los recibos privados y las métricas están en
[la evidencia de este pase](memory-comparison115-evidence.json). El ensayo no
cierra workflows nativos, interacción humana del panel, revisión independiente
ni aceptación global de la implementación.
