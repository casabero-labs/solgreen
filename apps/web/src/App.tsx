import {
  Activity,
  BatteryCharging,
  CircleCheck,
  Database,
  FileClock,
  Gauge,
  Leaf,
  Moon,
  ReceiptText,
  Sun,
  TriangleAlert,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { EnergyChart } from "./components/EnergyChart";
import { dashboardPeriods, type PeriodKey } from "./data/demo";

type ViewKey = "overview" | "data" | "economy";
type Theme = "light" | "dark";

type MetricCardProps = {
  label: string;
  value: string;
  supporting: string;
  icon: React.ReactNode;
  testId?: string;
};

const periodLabels: Record<PeriodKey, string> = {
  "24h": "Últimas 24 horas",
  "7d": "Últimos 7 días",
  "30d": "Últimos 30 días",
};

function MetricCard({ label, value, supporting, icon, testId }: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-card-header">
        <span className="metric-icon" aria-hidden="true">{icon}</span>
        <span className="metric-label">{label}</span>
      </div>
      <strong className="metric-value" data-testid={testId}>{value}</strong>
      <p>{supporting}</p>
    </article>
  );
}

function StatusRow({
  title,
  detail,
  status,
}: {
  title: string;
  detail: string;
  status: "ready" | "review";
}) {
  const Icon = status === "ready" ? CircleCheck : TriangleAlert;
  return (
    <li className="status-row">
      <span className={`status-icon status-icon-${status}`} aria-hidden="true">
        <Icon size={18} strokeWidth={1.5} />
      </span>
      <span>
        <strong>{title}</strong>
        <small>{detail}</small>
      </span>
      <span className="status-word">{status === "ready" ? "Listo" : "Revisar"}</span>
    </li>
  );
}

