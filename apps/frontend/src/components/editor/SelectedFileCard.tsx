import { formatFileSize } from "../../utils/editor";
import {
  CheckCircleIcon,
  FileTextIcon,
  TrashIcon,
} from "./EditorIcons";

interface SelectedFileCardProps {
  file: File;
  onRemove: () => void;
  disabled?: boolean;
}

export default function SelectedFileCard({
  file,
  onRemove,
  disabled = false,
}: SelectedFileCardProps) {
  return (
    <div className="rounded-2xl border border-lineborder bg-card p-4">
      <p className="mb-3 text-xs font-bold text-ink">فایل انتخاب‌شده</p>

      <div className="flex items-center gap-3 rounded-xl border border-lineborder bg-card p-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 dark:bg-blue-400/15 dark:text-blue-300">
          <FileTextIcon className="h-6 w-6" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold text-ink">{file.name}</p>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-subtext">
            <span>{formatFileSize(file.size)}</span>
            <span className="inline-flex items-center gap-1 font-medium text-emerald-600">
              <CheckCircleIcon className="h-3.5 w-3.5" />
              آماده برای پردازش
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          aria-label="حذف فایل"
          title="حذف فایل"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/15 dark:text-white/55 dark:hover:border-rose-400/35 dark:hover:bg-rose-400/15 dark:hover:text-rose-300"
        >
          <TrashIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
