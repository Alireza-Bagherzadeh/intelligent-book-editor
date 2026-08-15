import type { ProcessStatus } from "../../types/editor";
import { LoaderIcon, RefreshIcon, SparklesIcon } from "./EditorIcons";

interface ProcessingButtonProps {
  status: ProcessStatus;
  disabled: boolean;
  onClick: () => void;
}

export default function ProcessingButton({ status, disabled, onClick }: ProcessingButtonProps) {
  const content = {
    idle: { label: "آغاز ویراستاری هوشمند", icon: <SparklesIcon className="h-5 w-5" /> },
    processing: { label: "در حال خواندن و تحلیل متن...", icon: <LoaderIcon className="h-5 w-5 animate-spin" /> },
    success: { label: "تحلیل دوباره متن", icon: <RefreshIcon className="h-5 w-5" /> },
    error: { label: "تلاش دوباره", icon: <RefreshIcon className="h-5 w-5" /> },
  }[status];

  return (
    <button type="button" disabled={disabled} onClick={onClick} className="inline-flex min-h-14 w-full items-center justify-center gap-2 rounded-full bg-brand px-8 text-sm font-extrabold text-brand-foreground shadow-[0_16px_30px_-18px_rgba(138,61,35,.95)] transition hover:-translate-y-1 hover:bg-ink disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none sm:w-auto sm:min-w-72">
      {content.icon}
      {content.label}
    </button>
  );
}
