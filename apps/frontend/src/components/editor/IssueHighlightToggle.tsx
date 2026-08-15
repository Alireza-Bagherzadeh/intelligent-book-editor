interface IssueHighlightToggleProps {
  enabled: boolean;
  issuesCount: number;
  onChange: (enabled: boolean) => void;
}

export default function IssueHighlightToggle({
  enabled,
  issuesCount,
  onChange,
}: IssueHighlightToggleProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-lineborder bg-card px-4 py-3">
      <div>
        <p className="text-sm font-extrabold text-ink">
          نمایش اصلاحات
        </p>

        <p className="mt-1 text-xs text-subtext">
          {issuesCount > 0
            ? `${issuesCount} مورد پیشنهادی در متن شناسایی شده است.`
            : "اصلاحی برای نمایش وجود ندارد."}
        </p>
      </div>

      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        disabled={issuesCount === 0}
        onClick={() =>
          onChange(!enabled)
        }
        className={[
          "relative h-7 w-12 rounded-full transition",
          enabled
            ? "bg-brand"
            : "bg-slate-300 dark:bg-white/20",
          issuesCount === 0
            ? "cursor-not-allowed opacity-50"
            : "cursor-pointer",
        ].join(" ")}
      >
        <span
          className={[
            "absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition dark:bg-[#fff8ef]",
            enabled
              ? "right-1"
              : "right-6",
          ].join(" ")}
        />
      </button>

      <div className="flex w-full flex-wrap gap-2 border-t border-lineborder pt-3">
        <IssueLegend
          label="نیم‌فاصله"
          category="half-space"
        />

        <IssueLegend
          label="فاصله‌گذاری"
          category="spacing"
        />

        <IssueLegend
          label="نشانه‌گذاری"
          category="punctuation"
        />

        <IssueLegend
          label="یکدست‌سازی"
          category="consistency"
        />

        <IssueLegend
          label="نگارشی"
          category="grammar"
        />
      </div>
    </div>
  );
}

function IssueLegend({
  label,
  category,
}: {
  label: string;
  category: string;
}) {
  return (
    <span
      className="editor-issue-legend"
      data-issue-category={category}
    >
      <span className="editor-issue-legend-dot" />

      {label}
    </span>
  );
}
