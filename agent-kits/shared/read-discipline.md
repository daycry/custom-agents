<!--
  FRAGMENTO COMPARTIDO: disciplina de lectura del recon.
  Lo referencian los agentes que EXPLORAN un repo (documenter, nemesis, evaluator, qa).
  Objetivo: leer lo justo — el recon es lo más caro en tokens del plugin.
-->

# Disciplina de lectura (recon)

Cuando explores un repositorio o proyecto para fundamentar tu trabajo, **lee lo justo**. El recon es la fase más cara en tokens; estas reglas la abaratan sin perder rigor.

1. **`grep`/`glob` antes de `Read`.** Localiza primero (qué ficheros, qué símbolos, dónde está lo relevante) y solo entonces abre. No abras un fichero "por si acaso".
2. **`Read` con `limit`/`offset`.** Cuando ya sabes qué parte necesitas, lee ese fragmento, no el fichero entero. Un fichero grande se lee por tramos guiados por el `grep`, no de una vez.
3. **Ignora lo que no aporta señal:** `node_modules/`, `vendor/`, `.git/`, `dist/`, `build/`, `coverage/`, lockfiles (`package-lock.json`, `composer.lock`, `poetry.lock`, `yarn.lock`), minificados (`*.min.js`, `*.min.css`), binarios, imágenes, `*.map`, y datos generados. Restríngelo con globs en `grep`/`glob`.
4. **Muestra representativa, no exhaustiva.** Para entender un patrón (cómo son los controladores, los tests, los componentes) basta leer 1-3 ejemplos, no todos. Declara que has muestreado en vez de leerlo todo.
5. **Excepción explícita:** si el fichero **es el objeto de trabajo** (el documento a documentar, el fichero a auditar línea a línea, el artefacto a reescribir), léelo completo — la regla es "no leas de más", no "no leas".

Si delegas exploración a un subagente, pásale estas mismas reglas: que devuelva hallazgos (rutas + líneas + resumen), no volcados de ficheros.
