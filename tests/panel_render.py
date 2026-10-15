"""Ayuda de los tests del panel: renderiza UNA pagina como lo haria el exportador o el servidor."""


def pagina(panel, datos, slug, *, live=False, review_enabled=False, review_id='', nonce=None, chart_ok=True):
    pp = panel._load_pages()
    modo = 'servido' if live else 'exportado'
    cuerpos = panel.cuerpos_paginas(datos, live=live, review_enabled=review_enabled, review_id=review_id)
    omitidos = set() if review_enabled else {'panel-review.js'}
    return pp.render_page(slug, modo=modo, generado='2026-10-15 10:00 UTC',
                          datos=pp.datos_de_pagina(slug, datos, modo=modo), cuerpo=cuerpos[slug],
                          chart_ok=chart_ok, nonce=nonce, scripts_omitidos=omitidos)
