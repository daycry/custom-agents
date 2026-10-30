# C: memoria, límites y contrato de compilación

Identifica estándar C, compilador y target/ABI desde build, toolchain y CI. Usa
Make/CMake/Meson u otro sistema existente; no instala ni impone uno. C no es C++:
no propone RAII, STL o excepciones de C++ para un proyecto C. Comprueba extensiones
y compatibilidad antes de introducir APIs de otro estándar o compilador.

| Situación | Criterio | Escenario que lo comprueba |
|---|---|---|
| Buffer y longitud | Contrato de capacidad, longitud válida y terminador cuando sea cadena | Vacío, capacidad exacta y un byte de más no escriben fuera del buffer |
| Asignación de memoria | Propietario y liberación explícitos en éxito y error | Fallo en la segunda asignación libera la primera sin doble free |
| Tamaño calculado | Comprobar overflow antes de multiplicar/sumar y convertir tipos | Tamaños extremos se rechazan antes de reservar un buffer insuficiente |
| `realloc` | Conservar el puntero original hasta confirmar éxito | Fallo de reasignación permite liberar y conservar el estado anterior |
| E/S parcial | Bucle acotado que distingue EOF, error y avance según la API | Lectura/escritura corta no se presenta como mensaje completo |
| Concurrencia | Dueño y sincronización de memoria compartida; `volatile` no sustituye un lock | Operaciones concurrentes no dependen de lecturas/escrituras sin sincronizar |

No asumas ancho de `int`/`long`, signedness de char o layout idéntico entre targets.
En formatos externos, usa tipos/tamaños, orden de bytes y validación explícitos;
un cast de puntero no es un parser portable. Conserva códigos de error y errno
cuando corresponda al contrato, sin leer resultados inválidos tras el fallo.

Para aritmética de tamaño usa comprobaciones compatibles con el estándar y
toolchain del proyecto. Los builtins de overflow de GCC son una opción específica,
no una función ISO C universal. Si CMake exige un estándar, revisa también
C_STANDARD_REQUIRED y extensiones; C_STANDARD por sí solo puede admitir degradación.

Compila con los avisos acordados y prueba límites, entradas malformadas y fallos
de recursos. Sanitizers como AddressSanitizer, cuando el target los soporte,
ayudan a detectar accesos fuera de rango y uso tras liberar; su ausencia de avisos
no prueba corrección completa. No cambia flags de producción por invocar la guía.
Declara qué compilador/target y casos se ejecutaron, sin atribuirlo a otras plataformas.

Fuentes oficiales, 2026-10-30: [overflow GCC](https://gcc.gnu.org/onlinedocs/gcc/Integer-Overflow-Builtins.html),
[AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html),
[C_STANDARD](https://cmake.org/cmake/help/latest/prop_tgt/C_STANDARD.html).
Se consultan sus versiones al aplicar opciones concretas.
