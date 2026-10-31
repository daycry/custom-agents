# Reserva antes de llamar

Define unidad monetaria y precisión fija, presupuesto total, ámbito y mecanismo
atómico compartido por los workers que consumen ese saldo. No uses un contador
independiente por proceso como límite global.

La admisión reserva una cota válida para la solicitud antes de efectuarla. La cota
necesita precios vigentes y límites compatibles con el contrato del proveedor;
si no se puede acotar el coste, declara que no hay garantía de límite estricto.
Un modo estimado solo procede si está autorizado y se identifica como tal.

Relaciona cada reserva con un ID de operación y cada intento real. Al completar,
reconcilia uso y coste, liberando únicamente saldo que se sepa no consumido.
Un timeout, caída o cancelación no libera automáticamente una reserva que pudo
facturarse. Mantén un estado incierto recuperable y contrástalo con los recibos
disponibles; no repitas llamadas para averiguar si la primera funcionó.

En el proyecto consumidor verifica concurrencia sobre el último saldo disponible,
caída tras reservar, respuesta perdida, reconciliación repetida y precio ausente.
No son pruebas que esta skill haya ejecutado: su implementación determina los
oráculos. Calidad, latencia y coste se comparan sobre la misma carga y condiciones.
