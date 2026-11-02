# Plan de validación

- Adaptador: metadatos propios, cwd vecino rechazado, ninguna llamada a resume/read
  de turnos/start, títulos sin preview, fechas e IDs inválidos, paginación,
  duplicados, cursor repetido, límite, error y cierre de procesos propios.
- Servicio/HTTP: autenticación, workspace registrado, caché por proyecto,
  proveedores sin soporte explícitos y cierre durante consulta.
- Navegador real: solo lectura externa, XSS en título, cambio de proyecto, chat
  propio sin regresión, estados remoto/vacío/error, filtros y teclado.
- Actividad: opt-in explicado, señal con fecha, respuesta terminada diferenciada,
  sin afirmar proceso vivo desde hooks. Eventos reales después de habilitar
  captura; no inferencia ni agentes ficticios.
- Revisión A/B/C según selección, comprobación de alcance, lint, evals, interop,
  regresiones pertinentes y cobertura oficial sobre código cambiado.
