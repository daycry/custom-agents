<!--
Plantilla de la GUÍA DE INCORPORACIÓN al repositorio (categoría «guías how-to»): lo que necesita
quien acaba de entrar para orientarse. Sustituye {{...}}, borra estos comentarios y omite las
secciones que no apliquen (decláralo en el índice).
Reglas de esta plantilla:
· Cada comando sale de su FUENTE real (scripts del manifiesto, Makefile, CI, README) y se copia;
  NO se ejecuta para escribir la guía (ni instalaciones, ni migraciones, ni servidores).
· Cada versión dice su fuente: «declaración» (rango del manifiesto), «lockfile» (versión resuelta)
  u «observación» (salida ya existente, p. ej. un log de CI). Si no hay fuente: ⚠️ verificar.
· Variables de entorno: solo NOMBRES y para qué sirven. Nunca copies valores de `.env.example`
  ni de otra configuración: pueden ser privados.
· Adapta el recorrido al tipo de proyecto (servicio HTTP, CLI, consumidor de colas, librería,
  monorepo): no inventes un flujo HTTP si no lo hay.
-->
# Guía de incorporación — {{NOMBRE_PROYECTO}}

> {{QUE_ES_Y_PARA_QUIEN_EN_UNA_LINEA}}

## Por dónde entra la ejecución

| Entrada | Ruta | Qué arranca |
|---------|------|-------------|
| {{ENTRADA}} | `{{RUTA}}` | {{QUE_ARRANCA}} |

## Cómo está organizado

| Carpeta | Qué contiene |
|---------|--------------|
| `{{CARPETA}}` | {{CONTENIDO}} |

<!-- En un monorepo, una fila por paquete con su propio manifiesto; dice cuál afecta a qué. -->

## Recorrido de una ejecución

<!-- Un caso real de extremo a extremo con rutas: petición → controlador → servicio → datos, o
comando → parser → acción, o mensaje → consumidor → efecto. Diagrama ASCII si ayuda. -->
{{RECORRIDO_CON_RUTAS}}

## Stack y versiones

| Tecnología | Versión | Fuente de la versión | Propósito |
|------------|---------|----------------------|-----------|
| {{TECNOLOGIA}} | {{VERSION}} | {{declaración `package.json` · lockfile `package-lock.json` · observación}} | {{PROPOSITO}} |

## Comandos

| Tarea | Comando | Fuente | Efectos |
|-------|---------|--------|---------|
| {{instalar / arrancar / probar / lint / build}} | `{{COMANDO}}` | `{{FICHERO_ORIGEN}}` | {{solo lectura · escribe ficheros · migra la base de datos · usa red}} |

<!-- La columna Efectos avisa de lo que cambia algo fuera del código: migraciones, datos, red. -->

## Configuración y entorno

| Variable | Para qué sirve | Dónde se obtiene el valor |
|----------|----------------|---------------------------|
| `{{NOMBRE_VARIABLE}}` | {{USO}} | {{quién la da o dónde se genera}} |

## Convenciones

<!-- Solo las que se ven en el repo, con evidencia: estilo y linter configurado, dónde van los
tests y cómo se nombran, ramas y mensajes de commit si el historial o la CI los fijan. -->
- {{CONVENCION}} — evidencia: `{{RUTA_O_CONFIG}}`

## Zonas con riesgo

<!-- Ficheros grandes o muy cambiados, código sin tests, integraciones externas, migraciones. -->
- `{{RUTA}}` — {{POR_QUE}}

## Primeros pasos

1. {{PASO}}

## Pendiente de verificar

<!-- Lo que no se pudo confirmar con una fuente del repo. Si no hay nada, escribe «ninguno». -->
- {{PENDIENTE}} ⚠️ verificar

---

**Última actualización:** {{FECHA}}
