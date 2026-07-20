import { max } from "d3-array";
import { scaleLinear, scalePoint } from "d3-scale";
import { curveMonotoneX, line } from "d3-shape";
import { useId, useMemo } from "react";

import type { EnergyPoint } from "../data/demo";

type EnergyChartProps = {
  data: EnergyPoint[];
  periodLabel: string;
};

const WIDTH = 760;
const HEIGHT = 280;
const MARGIN = { top: 24, right: 24, bottom: 48, left: 56 };

export function EnergyChart({ data, periodLabel }: EnergyChartProps) {
  const titleId = useId();
  const descriptionId = useId();

  const chart = useMemo(() => {
    const highest = max(data, (point) => Math.max(point.pv, point.load, point.grid)) ?? 1;
    const x = scalePoint<string>()
      .domain(data.map((point) => point.label))
      .range([MARGIN.left, WIDTH - MARGIN.right])
      .padding(0.35);
    const y = scaleLinear()
      .domain([0, highest * 1.12])
      .nice()
      .range([HEIGHT - MARGIN.bottom, MARGIN.top]);

    const buildLine = (selector: (point: EnergyPoint) => number) =>
      line<EnergyPoint>()
        .x((point) => x(point.label) ?? MARGIN.left)
        .y((point) => y(selector(point)))
        .curve(curveMonotoneX)(data) ?? "";

    return {
      x,
      y,
      pvPath: buildLine((point) => point.pv),
      loadPath: buildLine((point) => point.load),
      gridPath: buildLine((point) => point.grid),
      ticks: y.ticks(4),
    };
  }, [data]);

  return (
    <figure className="chart-card" aria-labelledby={titleId} aria-describedby={descriptionId}>
      <div className="chart-heading">
        <div>
          <p className="eyebrow">PERFIL ENERGÉTICO</p>
          <h2 id={titleId}>Producción, consumo y red</h2>
          <p id={descriptionId} className="supporting-text">
            Serie demostrativa para {periodLabel}. Potencia y energía no se mezclan en el mismo eje.
          </p>
        </div>
        <div className="chart-legend" aria-label="Leyenda">
          <span><i className="legend-line legend-pv" />FV</span>
          <span><i className="legend-line legend-load" />Carga</span>
          <span><i className="legend-line legend-grid" />Red</span>
        </div>
      </div>

      <div className="chart-scroll" tabIndex={0} aria-label="Gráfica desplazable">
        <svg
          className="energy-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-labelledby={titleId}
          aria-describedby={descriptionId}
        >
          {chart.ticks.map((tick) => (
            <g key={tick}>
              <line
                className="chart-grid-line"
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={chart.y(tick)}
                y2={chart.y(tick)}
              />
              <text className="chart-axis-label" x={MARGIN.left - 12} y={chart.y(tick) + 4}>
                {tick}
              </text>
            </g>
          ))}

          {data.map((point) => (
            <text
              key={point.label}
              className="chart-axis-label chart-axis-label-x"
              x={chart.x(point.label)}
              y={HEIGHT - 18}
            >
              {point.label}
            </text>
          ))}

          <path className="chart-line chart-line-pv" d={chart.pvPath} />
          <path className="chart-line chart-line-load" d={chart.loadPath} />
          <path className="chart-line chart-line-grid" d={chart.gridPath} />
        </svg>
      </div>

      <details className="chart-table-disclosure">
        <summary>Ver tabla alternativa</summary>
        <div className="table-scroll">
          <table>
            <caption>Datos demostrativos del perfil energético</caption>
            <thead>
              <tr>
                <th>Periodo</th>
                <th>FV</th>
                <th>Carga</th>
                <th>Red</th>
              </tr>
            </thead>
            <tbody>
              {data.map((point) => (
                <tr key={point.label}>
                  <td>{point.label}</td>
                  <td>{point.pv.toFixed(1)}</td>
                  <td>{point.load.toFixed(1)}</td>
                  <td>{point.grid.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
