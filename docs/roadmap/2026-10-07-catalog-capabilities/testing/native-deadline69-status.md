# Plazo nativo y validación global

El arranque síncrono de la CLI consumía el plazo antes de crear el temporizador.
La regresión con proceso real observa exit 0 tardío en el código anterior y exige
exit 124 sin salida. La corrección conserva el deadline absoluto y descarta
respuestas tardías: seis casos pasan en cada plataforma, sin skips.

Windows global conserva 7.126 pases, 2 fallos y 99 skips sobre 7.227 casos. Los
dos fallos se reproducen en el informe y pasan juntos después de restaurar
los modos Git de la copia privada y aclarar la firma del contrato. La ejecución
global original sigue fallida; los dos pases posteriores no la relabelan.
Los 31 archivos Python modificados tienen cobertura oficial de 90,95 %.

Los 61 contratos DOM de actividad y revisión pasan. Se compila el cuerpo exacto
que incrusta el HTML bajo el nombre del asset, con cobertura V8 oficial:
actividad 100 % y revisión 98,79 % de líneas. No acredita interacción en navegador.

Node completo conserva 327/329 pases con concurrencia por defecto. La prueba
con concurrencia de archivos 2 agotó su límite global antes de terminar; el
segundo recorrido mantiene todos los casos y plazos individuales con presupuesto
global de 900 s: pasan los 329 casos, sin fallos ni skips. CI y su copia manual
usan concurrencia de archivos 2. La cobertura V8 oficial de los tres archivos
medidos en esta suite es 92,32 % de líneas; no incluye los otros tres destinos
JavaScript del diff. Los dos controladores del panel se miden por separado; el
export OpenCode conserva bytes idénticos al adaptador, sin acreditar su despacho.
Linux Python global, revisión independiente, aceptación nativa
y visual, consolidación en el checkout, commits y push siguen pendientes.

[Evidencia estructurada](native-deadline69-evidence.json).

Linux global terminó con 7.160 pases, 8 fallos y 59 skips sobre 7.227 casos;
colección conservada, dashboard directo correcto y cobertura de los 31 archivos
Python modificados de 91,07 %. El contenedor propio se retiró. Siete fallos
proceden de la copia de prueba: archivos bind desde Windows expuestos como
ejecutables y tmpfs sin ejecución pese al chmod de las fixtures. El octavo
corresponde a la firma documental. Con fuente de entrada en solo lectura,
copia nativa con modos exactos del manifiesto y tmpfs ejecutable para las
fixtures, pasan los ocho casos, sin editar tests o producto. Fuente y
dependencias permanecen intactas y el contenedor focal se retiró. La suite
completa bajo esa topología todavía debe ejecutarse; el focal no la acepta.

La suite Linux completa en copia nativa pasó: 7.168 casos, 59 skips y cero
fallos sobre los mismos 7.227 IDs; cobertura CTracer de los 31 archivos Python
modificados de 91,07 %, dashboard directo correcto, fuente/dependencias
conservadas y contenedor propio eliminado. La anterior suite fallida se conserva.

El módulo OpenCode generado pasa 23 casos con el instalador real de proyecto
y guardias por rol, sin cambiar aserciones. Cobertura V8 del entrypoint:
93,03 % de líneas / 64,67 % de ramas. La primera fixture parcial conserva
17/20: dos fuentes mal resueltas al mover el test y un bundle incompleto.
Ninguno requirió editar producción. No prueba carga del servidor nativo.

Los seis destinos JavaScript del diff tienen informes V8 reales; contra
HEAD 3be4821 hay 214 líneas de fuente modificadas, dos no cubiertas: 99,07 %.
Este conteo incluye comentarios y líneas vacías; no es una métrica de
statements o ramas ni se suma a cobertura Python. Windows vuelve a ejecutar
la suite completa del source1141 con los modos Git corregidos; sigue pendiente.
