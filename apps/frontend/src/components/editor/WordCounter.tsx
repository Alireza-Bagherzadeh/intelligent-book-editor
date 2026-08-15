import { EDITOR_MAX_WORDS } from "../../data/editorContent";
import { AlertCircleIcon } from "./EditorIcons";

interface WordCounterProps {
  wordCount: number;
}

export default function WordCounter({ wordCount }: WordCounterProps) {
  const isOverLimit = wordCount > EDITOR_MAX_WORDS;

  return (
    <div className="flex flex-col gap-2 border-t border-lineborder bg-card px-5 py-3 text-xs text-subtext sm:flex-row sm:items-center sm:justify-between">
      <span
        className={`inline-flex items-center gap-2 ${
          isOverLimit ? "font-semibold text-rose-600" : ""
        }`}
      >
        <AlertCircleIcon className="h-4 w-4" />
        حداکثر {EDITOR_MAX_WORDS.toLocaleString("fa-IR")} کلمه در هر درخواست
        آزمایشی
      </span>

      <span className={isOverLimit ? "font-bold text-rose-600" : "font-medium"}>
        {wordCount.toLocaleString("fa-IR")} کلمه
      </span>
    </div>
  );
}