export function App() {
  const [theme, setTheme] = useState<Theme>("light");
  const [view, setView] = useState<ViewKey>("overview");
  const [period, setPeriod] = useState<PeriodKey>("24h");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.style = "ink";
    document.documentElement.dataset.inkStyle = "console";
  }, [theme]);

  const snapshot = dashboardPeriods[period];
  const autonomy = useMemo(() => {
    if (snapshot.consumptionKwh === 0) return 0;
    return Math.max(
      0,
      Math.min(100, ((snapshot.consumptionKwh - snapshot.gridImportKwh) / snapshot.consumptionKwh) * 100),
    );
  }, [snapshot]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#main-content" aria-label="Solgreen, ir al inicio">
          <span className="brand-mark" aria-hidden="true"><Leaf size={18} strokeWidth={1.5} /></span>
          <span>SOLGREEN</span>
          <small>PRE-ALPHA</small>
        </a>

        <nav className="primary-nav" aria-label="Secciones principales">
          <button
            className={view === "overview" ? "nav-button active" : "nav-button"}
            type="button"
            aria-current={view === "overview" ? "page" : undefined}
            onClick={() => setView("overview")}
          >
            Planta
          </button>
          <button
            className={view === "data" ? "nav-button active" : "nav-button"}
            type="button"
            aria-current={view === "data" ? "page" : undefined}
            onClick={() => setView("data")}
          >
            Datos
          </button>
          <button
            className={view === "economy" ? "nav-button active" : "nav-button"}
            type="button"
            aria-current={view === "economy" ? "page" : undefined}
            onClick={() => setView("economy")}
          >
            Economía
          </button>
        </nav>

        <button
          className="theme-toggle"
          type="button"
          aria-label={theme === "light" ? "Activar modo oscuro" : "Activar modo claro"}
          aria-pressed={theme === "dark"}
          onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
        >
          <span aria-hidden="true">
            {theme === "light" ? <Moon size={16} strokeWidth={1.5} /> : <Sun size={16} strokeWidth={1.5} />}
          </span>
        </button>
      </header>

      <main id="main-content" className="main-content">
        <div className="demo-notice" role="note">
          <Database size={18} strokeWidth={1.5} aria-hidden="true" />
          <div>
            <strong>Datos demostrativos</strong>
            <span>Esta primera vertical valida navegación, jerarquía y accesibilidad. No representa una planta real ni una factura vigente.</span>
          </div>
        </div>

        <section className="page-heading" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">PLANTA · CASABERO</p>
            <h1 id="page-title">
              {view === "overview" && "Estado energético"}
              {view === "data" && "Calidad y procedencia"}
              {view === "economy" && "Inteligencia económica"}
            </h1>
            <p className="page-description">
              {view === "overview" && "Lectura clara de producción, consumo, red y batería con evidencia visible."}
              {view === "data" && "Separación explícita entre datos medidos, normalizados, calculados y pendientes."}
              {view === "economy" && "Fundación Afinia integrada, sin presentar cifras vigentes hasta contar con perfil verificado."}
            </p>
          </div>
          <span className="system-status">
            <i aria-hidden="true" />
            Modo demostración
          </span>
        </section>

        <div className="period-toolbar" aria-label="Seleccionar periodo">
          {(Object.keys(periodLabels) as PeriodKey[]).map((key) => (
            <button
              key={key}
              type="button"
              className={period === key ? "period-button active" : "period-button"}
              aria-pressed={period === key}
              onClick={() => setPeriod(key)}
            >
              {key}
            </button>
          ))}
          <span>{periodLabels[period]}</span>
        </div>

        {view === "overview" && (
          <>
            <section className="metric-grid" aria-label="Indicadores principales">
              <MetricCard
                label="Producción FV"
                value={`${snapshot.productionKwh.toFixed(1)} kWh`}
                supporting="Integración demostrativa del periodo"
                icon={<Sun size={18} strokeWidth={1.5} />}
                testId="production-value"
              />
              <MetricCard
                label="Consumo"
                value={`${snapshot.consumptionKwh.toFixed(1)} kWh`}
                supporting="Carga doméstica agregada"
                icon={<Zap size={18} strokeWidth={1.5} />}
              />
              <MetricCard
                label="Compra de red"
                value={`${snapshot.gridImportKwh.toFixed(1)} kWh`}
                supporting="No equivale todavía al medidor fiscal"
                icon={<Gauge size={18} strokeWidth={1.5} />}
              />
              <MetricCard
                label="SOC de referencia"
                value={`${snapshot.batterySocPct}%`}
                supporting={`Autonomía estimada del periodo: ${autonomy.toFixed(0)}%`}
                icon={<BatteryCharging size={18} strokeWidth={1.5} />}
              />
            </section>

            <EnergyChart data={snapshot.points} periodLabel={periodLabels[period]} />

            <section className="two-column-grid">
              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">CALIDAD</p>
                    <h2>Confianza del periodo</h2>
                  </div>
                  <strong className="quality-score">{snapshot.coveragePct.toFixed(1)}%</strong>
                </div>
                <div className="progress-track" aria-label={`Cobertura ${snapshot.coveragePct.toFixed(1)}%`}>
                  <span style={{ width: `${snapshot.coveragePct}%` }} />
                </div>
                <p className="supporting-text">{snapshot.qualityLabel}</p>
                <ul className="status-list">
                  <StatusRow title="Orden temporal" detail="Muestras ordenadas por UTC" status="ready" />
                  <StatusRow title="Semántica de cero" detail="Corrección científica pendiente en U1" status="review" />
                  <StatusRow title="Convención de red" detail="Requiere perfil humano confirmado" status="review" />
                </ul>
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">TRAZABILIDAD</p>
                    <h2>Últimos procesos</h2>
                  </div>
                  <Activity size={20} strokeWidth={1.5} aria-hidden="true" />
                </div>
                <ol className="activity-list">
                  <li>
                    <time>U0</time>
                    <span><strong>Frontend Ink iniciado</strong><small>React + D3 + tabla accesible</small></span>
                  </li>
                  <li>
                    <time>R0</time>
                    <span><strong>Baseline reconciliado</strong><small>CI, privacidad y estado real</small></span>
                  </li>
                  <li>
                    <time>E0</time>
                    <span><strong>Economía absorbida</strong><small>Perfil histórico marcado como no vigente</small></span>
                  </li>
                </ol>
              </article>
            </section>
          </>
        )}

        {view === "data" && (
          <section className="workspace-grid">
            <article className="panel panel-large">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">CONTRATOS</p>
                  <h2>Capas de procedencia</h2>
                </div>
                <Database size={20} strokeWidth={1.5} aria-hidden="true" />
              </div>
              <div className="lineage-stack">
                <div><span>01</span><strong>Original</strong><small>CSV/XLSX privado e inmutable</small></div>
                <div><span>02</span><strong>Medido</strong><small>Valor observado sin inferencia</small></div>
                <div><span>03</span><strong>Normalizado</strong><small>Tiempo, nombres y unidades canónicas</small></div>
                <div><span>04</span><strong>Calculado</strong><small>Energía y métricas con método versionado</small></div>
                <div><span>05</span><strong>Inferido</strong><small>Hipótesis separada de hechos</small></div>
              </div>
            </article>

            <aside className="panel action-panel" aria-labelledby="import-title">
              <FileClock size={22} strokeWidth={1.5} aria-hidden="true" />
              <h2 id="import-title">Importación web</h2>
              <p>La UI de carga real entra en U4 después de cerrar semántica, métricas y contratos API.</p>
              <button className="button button-primary" type="button" disabled aria-describedby="import-reason">
                Importar archivo
              </button>
              <small id="import-reason">No disponible todavía: evita prometer un flujo que el backend aún no expone.</small>
            </aside>
          </section>
        )}

        {view === "economy" && (
          <section className="workspace-grid">
            <article className="panel panel-large">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">AFINIA · E0 ABSORBIDO</p>
                  <h2>Factura y gestión de cargas</h2>
                </div>
                <ReceiptText size={20} strokeWidth={1.5} aria-hidden="true" />
              </div>
              <div className="economic-grid">
                <div>
                  <span className="economic-code">01</span>
                  <strong>Perfil tarifario</strong>
                  <p>Versionado por vigencia, territorio, segmento y fuente.</p>
                  <small>Estado: referencia histórica, no vigente</small>
                </div>
                <div>
                  <span className="economic-code">02</span>
                  <strong>Motor determinístico</strong>
                  <p>Factura, subsidio, redondeos y trazabilidad sin aritmética del LLM.</p>
                  <small>Estado: diseñado, implementación U5</small>
                </div>
                <div>
                  <span className="economic-code">03</span>
                  <strong>Perfil horario</strong>
                  <p>Compra, consumo, producción y batería integrados en kWh.</p>
                  <small>Bloqueado por métricas U2</small>
                </div>
                <div>
                  <span className="economic-code">04</span>
                  <strong>Recomendaciones</strong>
                  <p>Ventanas de carga con reserva, confort y potencia como restricciones.</p>
                  <small>Propuesta, nunca control automático</small>
                </div>
              </div>
            </article>

            <aside className="panel evidence-panel">
              <TriangleAlert size={22} strokeWidth={1.5} aria-hidden="true" />
              <h2>Resultado monetario bloqueado</h2>
              <p>No existe un perfil tarifario vigente y verificado en esta demostración.</p>
              <strong>No se muestra COP actual</strong>
              <small>La energía puede explorarse; la cifra monetaria espera fuente oficial y revisión humana.</small>
            </aside>
          </section>
        )}
      </main>

      <footer className="footer">
        <span>Solgreen · línea unificada U0</span>
        <span>Showcase Ink · estandar-casabero</span>
      </footer>
    </div>
  );
}
