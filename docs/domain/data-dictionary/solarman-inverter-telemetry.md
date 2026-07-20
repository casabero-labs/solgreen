# Diccionario SolarMAN — Telemetría técnica del inversor

Formato inicial observado: 120 columnas. El parser debe conservar nombres originales y mapear progresivamente a señales canónicas.

| # | Columna original | Nombre canónico propuesto | Unidad/tipo |
|---:|---|---|---|
| 1 | `Nombre del dispositivo` | `nombre_del_dispositivo` | texto/estado |
| 2 | `número de serie` | `numero_de_serie` | texto/estado |
| 3 | `Dispositivo principal` | `dispositivo_principal` | texto/estado |
| 4 | `Número de serie del dispositivo` | `numero_de_serie_del_dispositivo` | texto/estado |
| 5 | `Hora actualizada` | `hora_actualizada` | texto/estado |
| 6 | `Nombre del dispositivo` | `nombre_del_dispositivo` | texto/estado |
| 7 | `PV Open Circuit Voltage(V)` | `pv_open_circuit_voltage` | V |
| 8 | `PV Maximum Charging Current(A)` | `pv_maximum_charging_current` | A |
| 9 | `Rated Output Power(W)` | `rated_output_power` | W |
| 10 | `Parallel Mode` | `parallel_mode` | texto/estado |
| 11 | `Hora del sistema` | `hora_del_sistema` | texto/estado |
| 12 | `Current state of machine` | `current_state_of_machine` | texto/estado |
| 13 | `BMS Version1` | `bms_version1` | texto/estado |
| 14 | `BMS Version2` | `bms_version2` | texto/estado |
| 15 | `Software Version Number 1` | `software_version_number_1` | texto/estado |
| 16 | `Software Version Number 2` | `software_version_number_2` | texto/estado |
| 17 | `Hardware Version` | `hardware_version` | texto/estado |
| 18 | `Software Version Number 4` | `software_version_number_4` | texto/estado |
| 19 | `Upgrade Flag Bit` | `upgrade_flag_bit` | texto/estado |
| 20 | `Minor version number` | `minor_version_number` | texto/estado |
| 21 | `Voltaje CC PV1(V)` | `voltaje_cc_pv1` | V |
| 22 | `Voltaje CC PV2(V)` | `voltaje_cc_pv2` | V |
| 23 | `Corriente CC PV1(A)` | `corriente_cc_pv1` | A |
| 24 | `Corriente CC PV2(A)` | `corriente_cc_pv2` | A |
| 25 | `Potencia CC PV1(W)` | `potencia_cc_pv1` | W |
| 26 | `Potencia CC PV2(W)` | `potencia_cc_pv2` | W |
| 27 | `Voltaje CA R/U/A(V)` | `voltaje_ca_r_u_a` | V |
| 28 | `Voltaje CA S/V/B(V)` | `voltaje_ca_s_v_b` | V |
| 29 | `Corriente CA R/U/A(A)` | `corriente_ca_r_u_a` | A |
| 30 | `Corriente CA S/V/B(A)` | `corriente_ca_s_v_b` | A |
| 31 | `Frecuencia R de salida de CA(Hz)` | `frecuencia_r_de_salida_de_ca` | Hz |
| 32 | `Frecuencia de salida CA S(Hz)` | `frecuencia_de_salida_ca_s` | Hz |
| 33 | `Potencia total CA (activa)(W)` | `potencia_total_ca` | W |
| 34 | `Producción acumulada (activa)(kWh)` | `produccion_acumulada` | kWh |
| 35 | `Producción diaria (activa)(kWh)` | `produccion_diaria` | kWh |
| 36 | `PV Total Charging Power(W)` | `pv_total_charging_power` | W |
| 37 | `Total Charging Power (PV + Mains)(W)` | `total_charging_power` | W |
| 38 | `Daily generator output(kWh)` | `daily_generator_output` | kWh |
| 39 | `Total generator output(kWh)` | `total_generator_output` | kWh |
| 40 | `Estado de red` | `estado_de_red` | texto/estado |
| 41 | `Frecuencia de red(Hz)` | `frecuencia_de_red` | Hz |
| 42 | `Alimentación acumulada de red(kWh)` | `alimentacion_acumulada_de_red` | kWh |
| 43 | `Energía adquirida acumulada(kWh)` | `energia_adquirida_acumulada` | kWh |
| 44 | `Alimentación diaria de red(kWh)` | `alimentacion_diaria_de_red` | kWh |
| 45 | `Energía diaria adquirida(kWh)` | `energia_diaria_adquirida` | kWh |
| 46 | `Battery Charging Of The Day By Utility Grid (Ah)(AH)` | `battery_charging_of_the_day_by_utility_grid` | AH |
| 47 | `Share the amount of charge on the same day(kWh)` | `share_the_amount_of_charge_on_the_same_day` | kWh |
| 48 | `Cumulative Charge Of Utility Power(kWh)` | `cumulative_charge_of_utility_power` | kWh |
| 49 | `Mains Charging Power(W)` | `mains_charging_power` | W |
| 50 | `Total Active Power Of The Grid(W)` | `total_active_power_of_the_grid` | W |
| 51 | `Utility Charge Current(A)` | `utility_charge_current` | A |
| 52 | `L1 Utility Active Power(W)` | `l1_utility_active_power` | W |
| 53 | `L2 Utility Active Power(W)` | `l2_utility_active_power` | W |
| 54 | `L1 Utility Apparent power(VA)` | `l1_utility_apparent_power` | VA |
| 55 | `L2 Utility Apparent power(VA)` | `l2_utility_apparent_power` | VA |
| 56 | `Total charging amount of mains(AH)` | `total_charging_amount_of_mains` | AH |
| 57 | `Grid Code` | `grid_code` | texto/estado |
| 58 | `L1 Mains Voltage(V)` | `l1_mains_voltage` | V |
| 59 | `L1 Mains Current(A)` | `l1_mains_current` | A |
| 60 | `L2 Mains Voltage(V)` | `l2_mains_voltage` | V |
| 61 | `L2 Mains Current(A)` | `l2_mains_current` | A |
| 62 | `Potencia de carga L1(W)` | `potencia_de_carga_l1` | W |
| 63 | `Potencia de carga L2(W)` | `potencia_de_carga_l2` | W |
| 64 | `Corriente de salida R/U/A(A)` | `corriente_de_salida_r_u_a` | A |
| 65 | `Corriente consumida S/V/B(A)` | `corriente_consumida_s_v_b` | A |
| 66 | `Potencia de consumo total(W)` | `potencia_de_consumo_total` | W |
| 67 | `Potencia aparente de consumo total(VA)` | `potencia_aparente_de_consumo_total` | VA |
| 68 | `Consumo total(kWh)` | `consumo_total` | kWh |
| 69 | `Consumo diario(kWh)` | `consumo_diario` | kWh |
| 70 | `L1 Load Rate(%)` | `l1_load_rate` | % |
| 71 | `L2 Load Rate(%)` | `l2_load_rate` | % |
| 72 | `Load Rate Of Whole Machine(%)` | `load_rate_of_whole_machine` | % |
| 73 | `L1 Load Apparent Power(VA)` | `l1_load_apparent_power` | VA |
| 74 | `L2 Load Apparent Power(VA)` | `l2_load_apparent_power` | VA |
| 75 | `Household Load Side Power L1(W)` | `household_load_side_power_l1` | W |
| 76 | `Household Load Side Power L2(W)` | `household_load_side_power_l2` | W |
| 77 | `BUS voltage(V)` | `bus_voltage` | V |
| 78 | `Positive BUS voltage(V)` | `positive_bus_voltage` | V |
| 79 | `Negative BUS voltage(V)` | `negative_bus_voltage` | V |
| 80 | `Output frequency(Hz)` | `output_frequency` | Hz |
| 81 | `Estado de batería` | `estado_de_bateria` | texto/estado |
| 82 | `Battery Charging Type` | `battery_charging_type` | texto/estado |
| 83 | `Voltaje de batería(V)` | `voltaje_de_bateria` | V |
| 84 | `Corriente de batería(A)` | `corriente_de_bateria` | A |
| 85 | `Potencia de batería(W)` | `potencia_de_bateria` | W |
| 86 | `SoC(%)` | `soc` | % |
| 87 | `Energía de carga total(kWh)` | `energia_de_carga_total` | kWh |
| 88 | `Energía de descarga total(kWh)` | `energia_de_descarga_total` | kWh |
| 89 | `Energía de carga diaria(kWh)` | `energia_de_carga_diaria` | kWh |
| 90 | `Energía de descarga diaria(kWh)` | `energia_de_descarga_diaria` | kWh |
| 91 | `Battery Charging Of The Day (Ah)(AH)` | `battery_charging_of_the_day` | AH |
| 92 | `Battery Discharging Of The Day (Ah)(AH)` | `battery_discharging_of_the_day` | AH |
| 93 | `Cumulative Data Of Battery Charging (Ah)(AH)` | `cumulative_data_of_battery_charging` | AH |
| 94 | `Cumulative Data Of Battery Discharging (Ah)(AH)` | `cumulative_data_of_battery_discharging` | AH |
| 95 | `Battery 1 Status` | `battery_1_status` | texto/estado |
| 96 | `Temperatura ambiente(℃)` | `temperatura_ambiente` | °C |
| 97 | `Inverter radiator temperature(℃)` | `inverter_radiator_temperature` | °C |
| 98 | `Temperatura del transformador(℃)` | `temperatura_del_transformador` | °C |
| 99 | `PV radiator temperature(℃)` | `pv_radiator_temperature` | °C |
| 100 | `Estado de inversor` | `estado_de_inversor` | texto/estado |
| 101 | `System Status` | `system_status` | texto/estado |
| 102 | `Generator Operation Mode` | `generator_operation_mode` | texto/estado |
| 103 | `Voltaje de generador L1(V)` | `voltaje_de_generador_l1` | V |
| 104 | `Voltaje de generador L2(V)` | `voltaje_de_generador_l2` | V |
| 105 | `Voltaje de generador L3(V)` | `voltaje_de_generador_l3` | V |
| 106 | `Gen Current L1(A)` | `gen_current_l1` | A |
| 107 | `Gen Current L2(A)` | `gen_current_l2` | A |
| 108 | `Gen Current L3(A)` | `gen_current_l3` | A |
| 109 | `Generator Active Power L1(W)` | `generator_active_power_l1` | W |
| 110 | `Generator Active Power L2(W)` | `generator_active_power_l2` | W |
| 111 | `Generator Active Power L3(W)` | `generator_active_power_l3` | W |
| 112 | `Generator  Apparent Power L1(VA)` | `generator_apparent_power_l1` | VA |
| 113 | `Generator  Apparent Power L2(VA)` | `generator_apparent_power_l2` | VA |
| 114 | `Generator  Apparent Power L3(VA)` | `generator_apparent_power_l3` | VA |
| 115 | `Frecuencia generador(Hz)` | `frecuencia_generador` | Hz |
| 116 | `Number Of Parallel Machines` | `number_of_parallel_machines` | texto/estado |
| 117 | `Total Local Load Power Of Parallel System(W)` | `total_local_load_power_of_parallel_system` | W |
| 118 | `Total Household Load Power Of Parallel System(W)` | `total_household_load_power_of_parallel_system` | W |
| 119 | `Total Grid Power Of Parallel System(W)` | `total_grid_power_of_parallel_system` | W |
| 120 | `Total Oil Engine Port Power Of Parallel System(W)` | `total_oil_engine_port_power_of_parallel_system` | W |

## Grupos funcionales

- Identificación y versiones: 1–20.
- PV/MPPT: 21–26 y 36–39.
- Salida AC: 27–35.
- Red: 40–61.
- Cargas: 62–76.
- BUS y frecuencia de salida: 77–80.
- Batería: 81–95.
- Temperaturas y estados: 96–102.
- Generador: 103–115.
- Paralelo: 116–120.

## Señales prioritarias del MVP

Timestamp, estado de máquina, PV1/PV2 V-A-W, red L1/L2 V-A-W, frecuencia, carga L1/L2, carga total, BUS, batería V-A-W-SOC, temperaturas, estado del inversor, `System Status`, `Grid Code` y versiones.
