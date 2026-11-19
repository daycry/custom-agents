// .opencode/tools/{{nombre}}.ts — tool propia de OpenCode (el nombre del fichero es el de la tool).
// Una tool es código que ejecuta el runtime: léela como tal, sin red ni escrituras inesperadas.
// Contrato: salida corta y determinista, estado en la primera línea, errores con causa y arreglo.
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "{{descripcion}}",
  args: {
    entrada: tool.schema.string().describe("<qué recibe y en qué formato>"),
  },
  async execute(args) {
    // <hace una sola cosa; devuelve texto estable: «ok · …» o «error · causa · cómo arreglarlo»>
    return `ok · recibido: ${args.entrada}`
  },
})
