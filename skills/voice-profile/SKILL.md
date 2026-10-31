---
name: voice-profile
description: >
  Extrae un perfil de voz a partir de muestras autorizadas, con procedencia,
  rasgos observables y diferencias por canal. Úsala cuando el usuario diga
  "extrae mi estilo", "crea mi perfil de voz" o "analiza cómo escribo".
---

# Perfil de voz

Convierte ejemplos del autor en criterios reutilizables para redactar y revisar.
No decide la estrategia de marca ni escribe una campaña completa.

1. Delimita autor, muestras disponibles, público y uso previsto. Lee las muestras
   aportadas; buscar otras fuentes requiere que esté dentro del encargo.
2. Para extraer o actualizar el perfil, lee [el esquema](references/profile-schema.md).
   Conserva ejemplos y contraejemplos con su origen; separa observación e hipótesis.
3. Contrasta los rasgos entre muestras y canales. Devuelve las discrepancias que
   cambien la redacción, sin promediar registros incompatibles.
4. Ofrece el perfil en la respuesta. Si se ha pedido guardarlo, usa el destino
   autorizado y evita sobrescribir cambios de otro autor. No crea memoria personal
   ni incorpora muestras privadas al repositorio por defecto.

`content-production` y `relationship-planning` pueden consumir el perfil confirmado;
no necesitan volver a extraerlo. Sin muestras, acuerda un tono provisional y
declara esa limitación. La invocación no amplía los permisos de escritura del rol.

## Sesgos al extraer

Formato compartido: agent-kits/shared/rationalization-table.md.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Con una frase ya conozco su voz» | Una muestra breve no acredita regularidad ni variedad. | Marcar los rasgos como provisionales y pedir contraste si cambia el resultado. |
| «Uso el tono habitual de los fundadores» | El estereotipo sustituye las muestras del autor. | Asociar cada rasgo a ejemplos concretos del corpus autorizado. |
| «Mezclo su voz pública y sus mensajes privados» | Los canales pueden tener objetivos y límites distintos. | Separar perfiles por canal y explicar el conflicto observado. |
| «Le asigno un 92 % de confianza» | No existe una calibración que justifique ese porcentaje. | Indicar evidencia suficiente, limitada o contradictoria con su motivo. |
| «Guardo el corpus para la próxima vez» | Analizar no autoriza persistir datos personales. | Guardar solo lo solicitado en el destino ya autorizado. |
| «Corrijo las muestras para que encajen» | Altera la evidencia usada para inferir el estilo. | Mantener la cita fiel y separar propuestas de mejora. |

## Salida y evidencia

Perfil breve con ámbito, procedencia, rasgos, ejemplos, excepciones y cuestiones
abiertas. Distingue lo observado de lo acordado; si se persiste, informa la ruta
y qué se actualizó. No declares una identidad o preferencia que no esté acreditada.
