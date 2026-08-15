import type { ReactNode } from "react";
import { DownloadIcon } from "./EditorIcons";

interface OutputActionCardProps {
  title: string;
  description: string;
  icon: ReactNode;
  actionIcon?: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}

export default function OutputActionCard({
  title,
  description,
  icon,
  actionIcon,
  onClick,
  disabled = false,
}: OutputActionCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="group flex w-full items-center gap-3 rounded-2xl border border-lineborder bg-card p-3 text-right transition hover:-translate-y-0.5 hover:border-brand/30 hover:bg-brand/5 disabled:cursor-not-allowed disabled:opacity-45"
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/10 text-brand">
        {icon}
      </span>

      <span className="min-w-0 flex-1">
        <span className="block text-sm font-bold text-ink">{title}</span>
        <span className="mt-1 block text-[11px] leading-5 text-subtext">
          {description}
        </span>
      </span>

      <span className="text-subtext transition group-hover:text-brand">
        {actionIcon ?? <DownloadIcon className="h-4.5 w-4.5" />}
      </span>
    </button>
  );
}
