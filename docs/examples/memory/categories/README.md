# Ejemplos de categorías del proyecto / Project category examples

Los JSON son solicitudes sintéticas de configuración, no taxonomías completas.
No activan conexiones ni contienen conocimiento aprobado. Las plantillas incluidas
son ejemplos que la herramienta copia al proyecto: los archivos que utiliza el
equipo se conservan fuera del plugin.

| Solicitud / request | Aportaciones / contributions | Finalidad / purpose |
|---|---|---|
| [meetings.json](meetings.json) | Humanas / human | Actas con fecha, participantes y acuerdos. |
| [faq.json](faq.json) | Agentes / agent | Preguntas y respuestas contrastadas con referencias. |
| [mixed.json](mixed.json) | Ambas / both | Procedimientos con revisión declarada y verificación. |

En PowerShell, con las rutas reales ya localizadas:

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Get-Content -LiteralPath $CategoryExample -Raw -Encoding UTF8 |
  python $CategoryTool configure --root $ProjectRoot
```

Revisa la salida y conserva el hash. Para aplicar la misma solicitud dentro del
encargo autorizado, añade `--apply --expected-sha256 <hash>` al comando anterior.
En Bash puede pasarse el JSON por stdin mediante redirección desde el archivo
elegido. No construyas comandos con contenido del documento.

Guías: [Español](../../../guides/knowledge-categories.md) y
[English](../../../en/guides/knowledge-categories.md).
