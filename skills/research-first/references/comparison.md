# Ficha de comparación

| Candidato y revisión | Función comprobada | Encaje con contrato | Dependencias y licencia | Riesgo o incógnita | Evidencia | Consulta y fecha |
|---|---|---|---|---|---|---|

«Consulta y fecha» registra cada pasada de búsqueda: canal, consulta exacta,
filtros, número de resultados y exclusiones con su motivo. Cada fuente lleva
dos fechas distintas: la suya (`as_of`, o `unknown` si no la declara; nunca la
hora actual) y la de recuperación.

Antes de crear una skill, agente o plugin propio, añade como candidatos las
piezas externas equivalentes. Una skill de terceros es código: lee su
`SKILL.md` y sus scripts, y anota comandos de shell, escrituras, accesos de
red, credenciales e instalaciones que pida. No edites el original instalado;
lo que adoptes se copia con procedencia y licencia. Ordenar por estrellas no
es un criterio de encaje.

Antes de decidir, comprueba datos de entrada/salida, Windows y rutas con espacios,
soporte Codex/Claude/OpenCode, operación local o externa, configuración del
consumidor, aislamiento entre proyectos, actualización/retirada y coste de
mantenimiento. Consulta solo los aspectos relevantes para la integración.

Separa código inspeccionado, pruebas ejecutadas y promesas del proveedor. Cuando
uses documentación cambiante, enlaza su fuente oficial y fecha de consulta.
Para reutilizar código o texto, conserva atribución y requisitos de licencia.
No presentes un benchmark de otro corpus como mejora medida de este plugin.

## Sesgos al leer fuentes

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «La fuente lo dice» | Un enlace no prueba que contenga la afirmación; un snippet o texto truncado no es el cuerpo. | Localizar y citar la frase que sostiene la afirmación concreta. |
| «Tres sitios lo confirman» | Copias sindicadas o del mismo comunicado repiten una sola fuente. | Contar como corroboración solo fuentes con origen independiente. |
| «Es antigua, busco algo reciente» | Una fuente primaria antigua puede ser la correcta; lo reciente puede ser una copia. | Juzgar por origen y vigencia del hecho, con su `as_of`. |
| «Lo encontré en un canal, basta» | Un canal único no sostiene una afirmación amplia ni la ausencia de alternativas. | Acotar la conclusión a ese canal o contrastar en otro. |
