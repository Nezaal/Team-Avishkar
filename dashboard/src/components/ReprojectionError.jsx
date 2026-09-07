import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);
try { ChartJS.register(annotationPlugin); } catch {}

export default function ReprojectionError({ data }) {
  if (!data) return null;

  const chartData = {
    labels: data.histogramLabels,
    datasets: [
      {
        data: data.histogramBins,
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        barPercentage: 1,
        categoryPercentage: 1,
      },
    ],
  };

  const meanIdx = data.histogramLabels.findIndex((l) => parseFloat(l) >= data.mean);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: { display: true, text: 'Reprojection Error (TMC-2 px)', color: '#64748b', font: { size: 11 } },
        ticks: { color: '#94a3b8', font: { size: 10 }, maxRotation: 0 },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: 'Frequency', color: '#64748b', font: { size: 11 } },
        ticks: { color: '#94a3b8', font: { size: 10 }, callback: (v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v) },
        grid: { color: 'rgba(148,163,184,0.08)' },
      },
    },
    plugins: {
      legend: { display: false },
      annotation: {
        annotations: {
          meanLine: {
            type: 'line',
            xMin: meanIdx, xMax: meanIdx,
            borderColor: '#16a34a', borderWidth: 2, borderDash: [6, 4],
            label: {
              display: true, content: `RMSE: ${data.mean} px`, position: 'start',
              color: '#16a34a', font: { size: 11, weight: 'bold' }, backgroundColor: 'transparent',
            },
          },
        },
      },
    },
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>Reprojection Error (px)</h3>
      </div>
      <div className="histogram-chart">
        <Bar data={chartData} options={options} />
      </div>
      {(data.median != null || data.p95 != null) && (
        <div className="error-stats">
          {data.median != null && <span>Median: <strong>{data.median.toFixed(2)} px</strong></span>}
          {data.p95 != null && <span>P95: <strong>{data.p95.toFixed(2)} px</strong></span>}
          {data.max != null && <span>Max: <strong>{data.max.toFixed(2)} px</strong></span>}
        </div>
      )}
    </div>
  );
}
