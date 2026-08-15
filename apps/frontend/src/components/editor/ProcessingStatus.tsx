import type { ProcessStatus } from "../../types/editor";
import {
  AlertCircleIcon,
  CheckCircleIcon,
  LoaderIcon,
} from "./EditorIcons";

interface ProcessingStatusProps {
  status: ProcessStatus;
  isReady: boolean;
}

export default function ProcessingStatus({
  status,
  isReady,
}: ProcessingStatusProps) {
  if (status === "processing") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-3 py-1.5 text-[11px] font-bold text-brand dark:border-brand/45 dark:bg-brand/15">
        <LoaderIcon className="h-3.5 w-3.5 animate-spin" />
        در حال پردازش
      </span>
    );
  }

  if (status === "success") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[11px] font-bold text-emerald-700 dark:border-emerald-400/35 dark:bg-emerald-400/15 dark:text-emerald-300">
        <CheckCircleIcon className="h-3.5 w-3.5" />
        پردازش تکمیل شد
      </span>
    );
  }

  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-1.5 text-[11px] font-bold text-rose-700 dark:border-rose-400/35 dark:bg-rose-400/15 dark:text-rose-300">
        <AlertCircleIcon className="h-3.5 w-3.5" />
        خطا در پردازش
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[11px] font-bold ${
        isReady
          ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-400/35 dark:bg-emerald-400/15 dark:text-emerald-300"
          : "border-slate-200 bg-slate-50 text-slate-500 dark:border-white/15 dark:bg-white/[0.06] dark:text-white/55"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${
          isReady ? "bg-emerald-500" : "bg-slate-300"
        }`}
      />
      {isReady ? "آماده برای پردازش" : "در انتظار محتوا"}
    </span>
  );
}
