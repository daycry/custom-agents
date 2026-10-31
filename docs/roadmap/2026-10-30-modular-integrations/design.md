# Contratos de la modularización

- El catálogo mantiene fuentes canónicas únicas y perfiles de selección; importar una idea no obliga a añadir una skill.
- El núcleo decide sobre tasks.md y docs/. Las herramientas externas son proyecciones o destinos opt-in, nunca el ledger ni autoridad sobre QA.
- Los puertos describen funciones y eventos, no marcas ni nombres de herramientas. Los adaptadores opcionales traducen datos y recibos.
- La configuración pertenece a la raíz del proyecto. No se buscan opt-ins en otros proyectos ni se ejecutan rutas tomadas de esa configuración.
- Una integración declarada permanece con disponibilidad/permisos sin verificar hasta contrastar la sesión. No es una autorización para mensajes o efectos externos.
- Nuevas integraciones pueden ser extensiones de proyecto; el catálogo del bundle no constituye una lista cerrada de proveedores.
- Jira/Confluence existentes mantienen compatibilidad mediante lectura explícita de sus opt-ins; una configuración nueva tiene precedencia. Nunca se resetea o migra silenciosamente una configuración corrupta.
- Los perfiles filtrarán solo modos que realmente soporten la selección. Las instalaciones nativas completas se describen como completas; no se modifica una caché compartida para simular selección por proyecto.
- Las pruebas de integración usan directorios/variables/transportes propios, sin cambiar cuentas reales ni invocar servicios externos.

Investigación de referencia: ECC, repositorio affaan-m/ECC, revisión b38be6a7f6350964d59328b52f0624e1d1d552d1; manifiestos de módulos/perfiles y skill-adaptation-policy. Es evidencia de modularidad/instalación, no prueba de DDD. El diseño de puertos/adaptadores se aplica a las responsabilidades existentes, sin duplicar el parser del ledger ni crear otro motor de permisos.

## Selección concreta

El catálogo actual tiene 33 skills: 17 del ciclo base y 16 opcionales. Jira, Confluence, seguridad especializada, PDF, training, herramientas de catálogo, contenido/voz/relaciones y guías de aplicaciones LLM/datos tienen módulos separados. Tener un módulo en el catálogo no autoriza activarlo ni acredita uso medido.

Las 37 propuestas se mantienen como candidatas en admission.json: 19 especialidades para añadir bajo demanda, 16 extensiones de proyecto, una mejora de cobertura por estudiar con el consumidor y una decisión de rigor pendiente. Este cambio no instala esas 37 ni añade conectores reales a cuentas.

## Configuración del puerto v1

La raíz del proyecto contiene .claude/integrations.json: version=1 y bindings=[]. Cada binding activo identifica id, purpose, contract_version=1, adapter (kind=skill/tool, name, origin), events, capabilities y settings opcional como referencia relativa al proyecto. Los IDs de proveedores y herramientas no se enumeran en una lista cerrada del plugin.

El router devuelve solo declaraciones, con availability/permissions=unverified y execution=not_run. El cliente contrasta la sesión y el adaptador antes de ejecutar. Los filtros event/purpose/operation nunca convierten la configuración en permiso. Un binding inválido conserva diagnósticos y no suprime otro independiente; IDs duplicados no se eligen arbitrariamente. Una configuración explícita vacía desactiva el fallback heredado.

Los contratos de salida y los recibos pertenecen al adaptador. No se permite deducir entrega por tener un plan, un timeout o un texto generado; un resultado incierto exige reconciliación. El estado canónico y los gates locales permanecen bajo sus dueños actuales.
