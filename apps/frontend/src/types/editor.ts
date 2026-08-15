export type EditorMode = "text" | "file";

export type ProcessStatus = "idle" | "processing" | "success" | "error";

export interface EditorMetrics {
  grammar: number;
  halfSpace: number;
  consistency: number;
  suggestions: number;
}

export interface EditorResult {
  documentId: string;
  metrics: EditorMetrics;

  /**
   * متن ساده خروجی برای شمارش واژه‌ها و نمایش جایگزین.
   */
  editedText: string;

  /**
   * HTML ساختاریافته خروجی Backend برای نمایش
   * عنوان‌ها، پاراگراف‌ها و جدول‌ها در ویرایشگر.
   */
  editedHtml: string;
  issues: EditorIssue[];

  processedAt: string;
}

export type EditorIssueCategory =
  | "half-space"
  | "spacing"
  | "punctuation"
  | "consistency"
  | "grammar"
  | "suggestion";

export interface EditorIssue {
  id?: number;

  issueCode: string;
  category: EditorIssueCategory;

  title: string;
  description: string;
  severity: string;

  startOffset: number;
  endOffset: number;

  originalSegment: string;
  suggestionText: string;
}
