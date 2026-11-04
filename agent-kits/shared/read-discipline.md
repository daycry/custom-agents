# Disciplina de lectura

1. Localiza ficheros y símbolos con `grep`/`glob` antes de `Read`.
2. Lee fragmentos con `limit`/`offset`; divide fuentes grandes.
3. Excluye dependencias, `.git/`, generados, lockfiles, minificados, binarios,
   imágenes y mapas; restringe los globs.
4. Para patrones, muestra 1-3 ejemplos y declara el muestreo.
5. Si el archivo es el objeto del trabajo, léelo completo; la exclusión no aplica.

Reutiliza hallazgos vigentes de spec/evaluación/diseño; conserva requisitos,
código necesario y juicio independiente. Lee una vez por contexto vigente;
si cambia o se pierde, vuelve a la fuente. Al delegar, transmite estas reglas
y pide rutas, líneas y hallazgos, sin volcados.
Adapta solo secciones opcionales con motivo; conserva campos, estados y enlaces.
Si no cabe, divide sin recortar criterios, restricciones, evidencia ni errores.

Para fuentes extensas compartidas entre fases, lee
`agent-kits/shared/references/source-reuse.md` antes de usar
`agent-kits/shared/source-snapshot.py`. Evita ese
coste para lecturas breves. Un recibo no sustituye requisitos, aprobación o tests.
