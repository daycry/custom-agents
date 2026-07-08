# findings.json — contrato de datos del informe

El agente normaliza SAST (skill `cybersecurity`) + DAST (`active-scan.sh` + tools externas) en **un solo** `findings.json` por scan. `build-report.php` lo inyecta en `template.html` → `index.html`. El formato del informe es SIEMPRE el mismo; solo cambian los datos.

```jsonc
{
  "meta": {
    "project": "bloonde-laravel",
    "target_url": "https://bloonde-laravel.test",   // null si solo SAST
    "scan_id": "2026-07-02_1530",
    "date": "2026-07-02 15:30",
    "scope": "full",                                  // full | quick | diff | dast
    "authorized_by": "jcode",                          // registro de autorización
    "tools_used": ["cybersecurity-skill","active-scan","nuclei","testssl"],
    "overall_score": 63,                               // 0-100
    "grade": "C",                                      // A|B|C|D|F
    "verdict": "Necesita mejoras: 5 High, stack EOL."  // 1 frase
  },
  "counts": { "critical":0, "high":5, "medium":10, "low":9, "info":3 },
  "areas": [
    { "key":"vuln",   "name":"Vulnerability Detection",        "score":63, "weight":20, "summary":"..." },
    { "key":"authz",  "name":"Authorization & Access Control", "score":78, "weight":15, "summary":"..." },
    { "key":"secrets","name":"Secret Management",              "score":63, "weight":10, "summary":"..." },
    { "key":"deps",   "name":"Dependency Security",            "score":42, "weight":10, "summary":"..." },
    { "key":"dast",   "name":"Runtime / DAST (live target)",   "score":70, "weight":0,  "summary":"..." }
  ],
  "findings": [
    {
      "id":"F-001",
      "title":"Path traversal en borrado de ficheros vía original_filename",
      "severity":"high",            // critical|high|medium|low|info
      "confidence":"high",          // high|medium|low
      "area":"vuln",                // vuln|authz|secrets|deps|iac|threat|ai|logic|dast
      "cwe":"CWE-22",
      "owasp":"A01:2021",
      "source":"sast",              // sast | dast
      "location":"app/Http/Controllers/Admin/PostAdminController.php:175",
      "what":"Qué es, en 1-2 frases.",
      "why":"Por qué importa / impacto.",
      "exploit":"Cómo lo explotaría un atacante (didáctico).",
      "fix":"Cómo se corrige, con before/after si aplica.",
      "evidence":"Fragmento redactado (secretos con first4****last4)."
    }
  ],
  "trend": {                        // opcional; el agente lo calcula vs scan anterior
    "previous_scan":"2026-06-20_1000",
    "new":["F-001"],
    "fixed":["F-014"],
    "recurring":["F-002","F-003"]
  }
}
```

Reglas: severidades y áreas en minúscula (valores fijos arriba). `evidence` SIEMPRE redactada. `weight` es informativo (el score global lo calcula el agente). El informe tolera campos ausentes (trend, target_url, evidence).
