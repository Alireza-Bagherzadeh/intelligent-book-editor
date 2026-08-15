import {
  EDITOR_ALLOWED_EXTENSIONS,
  EDITOR_MAX_FILE_SIZE,
} from "../data/editorContent";

export function countWords(value: string): number {
  const normalized = value.trim();
  if (!normalized) return 0;

  return normalized.split(/\s+/u).filter(Boolean).length;
}

export function formatFileSize(size: number): string {
  if (size < 1024) return `${size} بایت`;

  const kilobytes = size / 1024;
  if (kilobytes < 1024) return `${kilobytes.toFixed(1)} کیلوبایت`;

  const megabytes = kilobytes / 1024;
  return `${megabytes.toFixed(2)} مگابایت`;
}

export function validateEditorFile(file: File): string | null {
  const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;

  if (!EDITOR_ALLOWED_EXTENSIONS.includes(extension)) {
    return "فقط فایل‌های DOCX و TXT قابل بارگذاری هستند.";
  }

  if (file.size > EDITOR_MAX_FILE_SIZE) {
    return "حجم فایل نباید بیشتر از ۲۰ مگابایت باشد.";
  }

  return null;
}
