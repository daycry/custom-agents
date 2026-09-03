# Anti-patrones de TDD — catálogo con ejemplos

Léelo desde `SKILL.md` **solo** si dudas de si tu test cuenta como rojo válido. Cada entrada: qué se ve,
por qué no cuenta, y la versión que sí cuenta. Ejemplos en Python/pytest por brevedad; el patrón es el
mismo en cualquier stack (`by-stack.md`).

## 1. Tests después («ya lo cubro»)

**Se ve así:** el diff tiene `model_tier.py` completo y, en el último commit, `test_model_tier.py` con
tests que pasan a la primera.

**Por qué no cuenta:** ningún test ha fallado nunca; no sabes si detectan un fallo o si pasan por
casualidad (aserciones débiles, fixture que coincide con el default).

**Versión que cuenta:** ley dura → borra el código, escribe el test del primer criterio, córrelo
(`1 failed` con `NameError: resolver`), registra `RED: … · fecha`, reescribe lo mínimo.

## 2. Test vacío o `assert True`

```python
def test_override_effort():
    pass            # TODO
def test_algo():
    assert True     # placeholder
```

**Por qué no cuenta:** no puede fallar → no expresa criterio. Si además anotas `RED:` con él, el ledger
miente (test-teatro).

**Versión que cuenta:**
```python
def test_override_effort(plugin):
    root, proj = plugin
    _dev(proj, {"modelos": {"architect": {"effort": "xhigh"}}})
    assert mt.resolver("architect", root=root, project=proj)["effort"] == "xhigh"
```
Falla hoy con `KeyError`/`AssertionError`; pasará cuando exista la capa 2.

## 3. Assert trivial

```python
def test_resolver():
    assert mt.resolver("architect", root=root) is not None
```

**Por qué no cuenta:** pasa devolviendo cualquier cosa (`{}`, `"x"`, un dict con el modelo equivocado).
El criterio era «devuelve `opus`/`high` del frontmatter».

**Versión que cuenta:** `assert (r["model"], r["effort"]) == ("opus", "high")` — falla con cualquier
valor distinto.

## 4. El test ya pasaba

**Se ve así:** escribes el test, sale `passed` a la primera y anotas `RED: … pasó` (o no anotas nada).

**Por qué no cuenta:** no hay evidencia de que detecte el fallo. Dos causas posibles: (a) el criterio ya
estaba implementado → no es TDD de esta tarea, dilo («criterio ya cubierto por X, sin RED»); (b) el
test no prueba lo que crees → **rómpelo a propósito**: comenta la línea de la funcionalidad y vuelve
a correr; si sigue verde, el test está mal.

## 5. Rojo por la razón equivocada

```
E   ModuleNotFoundError: No module named 'model_tier'
```

**Por qué no cuenta:** el test ni siquiera llegó al assert. Un `ImportError` del test, una fixture rota
o un `SyntaxError` son rojos de fontanería, no del criterio.

**Versión que cuenta:** arregla la fontanería (importa por ruta, crea la fixture) hasta ver
`AssertionError` o `NameError`/`AttributeError` **de la función nueva**. Ese es el `RED:` que se registra.

## 6. Un test gigante por tarea

```python
def test_todo_model_tier():
    # 40 líneas: frontmatter, dev.json, inválidos, corrupto, --all, --json…
```

**Por qué no cuenta (del todo):** al fallar no dice qué criterio falla; el ciclo RED→GREEN se vuelve
«todo rojo → todo verde» y pierde la señal por criterio. Además, el REFACTOR asusta.

**Versión que cuenta:** un test por criterio (`test_sin_dev_json_devuelve_frontmatter`,
`test_override_parcial_solo_effort`, `test_valor_invalido_se_ignora_con_aviso`…), cada uno con su `RED:`.

## 7. Test que prueba implementación, no comportamiento

```python
def test_usa_json_load(monkeypatch):
    llamado = []
    monkeypatch.setattr(json, "load", lambda fh: llamado.append(1) or {})
    mt.resolver("architect", root=root, project=proj)
    assert llamado
```

**Por qué no cuenta:** el criterio es «lee el override de dev.json», no «llama a `json.load`». El
REFACTOR (p. ej. leer con `json.loads(fh.read())`) lo rompe sin cambiar comportamiento → señal falsa.

**Versión que cuenta:** escribe un `dev.json` real en el tmp y afirma sobre la salida (`fuente.model ==
"dev.json"`).

## 8. GREEN con «ya que estoy»

**Se ve así:** el test pedía `effort` override; el commit trae también `--all`, caché y colores.

**Por qué no cuenta:** el código extra no tiene test rojo detrás → es tests-después encubierto (§1).

**Versión que cuenta:** el mínimo que pasa el test; lo demás, cada cosa con su rojo. Si sobra código sin
test, bórralo (ley dura) o escribe su test antes de conservarlo.

## 9. Refactor que «arregla» tests

**Se ve así:** tras el REFACTOR hay 3 tests en rojo y los editas hasta que pasan.

**Por qué no cuenta:** o el refactor cambió comportamiento (no era refactor) o los tests probaban
implementación (§7). En ambos casos editar el test destruye la red de seguridad.

**Versión que cuenta:** revierte el refactor y hazlo en pasos que mantengan el verde; o, si el test era
de implementación, reescríbelo contra comportamiento observable **antes** del refactor.

## 10. Excepción no declarada

**Se ve así:** tarea de prosa (un `.md` de agente) marcada `completado` con `tdd: true` y sin `RED:` ni
`TDD n/a`.

**Por qué no cuenta:** el silencio no distingue «no aplicaba» de «me lo salté». La Lente A lo marca como
gap Important.

**Versión que cuenta:** `TDD n/a: prosa (agents/reviewer.md), sin código testeable` en la tarea.
