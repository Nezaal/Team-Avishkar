import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';

ChartJS.register(LinearScale, PointElement, Tooltip);

export default function CorrespondenceDistribution({ data, correspondences, sourceImage }) {
  if (!data) return null;

  const inlierPts = (correspondences || []).filter((c) => c.inlier).map((c) => ({ x: c.ohrc_x, y: c.ohrc_y }));
  const outlierPts = (correspondences || []).filter((c) => !c.inlier).map((c) => ({ x: c.ohrc_x, y: c.ohrc_y }));

  const maxX = sourceImage?.width || 8192;
  const maxY = sourceImage?.height || 8192;

  const chartData = {
    datasets: [
      {
        label: 'Inliers',
        data: inlierPts,
        backgroundColor: 'rgba(22, 163, 74, 0.6)',
        pointRadius: 2.5,
        pointHoverRadius: 5,
      },
      {
        label: 'Outliers',
        data: outlierPts,
        backgroundColor: 'rgba(239, 68, 68, 0.35)',
        pointRadius: 2,
        pointHoverRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: { display: true, text: 'OHRC X (px)', color: '#64748b', font: { size: 11 } },
        min: 0, max: maxX,
        ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 5 },
        grid: { color: 'rgba(148,163,184,0.08)' },
      },
      y: {
        title: { display: true, text: 'OHRC Y (px)', color: '#64748b', font: { size: 11 } },
        min: 0, max: maxY,
        ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 5 },
        grid: { color: 'rgba(148,163,184,0.08)' },
      },
    },
    plugins: {
      legend: { display: true, position: 'top', labels: { boxWidth: 8, padding: 10, font: { size: 11 } } },
      tooltip: {
        callbacks: { label: (ctx) => `(${Math.round(ctx.raw.x)}, ${Math.round(ctx.raw.y)})` },
      },
    },
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3>Correspondence Distribution</h3>
      </div>
      <div className="correspondence-content">
        <div className="scatter-chart">
          <Scatter data={chartData} options={options} />
        </div>
        <div className="correspondence-stats">
          <div className="stat-row">
            <span className="stat-label">Raw Matches</span>
            <span className="stat-value">{data.totalPoints?.toLocaleString()}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">After Filter</span>
            <span className="stat-value">{data.filteredPoints?.toLocaleString()}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Inliers</span>
            <span className="stat-value stat-green">
              {data.inlierCount?.toLocaleString()} ({data.inlierPct}%)
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Outliers</span>
            <span className="stat-value stat-orange">
              {data.outlierCount?.toLocaleString()} ({data.outlierPct}%)
            </span>
          </div>
          {data.meanConfidence != null && (
            <div className="stat-row">
              <span className="stat-label">Mean Confidence</span>
              <span className="stat-value stat-blue">{data.meanConfidence.toFixed(3)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
