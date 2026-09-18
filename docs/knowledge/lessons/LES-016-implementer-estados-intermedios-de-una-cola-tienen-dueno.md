---
id: LES-016
tipo: leccion
area: Diseño / colas y estado durable
estado: aceptada (validada: usuario, 2026-09-18)
fuente: 2026-09-17-session-end-durable-capture/retro.md#aprendizajes
---

## implementer (y architect)

- **Cada estado intermedio de una cola tiene que tener dueño: quién lo ve y quién lo recupera.** En
  `session-end-durable-capture`, 5 de los 6 Critical del bucle de revisión salieron del mismo patrón:
  una corrección sustituía una operación atómica (`os.replace` único) por una secuencia de dos o tres
  pasos (`.claiming` → `utime` → rename; manifiesto → mover) y ningún barrido reconocía el fichero
  intermedio si el proceso moría entre pasos — la cola se declaraba «vacía y sana» con la sesión
  perdida dentro. Antes de codificar una cola durable: tabla **estado × fallo × quién recupera**, y un
  test de corte por transición con muerte real del proceso (`os.kill(getpid, 9)` dentro del paso),
  no un monkeypatch. Verificar cada guarda con su mutante (quitar la corrección → el test debe
  ponerse rojo): cuatro gaps de esta iniciativa se cerraron con guardas que su propio mutante no
  detectaba. Evidencia: `docs/roadmap/2026-09-17-session-end-durable-capture/tasks.md`, gaps 1-2,
  25-27 y N-1/N-2 de la 4.ª pasada.
