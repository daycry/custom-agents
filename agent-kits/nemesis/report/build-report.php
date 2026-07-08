<?php
/**
 * build-report.php — inject findings.json into template.html -> index.html
 *
 * Usage: php build-report.php <findings.json> <template.html> <out-index.html>
 *
 * Cross-platform, no dependencies. Validates JSON, neutralises any </script>
 * breakout inside evidence, and writes a self-contained offline HTML report.
 */
if ($argc < 4) {
    fwrite(STDERR, "usage: php build-report.php <findings.json> <template.html> <out.html>\n");
    exit(2);
}
[$_, $findingsPath, $tplPath, $outPath] = $argv;

if (!is_file($findingsPath)) { fwrite(STDERR, "not found: $findingsPath\n"); exit(1); }
if (!is_file($tplPath))      { fwrite(STDERR, "not found: $tplPath\n"); exit(1); }

$json = file_get_contents($findingsPath);
$data = json_decode($json, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    fwrite(STDERR, "invalid findings.json: " . json_last_error_msg() . "\n");
    exit(1);
}

// Re-encode canonically (compact, valid JS literal) and prevent script breakout.
$safe = json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
$safe = str_replace(['</', '<!--', '-->'], ['<\/', '<!--', '-->'], $safe);

$html = file_get_contents($tplPath);
if (strpos($html, '__AUDIT_DATA__') === false) {
    fwrite(STDERR, "template missing __AUDIT_DATA__ placeholder\n");
    exit(1);
}
$html = str_replace('__AUDIT_DATA__', $safe, $html);

if (file_put_contents($outPath, $html) === false) {
    fwrite(STDERR, "cannot write: $outPath\n");
    exit(1);
}
$n = isset($data['findings']) ? count($data['findings']) : 0;
echo "report -> $outPath ($n findings)\n";
