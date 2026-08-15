import type { EditorMode } from "../../types/editor";
import { PenIcon, UploadIcon } from "./EditorIcons";

interface EditorModeTabsProps {
  activeMode: EditorMode;
  onModeChange: (mode: EditorMode) => void;
  disabled?: boolean;
}

const baseClass =
  "relative flex min-h-14 flex-1 items-center justify-center gap-2 border-b-2 px-5 text-sm font-bold transition-colors sm:flex-none sm:min-w-40";

export default function EditorModeTabs({
  activeMode,
  onModeChange,
  disabled = false,
}: EditorModeTabsProps) {
  return (
    <div className="flex border-b border-ink/10 bg-paper px-3 pt-3">
      <button
        type="button"
        disabled={disabled}
        onClick={() => onModeChange("text")}
        className={`${baseClass} ${
          activeMode === "text"
            ? "border-brand bg-card text-brand"
            : "border-transparent text-subtext hover:text-ink"
        } disabled:cursor-not-allowed disabled:opacity-50`}
      >
        <PenIcon className="h-5 w-5" />
        ورود متن
      </button>

      <button
        type="button"
        disabled={disabled}
        onClick={() => onModeChange("file")}
        className={`${baseClass} ${
          activeMode === "file"
            ? "border-brand bg-card text-brand"
            : "border-transparent text-subtext hover:text-ink"
        } disabled:cursor-not-allowed disabled:opacity-50`}
      >
        <UploadIcon className="h-5 w-5" />
        آپلود فایل
      </button>
    </div>
  );
}
