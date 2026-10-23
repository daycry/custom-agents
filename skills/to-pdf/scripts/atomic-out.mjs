/**
 * atomic-out.mjs — escribe una salida derivada sin dejar copias parciales ni pasar una vieja por actual.
 *
 * `render(tmpPath)` produce el fichero en un temporal del MISMO directorio; solo si termina bien se
 * renombra sobre `out`. Si falla, el temporal se borra y, si ya existía `out`, el error lo dice: ese
 * PDF es de una fuente anterior y no debe presentarse como el actual. No borra la salida previa
 * (es del usuario); el llamador ve el exit distinto de 0 y el aviso.
 */
import { existsSync } from 'node:fs';
import { rename, rm } from 'node:fs/promises';
import { dirname, basename, join } from 'node:path';

export async function writeAtomically(out, render) {
  const tmp = join(dirname(out), `.${basename(out)}.${process.pid}.${Date.now()}.tmp`);
  try {
    await render(tmp);
    if (!existsSync(tmp)) throw new Error('la conversión terminó sin escribir la salida');
    await rename(tmp, out);
  } catch (e) {
    await rm(tmp, { force: true });
    const reason = e && e.message ? e.message : String(e);
    const stale = existsSync(out)
      ? ` — ${out} sigue siendo la salida ANTERIOR: no corresponde a esta fuente`
      : '';
    throw new Error(`${reason}${stale}`);
  }
  return out;
}
