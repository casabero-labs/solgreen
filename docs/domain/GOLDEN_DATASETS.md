# Golden datasets

Los archivos reales permanecen fuera de Git. El repositorio guarda:

- hash SHA-256;
- rango temporal;
- schema detectado;
- lista de episodios esperados;
- fixtures sintéticos minimizados.

## Casos iniciales

### GOLDEN-001 — Dropout FV 17 de julio, 12:37

Esperado:

- potencia PV alta antes;
- PV1/PV2 a 0 W con voltaje presente;
- batería asume carga;
- recuperación fuerte después;
- clasificación `pv_mppt_dropout`;
- no afirmar AFCI confirmado.

### GOLDEN-002 — Red inestable 17 de julio

Esperado:

- pérdida de red;
- soporte de batería/PV;
- reconexión con L2 elevada;
- episodios separados o correlacionados según ventana.

### GOLDEN-003 — Descarga profunda y reinicios 19 de julio

Esperado:

- SOC mínimo alrededor de 7%;
- bloque de inicializaciones;
- estado de espera;
- correlación con código 04 observado externamente;
- limitación: el archivo no contiene el log nativo de alarma.

### GOLDEN-004 — Datos corruptos/desincronizados

Esperado:

- residual energético excesivo;
- no usar la muestra para eficiencia;
- calidad degradada.

### GOLDEN-005 — Salto SOC imposible

Esperado:

- flag de recalibración o inconsistencia;
- no interpretar como energía real cargada.
