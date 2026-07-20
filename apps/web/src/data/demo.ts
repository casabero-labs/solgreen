export type PeriodKey = "24h" | "7d" | "30d";

export type EnergyPoint = {
  label: string;
  pv: number;
  load: number;
  grid: number;
};

export type DashboardPeriod = {
  productionKwh: number;
  consumptionKwh: number;
  gridImportKwh: number;
  batterySocPct: number;
  coveragePct: number;
  qualityLabel: string;
  points: EnergyPoint[];
};

export const dashboardPeriods: Record<PeriodKey, DashboardPeriod> = {
  "24h": {
    productionKwh: 28.4,
    consumptionKwh: 31.7,
    gridImportKwh: 8.6,
    batterySocPct: 72,
    coveragePct: 98.6,
    qualityLabel: "Cobertura alta · 1 hueco corto",
    points: [
      { label: "00:00", pv: 0, load: 1.1, grid: 0.8 },
      { label: "03:00", pv: 0, load: 0.9, grid: 0.7 },
      { label: "06:00", pv: 0.4, load: 1.4, grid: 0.5 },
      { label: "09:00", pv: 3.8, load: 2.2, grid: 0 },
      { label: "12:00", pv: 6.7, load: 4.1, grid: 0 },
      { label: "15:00", pv: 4.9, load: 3.2, grid: 0 },
      { label: "18:00", pv: 0.8, load: 3.7, grid: 0.4 },
      { label: "21:00", pv: 0, load: 2.8, grid: 1.3 },
    ],
  },
  "7d": {
    productionKwh: 191.6,
    consumptionKwh: 218.9,
    gridImportKwh: 59.4,
    batterySocPct: 68,
    coveragePct: 96.2,
    qualityLabel: "Cobertura útil · revisar 3 huecos",
    points: [
      { label: "Lun", pv: 29.4, load: 31.2, grid: 7.4 },
      { label: "Mar", pv: 27.8, load: 30.1, grid: 8.2 },
      { label: "Mié", pv: 24.2, load: 32.6, grid: 11.1 },
      { label: "Jue", pv: 30.7, load: 31.4, grid: 7.1 },
      { label: "Vie", pv: 28.9, load: 30.8, grid: 7.9 },
      { label: "Sáb", pv: 26.1, load: 33.2, grid: 9.6 },
      { label: "Dom", pv: 24.5, load: 29.6, grid: 8.1 },
    ],
  },
  "30d": {
    productionKwh: 812.3,
    consumptionKwh: 941.8,
    gridImportKwh: 257.6,
    batterySocPct: 70,
    coveragePct: 92.8,
    qualityLabel: "Cobertura parcial · análisis preliminar",
    points: [
      { label: "Sem 1", pv: 191.6, load: 218.9, grid: 59.4 },
      { label: "Sem 2", pv: 208.4, load: 226.7, grid: 55.1 },
      { label: "Sem 3", pv: 184.2, load: 238.6, grid: 71.8 },
      { label: "Sem 4", pv: 228.1, load: 257.6, grid: 71.3 },
    ],
  },
};
