import type { ReactNode } from "react";

type MetricVariant = "purple" | "orange" | "green" | "blue";

interface ResultMetricCardProps {
  title: string;
  value: number | null;
  icon: ReactNode;
  variant: MetricVariant;
}

const variantClasses: Record<
  MetricVariant,
  { icon: string; value: string }
> = {
  purple: {
    icon: "bg-violet-50 text-violet-700 dark:bg-violet-400/20 dark:text-violet-300",
    value: "text-violet-700 dark:text-violet-300",
  },
  orange: {
    icon: "bg-amber-50 text-amber-600 dark:bg-amber-400/20 dark:text-amber-300",
    value: "text-amber-600 dark:text-amber-300",
  },
  green: {
    icon: "bg-emerald-50 text-emerald-600 dark:bg-emerald-400/20 dark:text-emerald-300",
    value: "text-emerald-600 dark:text-emerald-300",
  },
  blue: {
    icon: "bg-blue-50 text-blue-600 dark:bg-blue-400/20 dark:text-blue-300",
    value: "text-blue-600 dark:text-blue-300",
  },
};

export default function ResultMetricCard({
  title,
  value,
  icon,
  variant,
}: ResultMetricCardProps) {
  const classes = variantClasses[variant];

  return (
    <div className="rounded-2xl border border-lineborder bg-card p-3.5">
      <div className="flex items-center justify-between gap-2">
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${classes.icon}`}>
          {icon}
        </span>

        <span className={`text-lg font-extrabold ${classes.value}`}>
          {value === null ? "--" : value.toLocaleString("fa-IR")}
        </span>
      </div>

      <p className="mt-3 text-xs font-bold text-ink">{title}</p>
    </div>
  );
}
