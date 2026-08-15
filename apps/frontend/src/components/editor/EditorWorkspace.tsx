import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  EDITOR_MAX_WORDS,
  SAMPLE_EDITOR_TEXT,
} from "../../data/editorContent";

import {
  processEditorFile,
  processEditorText,
} from "../../services/editorApi";

import type {
  EditorMode,
  EditorResult,
  ProcessStatus,
} from "../../types/editor";

import { countWords } from "../../utils/editor";

import EditorModeTabs from "./EditorModeTabs";
import FileUploadPanel from "./FileUploadPanel";
import IssueHighlightToggle from "./IssueHighlightToggle";
import OutputSidebar from "./OutputSidebar";
import ProcessingButton from "./ProcessingButton";
import TextEditorPanel from "./TextEditorPanel";

function escapeHtml(
  value: string,
): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function plainTextToHtml(
  value: string,
): string {
  if (!value.trim()) {
    return "";
  }

  return value
    .split(/\n{2,}/u)
    .map((paragraph) => {
      const safeParagraph =
        escapeHtml(paragraph).replaceAll(
          "\n",
          "<br>",
        );

      return `<p>${safeParagraph}</p>`;
    })
    .join("");
}

export default function EditorWorkspace() {
  const [searchParams] =
    useSearchParams();

  const shouldLoadSample =
    searchParams.get("sample") ===
    "true";

  const initialText =
    shouldLoadSample
      ? SAMPLE_EDITOR_TEXT
      : "";

  const [mode, setMode] =
    useState<EditorMode>("text");

  const [text, setText] =
    useState(initialText);

  const [editorHtml, setEditorHtml] =
    useState(() =>
      plainTextToHtml(initialText),
    );

  const [fontFamily, setFontFamily] =
    useState("Yekan Bakh");

  const [fontSize, setFontSize] =
    useState("14");

  const [lineHeight, setLineHeight] =
    useState("1.8");

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(null);

  const [status, setStatus] =
    useState<ProcessStatus>("idle");

  const [result, setResult] =
    useState<EditorResult | null>(
      null,
    );

  const [error, setError] =
    useState<string | null>(null);

  const [
    showIssueHighlights,
    setShowIssueHighlights,
  ] = useState(true);

  const wordCount = useMemo(
    () => countWords(text),
    [text],
  );

  const issuesCount =
    result?.issues?.length ?? 0;

  const hasValidText =
    text.trim().length > 0 &&
    wordCount <= EDITOR_MAX_WORDS;

  const hasValidFile =
    selectedFile !== null;

  const isReady =
    mode === "text"
      ? hasValidText
      : hasValidFile;

  const isProcessing =
    status === "processing";

  const resetResultState = () => {
    if (
      status !== "idle" ||
      result ||
      error
    ) {
      setStatus("idle");
      setResult(null);
      setError(null);
      setShowIssueHighlights(true);
    }
  };

  const handleModeChange = (
    nextMode: EditorMode,
  ) => {
    setMode(nextMode);
    resetResultState();
  };

  const handleTextChange = (
    nextText: string,
    nextHtml: string,
  ) => {
    setText(nextText);
    setEditorHtml(nextHtml);

    /*
     * با ویرایش دستی متن، نتیجه قبلی دیگر
     * با محتوای فعلی هماهنگ نیست.
     */
    resetResultState();
  };

  const handleFileSelect = (
    file: File,
  ) => {
    setSelectedFile(file);
    resetResultState();
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    resetResultState();
  };

  const handleProcess =
    async () => {
      if (
        !isReady ||
        isProcessing
      ) {
        return;
      }

      setStatus("processing");
      setResult(null);
      setError(null);
      setShowIssueHighlights(true);

      try {
        /*
         * Mode را قبل از پردازش نگه می‌داریم؛
         * چون بعد از پردازش فایل، Tab را به
         * حالت متن تغییر می‌دهیم.
         */
        const processingMode =
          mode;

        const nextResult =
          processingMode === "text"
            ? await processEditorText(
                text,
              )
            : await processEditorFile(
                selectedFile as File,
              );

        /*
         * اگر ورودی DOCX بوده است، متن و HTML
         * ساخته‌شده از Blockهای Backend داخل
         * ویرایشگر نمایش داده می‌شوند.
         */
        setText(
          nextResult.editedText,
        );

        setEditorHtml(
          nextResult.editedHtml,
        );

        setMode("text");

        setResult(nextResult);
        setShowIssueHighlights(true);
        setStatus("success");
      } catch (caughtError) {
        setStatus("error");

        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "پردازش متن با خطا مواجه شد.",
        );
      }
    };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <section className="paper-card overflow-hidden rounded-[2.25rem]">
        <EditorModeTabs
          activeMode={mode}
          onModeChange={
            handleModeChange
          }
          disabled={isProcessing}
        />

        <div className="p-4 sm:p-6">
          {mode === "text" ? (
            <>
              {result && (
                <IssueHighlightToggle
                  enabled={
                    showIssueHighlights
                  }
                  issuesCount={
                    issuesCount
                  }
                  onChange={
                    setShowIssueHighlights
                  }
                />
              )}

              <TextEditorPanel
                value={text}
                htmlValue={editorHtml}
                onChange={
                  handleTextChange
                }
                disabled={
                  isProcessing
                }
                fontFamily={
                  fontFamily
                }
                onFontFamilyChange={
                  setFontFamily
                }
                fontSize={
                  fontSize
                }
                onFontSizeChange={
                  setFontSize
                }
                lineHeight={
                  lineHeight
                }
                onLineHeightChange={
                  setLineHeight
                }
                showIssueHighlights={
                  Boolean(result) &&
                  showIssueHighlights
                }
              />
            </>
          ) : (
            <FileUploadPanel
              selectedFile={
                selectedFile
              }
              onFileSelect={
                handleFileSelect
              }
              onFileRemove={
                handleFileRemove
              }
              disabled={
                isProcessing
              }
            />
          )}

          <div className="mt-4 flex justify-start">
            <ProcessingButton
              status={status}
              disabled={
                !isReady ||
                isProcessing
              }
              onClick={
                handleProcess
              }
            />
          </div>
        </div>
      </section>

      <OutputSidebar
        status={status}
        result={result}
        isReady={isReady}
        error={error}
      />
    </div>
  );
}
