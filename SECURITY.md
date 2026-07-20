# Seguridad de Solgreen

## Datos protegidos

- archivos originales de SolarMAN;
- números de serie y registradores;
- patrones de ocupación inferibles por consumo;
- ubicación y configuración de la instalación;
- claves de proveedores de IA;
- informes técnicos privados.

## Controles

- secretos exclusivamente en Infisical;
- almacenamiento privado por defecto;
- cifrado en tránsito y reposo;
- RBAC por instalación;
- RLS en PostgreSQL;
- URLs firmadas para archivos;
- auditoría de imports, análisis, exportaciones y cambios de configuración;
- minimización de datos enviados a LLM;
- redacción de seriales en reportes compartibles.

## Política IA

Los proveedores reciben episodios estructurados, no el dataset crudo completo, salvo decisión humana explícita y documentada.

## Reporte de vulnerabilidades

No abrir issues públicos con secretos, seriales, archivos de planta ni capturas privadas. Usar el canal privado del propietario del repositorio.
