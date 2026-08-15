import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import EditorToolbar, {
  type ActiveFormats,
  type TextAlignment,
} from "./EditorToolbar";

import WordCounter from "./WordCounter";

interface TextEditorPanelProps {
  value: string;
  htmlValue: string;

  onChange: (
    plainText: string,
    html: string,
  ) => void;

  disabled?: boolean;

  fontFamily: string;

  onFontFamilyChange: (
    value: string,
  ) => void;

  fontSize: string;

  onFontSizeChange: (
    value: string,
  ) => void;

  lineHeight: string;

  onLineHeightChange: (
    value: string,
  ) => void;

  /**
   * مشخص می‌کند Highlight خطاهای ویراستاری
   * داخل متن نمایش داده شوند یا خیر.
   */
  showIssueHighlights?: boolean;
}

const EMPTY_FORMATS: ActiveFormats = {
  bold: false,
  italic: false,
  underline: false,
  unorderedList: false,
  alignment: "right",
};

export default function TextEditorPanel({
  value,
  htmlValue,
  onChange,
  disabled = false,
  fontFamily,
  onFontFamilyChange,
  fontSize,
  onFontSizeChange,
  lineHeight,
  onLineHeightChange,
  showIssueHighlights = true,
}: TextEditorPanelProps) {
  const editorRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const savedRangeRef =
    useRef<Range | null>(null);

  const [
    activeFormats,
    setActiveFormats,
  ] = useState<ActiveFormats>(
    EMPTY_FORMATS,
  );

  /**
   * محتوای contentEditable را با State
   * موجود در EditorWorkspace هماهنگ می‌کند.
   */
  const syncFromEditor =
    useCallback(() => {
      const editor =
        editorRef.current;

      if (!editor) {
        return;
      }

      const plainText =
        editor.innerText.replace(
          /\u200B/g,
          "",
        );

      onChange(
        plainText,
        editor.innerHTML,
      );
    }, [onChange]);

  /**
   * بررسی می‌کند Selection فعلی داخل
   * همین ویرایشگر قرار داشته باشد.
   */
  const selectionBelongsToEditor =
    useCallback(
      (range: Range) => {
        const editor =
          editorRef.current;

        if (!editor) {
          return false;
        }

        const container =
          range.commonAncestorContainer;

        return (
          container === editor ||
          editor.contains(container)
        );
      },
      [],
    );

  /**
   * محل فعلی Cursor یا Selection را ذخیره می‌کند
   * تا بعد از کلیک روی Toolbar از بین نرود.
   */
  const saveSelection =
    useCallback(() => {
      const selection =
        window.getSelection();

      if (
        !selection ||
        selection.rangeCount === 0
      ) {
        return;
      }

      const range =
        selection.getRangeAt(0);

      if (
        selectionBelongsToEditor(
          range,
        )
      ) {
        savedRangeRef.current =
          range.cloneRange();
      }
    }, [selectionBelongsToEditor]);

  /**
   * Cursor یا Selection ذخیره‌شده را
   * قبل از اجرای دستور Toolbar برمی‌گرداند.
   */
  const restoreSelection =
    useCallback(() => {
      const editor =
        editorRef.current;

      if (!editor) {
        return;
      }

      editor.focus();

      const savedRange =
        savedRangeRef.current;

      if (!savedRange) {
        return;
      }

      const selection =
        window.getSelection();

      if (!selection) {
        return;
      }

      selection.removeAllRanges();
      selection.addRange(
        savedRange,
      );
    }, []);

  const detectAlignment =
    useCallback(
      (): TextAlignment => {
        try {
          if (
            document.queryCommandState(
              "justifyCenter",
            )
          ) {
            return "center";
          }

          if (
            document.queryCommandState(
              "justifyLeft",
            )
          ) {
            return "left";
          }

          return "right";
        } catch {
          return "right";
        }
      },
      [],
    );

  const refreshActiveFormats =
    useCallback(() => {
      try {
        setActiveFormats({
          bold:
            document.queryCommandState(
              "bold",
            ),

          italic:
            document.queryCommandState(
              "italic",
            ),

          underline:
            document.queryCommandState(
              "underline",
            ),

          unorderedList:
            document.queryCommandState(
              "insertUnorderedList",
            ),

          alignment:
            detectAlignment(),
        });
      } catch {
        setActiveFormats(
          EMPTY_FORMATS,
        );
      }
    }, [detectAlignment]);

  const runCommand = useCallback(
    (
      command: string,
      commandValue?: string,
    ) => {
      if (disabled) {
        return;
      }

      restoreSelection();

      try {
        document.execCommand(
          "styleWithCSS",
          false,
          "true",
        );

        document.execCommand(
          command,
          false,
          commandValue,
        );
      } finally {
        saveSelection();
        refreshActiveFormats();
        syncFromEditor();
      }
    },
    [
      disabled,
      refreshActiveFormats,
      restoreSelection,
      saveSelection,
      syncFromEditor,
    ],
  );

  const handleFontFamilyChange =
    useCallback(
      (nextFont: string) => {
        onFontFamilyChange(
          nextFont,
        );

        if (
          savedRangeRef.current
        ) {
          runCommand(
            "fontName",
            nextFont,
          );
        }
      },
      [
        onFontFamilyChange,
        runCommand,
      ],
    );

  const clearEditor =
    useCallback(() => {
      if (disabled) {
        return;
      }

      const editor =
        editorRef.current;

      if (!editor) {
        return;
      }

      editor.innerHTML = "";

      savedRangeRef.current =
        null;

      setActiveFormats(
        EMPTY_FORMATS,
      );

      onChange("", "");

      editor.focus();
    }, [disabled, onChange]);

  /**
   * وقتی Preview ساخته‌شده در editorApi.ts
   * از طریق EditorWorkspace تغییر کند،
   * HTML جدید داخل contentEditable قرار می‌گیرد.
   */
  useEffect(() => {
    const editor =
      editorRef.current;

    if (!editor) {
      return;
    }

    if (
      editor.innerHTML !==
      htmlValue
    ) {
      editor.innerHTML =
        htmlValue;
    }
  }, [htmlValue]);

  /**
   * وضعیت Formatting متن انتخاب‌شده
   * را با Toolbar هماهنگ می‌کند.
   */
  useEffect(() => {
    const handleSelectionChange =
      () => {
        const selection =
          window.getSelection();

        if (
          !selection ||
          selection.rangeCount === 0
        ) {
          return;
        }

        const range =
          selection.getRangeAt(0);

        if (
          selectionBelongsToEditor(
            range,
          )
        ) {
          savedRangeRef.current =
            range.cloneRange();

          refreshActiveFormats();
        }
      };

    document.addEventListener(
      "selectionchange",
      handleSelectionChange,
    );

    return () => {
      document.removeEventListener(
        "selectionchange",
        handleSelectionChange,
      );
    };
  }, [
    refreshActiveFormats,
    selectionBelongsToEditor,
  ]);

  const isEmpty =
    value.trim().length === 0;

  const wordCount =
    value.trim()
      ? value
          .trim()
          .split(/\s+/u)
          .length
      : 0;

  return (
    <div className="overflow-hidden rounded-[1.75rem] border border-lineborder bg-card shadow-inner">
      <EditorToolbar
        disabled={disabled}
        fontFamily={fontFamily}
        fontSize={fontSize}
        lineHeight={lineHeight}
        onFontFamilyChange={
          handleFontFamilyChange
        }
        onFontSizeChange={
          onFontSizeChange
        }
        onLineHeightChange={
          onLineHeightChange
        }
        onToggleBold={() =>
          runCommand("bold")
        }
        onToggleItalic={() =>
          runCommand("italic")
        }
        onToggleUnderline={() =>
          runCommand("underline")
        }
        onAlignLeft={() =>
          runCommand(
            "justifyLeft",
          )
        }
        onAlignCenter={() =>
          runCommand(
            "justifyCenter",
          )
        }
        onAlignRight={() =>
          runCommand(
            "justifyRight",
          )
        }
        onToggleList={() =>
          runCommand(
            "insertUnorderedList",
          )
        }
        onUndo={() =>
          runCommand("undo")
        }
        onRedo={() =>
          runCommand("redo")
        }
        onClear={clearEditor}
        activeFormats={
          activeFormats
        }
      />

      <div className="relative">
        {isEmpty && (
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-6 top-5 text-[15px] text-slate-300"
          >
            متن خام کتاب را اینجا تایپ یا پیست کنید...
          </div>
        )}

        <div
          ref={editorRef}
          role="textbox"
          aria-multiline="true"
          aria-label="متن کتاب"
          contentEditable={
            !disabled
          }
          suppressContentEditableWarning
          onInput={
            syncFromEditor
          }
          onMouseUp={
            saveSelection
          }
          onKeyUp={
            saveSelection
          }
          onFocus={
            saveSelection
          }
          className={[
            /*
             * ارتفاع و Scroll
             */
            "min-h-[360px] max-h-[60vh] w-full overflow-y-auto overscroll-contain",

            /*
             * ظاهر اصلی Editor
             */
            "bg-card px-6 py-7 text-bodytext outline-none sm:px-10",
            "selection:bg-brand/15 selection:text-ink",

            /*
             * فعال یا غیرفعال کردن Highlightها
             * بدون تغییر دادن خود HTML.
             */
            showIssueHighlights
              ? "editor-show-issues"
              : "editor-hide-issues",

            /*
             * Paragraphs
             */
            "[&_p]:my-2",

            /*
             * Headings returned by Backend
             */
            "[&_h1]:my-5 [&_h1]:text-2xl [&_h1]:font-extrabold [&_h1]:leading-relaxed [&_h1]:text-ink",

            "[&_h2]:my-4 [&_h2]:text-xl [&_h2]:font-extrabold [&_h2]:leading-relaxed [&_h2]:text-ink",

            "[&_h3]:my-3 [&_h3]:text-lg [&_h3]:font-bold [&_h3]:text-ink",

            "[&_h4]:my-3 [&_h4]:text-base [&_h4]:font-bold [&_h4]:text-ink",

            "[&_h5]:my-2 [&_h5]:font-bold",

            "[&_h6]:my-2 [&_h6]:font-semibold",

            /*
             * Lists
             */
            "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:pr-7",

            "[&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pr-7",

            "[&_li]:my-1 [&_li]:pr-1",

            /*
             * Tables returned by Backend
             */
            "[&_.editor-table-wrapper]:my-5",

            "[&_.editor-table-wrapper]:max-w-full",

            "[&_.editor-table-wrapper]:overflow-x-auto",

            "[&_table]:w-full",

            "[&_table]:border-collapse",

            "[&_table]:bg-card",

            "[&_td]:min-w-28",

            "[&_td]:border",

            "[&_td]:border-lineborder",

            "[&_td]:px-3",

            "[&_td]:py-2",

            "[&_td]:align-top",

            "[&_tr:first-child_td]:bg-paper",

            "[&_tr:first-child_td]:font-bold",

            disabled
              ? "cursor-not-allowed bg-paper opacity-80"
              : "",
          ].join(" ")}
          style={{
            direction: "rtl",
            textAlign: "right",
            fontFamily,
            fontSize:
              `${fontSize}px`,
            lineHeight,
            whiteSpace:
              "pre-wrap",
            wordBreak:
              "break-word",
          }}
        />
      </div>

      <WordCounter
        wordCount={wordCount}
      />
    </div>
  );
}
