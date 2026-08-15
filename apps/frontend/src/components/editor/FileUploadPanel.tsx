import {
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
} from "react";
import {
  EDITOR_ALLOWED_EXTENSIONS,
} from "../../data/editorContent";
import { validateEditorFile } from "../../utils/editor";
import {
  AlertCircleIcon,
  CloudUploadIcon,
  UploadIcon,
} from "./EditorIcons";
import SelectedFileCard from "./SelectedFileCard";

interface FileUploadPanelProps {
  selectedFile: File | null;
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  disabled?: boolean;
}

export default function FileUploadPanel({
  selectedFile,
  onFileSelect,
  onFileRemove,
  disabled = false,
}: FileUploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleFile = (file?: File) => {
    if (!file || disabled) return;

    const error = validateEditorFile(file);
    setValidationError(error);

    if (!error) {
      onFileSelect(file);
    }
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files?.[0]);
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex min-h-[345px] flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
          isDragging
            ? "border-brand bg-brand/10"
            : "border-brand/25 bg-gradient-to-b from-card to-paper"
        } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
      >
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-brand/10 text-brand">
          <CloudUploadIcon className="h-11 w-11" />
        </div>

        <h2 className="mt-5 text-xl font-extrabold text-ink">
          فایل خود را اینجا رها کنید
        </h2>

        <p className="mt-2 max-w-md text-sm leading-7 text-slate-500">
          فایل Word یا متن ساده را برای بررسی، ویرایش و آماده‌سازی کتاب بارگذاری
          کنید.
        </p>

        <p className="mt-2 text-xs text-slate-400">
          فرمت‌های مجاز: {EDITOR_ALLOWED_EXTENSIONS.join("، ")} · حداکثر حجم:
          ۲۰ مگابایت
        </p>

        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          className="mt-6 inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-brand px-7 text-sm font-bold text-brand-foreground shadow-lg shadow-brand/20 transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-50"
        >
          <UploadIcon className="h-5 w-5" />
          انتخاب فایل از سیستم
        </button>

        <span className="mt-3 text-xs text-slate-400">
          یا فایل را از پوشه خود بکشید و در این بخش رها کنید
        </span>

        <input
          ref={inputRef}
          type="file"
          accept=".docx,.txt"
          disabled={disabled}
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      {validationError && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
        >
          <AlertCircleIcon className="h-5 w-5 shrink-0" />
          {validationError}
        </div>
      )}

      {selectedFile && (
        <SelectedFileCard
          file={selectedFile}
          disabled={disabled}
          onRemove={() => {
            setValidationError(null);
            onFileRemove();
          }}
        />
      )}
    </div>
  );
}
