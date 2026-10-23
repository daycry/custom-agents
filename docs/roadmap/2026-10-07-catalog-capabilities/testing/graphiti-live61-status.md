# Comprobación real de Graphiti

El servidor instalado (graphiti-core 0.30.1) pierde la lectura del grupo anterior
tras escribir otro grupo: FalkorDB conserva tres episodios, pero MCP devuelve cero.
La causa se confirmó en el código instalado: get_episodes consulta el driver compartido,
que queda ligado al último grafo usado. El servidor oficial actual enruta por grupo.

Una imagen aislada con revisión oficial 0a3b1711b018e5590cf5c44a3ee3e67d6733ee13,
graphiti-core 0.30.2 y MCP 2.2.0 verificó la reconstrucción: seis creaciones únicas,
historial y UUID remapeados, grupo anterior consultable durante la construcción,
interrupción del cambio final y reintento sin duplicados. Se conservó un fallo del
comprobador al exigir una clave opcional de recibos; la auditoría posterior solo leyó
los datos existentes y confirmó el resultado. No se reencolaron los episodios.

La consulta semántica real sigue pendiente: el servidor devolvió tres entidades y
un hecho con UUID de episodios de origen, pero el adaptador busca nombres de episodios
y descartó los cuatro resultados. El siguiente cambio debe vincular esos UUID a
procedencia confirmada, respetar versiones retiradas y diferenciar contenido derivado.

Se comprobó la terminación de todos los envíos y se eliminaron únicamente los grafos
de prueba y la instancia temporal. El servicio original sigue activo con su imagen
anterior. La imagen compatible se conserva para revisión; no se ha desplegado.

[Recibo estructurado](graphiti-live61-evidence.json). Esta prueba no acepta las consultas
semánticas, los clientes nativos, la suite global ni el cierre de la iniciativa.
