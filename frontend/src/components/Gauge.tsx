export function ProgressBar({
  label,
  value,
  max = 100,
  suffix = "%",
}: {
  label: string;
  value: number;
  max?: number;
  suffix?: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const color =
    pct >= 90
      ? "bg-red-500"
      : pct >= 70
      ? "bg-orange-500"
      : pct >= 50
      ? "bg-yellow-500"
      : "bg-green-500";

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="mono text-slate-300">
          {value.toFixed(1)}
          {suffix}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[#1a2029]">
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function CircularGauge({
  value,
  label,
}: {
  value: number;
  label?: string;
}) {
  const pct = Math.min(100, Math.max(0, value));
  const color =
    pct >= 80
      ? "text-green-400"
      : pct >= 50
      ? "text-yellow-400"
      : "text-red-400";
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center">
      <svg width="120" height="120" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="#1a2029"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          className={color}
        />
        <text
          x="50"
          y="54"
          textAnchor="middle"
          fontSize="20"
          fontWeight="bold"
          fill="currentColor"
          className="text-slate-100"
        >
          {pct.toFixed(0)}%
        </text>
      </svg>
      {label && <div className="mt-1 text-xs text-slate-400">{label}</div>}
    </div>
  );
}
