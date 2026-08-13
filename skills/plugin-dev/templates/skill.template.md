---
name: <nombre-kebab>                    # == carpeta skills/<nombre-kebab>/ · nombre por FUNCIÓN, no por agente
description: <Qué capacidad aporta y a quién, 2-4 frases. Si es opt-in, dilo aquí. Termina SIEMPRE con los disparadores:> Úsala cuando el usuario diga "<frase 1>", "<frase 2>", o cuando <condición automática, p. ej. "X detecte Y">.
---

# <nombre> — <capacidad en una línea>

<Párrafo: qué hace, para qué agentes/comandos está pensada, y la regla central si la hay
(cita en bloque > si es una regla dura).>

## Cuándo NO usarla

<Los límites explícitos evitan invocaciones erróneas: qué casos parecen de esta skill pero no lo son.>

## Proceso

1. <Paso 1 — con el comando/script exacto si lo hay.>
2. <Paso 2.>
3. <Cierre: qué se entrega/actualiza y cómo se verifica.>

## Scripts propios (si los hay)

- `scripts/<x>.py` — <qué calcula>; determinista, con tests (`tests/…` o junto al script) y
  exit codes documentados (0 ok · 1 <caso> · 2 <caso>).
- Resolución de rutas: relativa dentro de la skill; desde fuera, `find` sobre
  `$PWD/.claude` y `$HOME/.claude` (regla 5 de CONVENTIONS).

## Degradación

<Qué pasa si falta la config/el conector/la dependencia: aviso concreto + el ciclo sigue.>
