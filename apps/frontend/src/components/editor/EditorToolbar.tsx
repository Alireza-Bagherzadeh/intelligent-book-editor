import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";

import {
  AlignCenterIcon,
  AlignLeftIcon,
  AlignRightIcon,
  BoldIcon,
  ChevronDownIcon,
  EraserIcon,
  FontFamilyIcon,
  FontSizeIcon,
  ItalicIcon,
  LineHeightIcon,
  ListIcon,
  RedoIcon,
  UnderlineIcon,
  UndoIcon,
} from "./EditorIcons";

import {
  findFont,
  getFontCatalog,
  prepareFont,
  type EditorFont,
} from "../../services/fontService";

export type TextAlignment = "left" | "center" | "right";

export interface ActiveFormats {
  bold: boolean;
  italic: boolean;
  underline: boolean;
  unorderedList: boolean;
  alignment: TextAlignment;
}

interface EditorToolbarProps {
  disabled?: boolean;

  fontFamily: string;
  fontSize: string;
  lineHeight: string;

  onFontFamilyChange: (value: string) => void;
  onFontSizeChange: (value: string) => void;
  onLineHeightChange: (value: string) => void;

  onToggleBold: () => void;
  onToggleItalic: () => void;
  onToggleUnderline: () => void;

  onAlignLeft: () => void;
  onAlignCenter: () => void;
  onAlignRight: () => void;

  onToggleList: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onClear: () => void;

  activeFormats?: ActiveFormats;
}

interface ToolbarButtonProps {
  label: string;
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
}

interface ToolbarSelectProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  disabled?: boolean;
  icon?: ReactNode;
}

interface FontComboboxProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

const FONT_SIZE_OPTIONS = [
  "12",
  "14",
  "16",
  "18",
  "20",
  "22",
  "24",
  "28",
  "32",
  "36",
];

const LINE_HEIGHT_OPTIONS = [
  "1.2",
  "1.4",
  "1.6",
  "1.8",
  "2",
  "2.2",
  "2.5",
  "3",
];

const INITIAL_VISIBLE_FONTS = 100;
const LOAD_MORE_STEP = 100;

const DEFAULT_ACTIVE_FORMATS: ActiveFormats = {
  bold: false,
  italic: false,
  underline: false,
  unorderedList: false,
  alignment: "right",
};

function ToolbarButton({
  label,
  children,
  onClick,
  disabled = false,
  active = false,
}: ToolbarButtonProps) {
  const preserveEditorSelection = (
    event: MouseEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
  };

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      aria-pressed={active}
      onMouseDown={preserveEditorSelection}
      onClick={onClick}
      disabled={disabled}
      className={[
        "inline-flex h-9 w-9 items-center justify-center rounded-lg border transition",
        active
          ? "border-brand/30 bg-brand/10 text-brand dark:border-brand/45 dark:bg-brand/15 dark:text-brand"
          : "border-transparent text-subtext hover:bg-brand/10 hover:text-brand",
        "disabled:cursor-not-allowed disabled:opacity-40",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function ToolbarSelect({
  label,
  value,
  options,
  onChange,
  disabled = false,
  icon,
}: ToolbarSelectProps) {
  return (
    <div className="flex h-9 items-center gap-2 rounded-lg border border-lineborder bg-card px-3">
      {icon && (
        <span
          className="text-subtext"
          aria-hidden="true"
        >
          {icon}
        </span>
      )}

      <select
        aria-label={label}
        title={label}
        value={value}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="bg-transparent text-xs font-medium text-ink outline-none"
      >
        {options.map((item) => (
          <option
            key={item}
            value={item}
          >
            {item}
          </option>
        ))}
      </select>
    </div>
  );
}

function FontCombobox({
  value,
  onChange,
  disabled = false,
}: FontComboboxProps) {
  const wrapperRef =
    useRef<HTMLDivElement | null>(null);

  const [fonts, setFonts] =
    useState<EditorFont[]>([]);

  /*
   * query فقط وضعیت متن هنگام تعامل کاربر
   * با Combobox را نگهداری می‌کند.
   *
   * هنگام بسته بودن Combobox مستقیماً
   * value دریافتی از Parent نمایش داده می‌شود.
   */
  const [query, setQuery] =
    useState(value);

  const [open, setOpen] =
    useState(false);

  const [isSearching, setIsSearching] =
    useState(false);

  const [
    highlightedIndex,
    setHighlightedIndex,
  ] = useState(0);

  const [
    visibleCount,
    setVisibleCount,
  ] = useState(INITIAL_VISIBLE_FONTS);

  /*
   * چون Catalog بلافاصله هنگام Mount
   * بارگذاری می‌شود، مقدار اولیه true است.
   *
   * در نتیجه دیگر به setLoading(true)
   * داخل useEffect نیاز نداریم.
   */
  const [loading, setLoading] =
    useState(true);

  const resetSearchNavigation =
    useCallback(() => {
      setHighlightedIndex(0);
      setVisibleCount(
        INITIAL_VISIBLE_FONTS,
      );
    }, []);

  /*
   * بستن Combobox باید تمام Stateهای
   * موقت Search را نیز Reset کند.
   */
  const closeCombobox = useCallback(
    (nextQuery: string = value) => {
      setOpen(false);
      setIsSearching(false);
      setQuery(nextQuery);

      resetSearchNavigation();
    },
    [
      resetSearchNavigation,
      value,
    ],
  );

  /*
   * دریافت Catalog فونت‌ها فقط یک بار
   * پس از Mount انجام می‌شود.
   *
   * State updateها داخل callback
   * عملیات Async هستند، نه مستقیماً
   * داخل Effect.
   */
  useEffect(() => {
    let cancelled = false;

    getFontCatalog()
      .then((catalog) => {
        if (!cancelled) {
          setFonts(catalog);
        }
      })
      .catch((error: unknown) => {
        console.error(
          "Failed to load font catalog:",
          error,
        );
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  /*
   * بستن Combobox هنگام کلیک بیرون.
   *
   * setStateها داخل PointerEvent callback
   * انجام می‌شوند، بنابراین همان مشکل
   * set-state-in-effect وجود ندارد.
   */
  useEffect(() => {
    const handleOutsideClick = (
      event: PointerEvent,
    ) => {
      const wrapper =
        wrapperRef.current;

      if (
        wrapper &&
        !wrapper.contains(
          event.target as Node,
        )
      ) {
        closeCombobox();
      }
    };

    document.addEventListener(
      "pointerdown",
      handleOutsideClick,
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        handleOutsideClick,
      );
    };
  }, [closeCombobox]);

  const matchingFonts =
    useMemo(() => {
      if (!isSearching) {
        return fonts;
      }

      const normalized = query
        .trim()
        .toLocaleLowerCase("en-US");

      if (!normalized) {
        return fonts;
      }

      return fonts.filter((font) =>
        font.family
          .toLocaleLowerCase("en-US")
          .includes(normalized),
      );
    }, [
      fonts,
      query,
      isSearching,
    ]);

  const visibleFonts =
    useMemo(
      () =>
        matchingFonts.slice(
          0,
          visibleCount,
        ),
      [
        matchingFonts,
        visibleCount,
      ],
    );

  /*
   * وقتی Combobox بسته است، value
   * واقعی Parent را نمایش می‌دهیم.
   *
   * در نتیجه اگر fontFamily از بیرون
   * تغییر کند، نیازی به این Effect نیست:
   *
   * useEffect(() => {
   *   setQuery(value);
   * }, [value]);
   */
  const displayedValue =
    open ? query : value;

  const openFullList = () => {
    if (disabled) {
      return;
    }

    setOpen(true);
    setIsSearching(false);

    /*
     * Search جدید همیشه از Font
     * فعلی شروع می‌شود.
     */
    setQuery(value);

    resetSearchNavigation();
  };

  const handleQueryChange = (
    nextQuery: string,
  ) => {
    setQuery(nextQuery);

    /*
     * تایپ کاربر یعنی ورود به Search Mode.
     */
    setIsSearching(true);
    setOpen(true);

    /*
     * نتایج Search عوض شده‌اند،
     * بنابراین انتخاب Keyboard و Pagination
     * باید از ابتدا شروع شوند.
     */
    resetSearchNavigation();
  };

  const chooseFont = (
    font: EditorFont,
  ) => {
    /*
     * در صورت Google Font بودن،
     * fontService آن را Load می‌کند.
     */
    prepareFont(font);

    /*
     * Parent منبع اصلی fontFamily است.
     */
    onChange(font.family);

    /*
     * پس از انتخاب، Query نیز با همان Font
     * هماهنگ می‌شود و Search Reset می‌شود.
     */
    closeCombobox(font.family);
  };

  const commitTypedFont = () => {
    const typed = query.trim();

    if (!typed) {
      /*
       * Font خالی پذیرفته نمی‌شود.
       * به مقدار فعلی Parent برمی‌گردیم.
       */
      closeCombobox(value);
      return;
    }

    const matchedFont =
      findFont(fonts, typed);

    if (matchedFont) {
      chooseFont(matchedFont);
      return;
    }

    /*
     * ممکن است Font در Catalog نباشد
     * ولی روی سیستم کاربر نصب شده باشد.
     */
    prepareFont(
      undefined,
      typed,
    );

    onChange(typed);

    closeCombobox(typed);
  };

  const handleEscape = () => {
    closeCombobox(value);
  };

  const handleArrowDown = () => {
    setOpen(true);

    setHighlightedIndex(
      (current) =>
        Math.min(
          current + 1,
          Math.max(
            visibleFonts.length - 1,
            0,
          ),
        ),
    );
  };

  const handleArrowUp = () => {
    setHighlightedIndex(
      (current) =>
        Math.max(
          current - 1,
          0,
        ),
    );
  };

  const handleEnter = () => {
    const highlightedFont =
      visibleFonts[
        highlightedIndex
      ];

    if (
      open &&
      highlightedFont
    ) {
      chooseFont(
        highlightedFont,
      );

      return;
    }

    commitTypedFont();
  };

  const toggleDropdown = () => {
    if (open) {
      closeCombobox();
      return;
    }

    openFullList();
  };

  return (
    <div
      ref={wrapperRef}
      className="relative"
    >
      <div
        className={[
          "flex h-9 w-10 items-center rounded-lg border bg-card transition sm:w-40",
          open
            ? "border-brand/60 ring-2 ring-brand/15"
            : "border-lineborder",
          disabled
            ? "opacity-50"
            : "",
        ].join(" ")}
      >
        <FontFamilyIcon
          className="mr-2 h-4 w-4 shrink-0 text-subtext"
          aria-hidden="true"
        />

        <input
          type="text"
          aria-label="انتخاب فونت"
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          value={displayedValue}
          disabled={disabled}
          onFocus={openFullList}
          onClick={() => {
            if (!open) {
              openFullList();
            }
          }}
          onChange={(event) =>
            handleQueryChange(
              event.target.value,
            )
          }
          onKeyDown={(event) => {
            switch (event.key) {
              case "ArrowDown":
                event.preventDefault();
                handleArrowDown();
                break;

              case "ArrowUp":
                event.preventDefault();
                handleArrowUp();
                break;

              case "Enter":
                event.preventDefault();
                handleEnter();
                break;

              case "Escape":
                event.preventDefault();
                handleEscape();
                break;

              default:
                break;
            }
          }}
          className="min-w-0 flex-1 bg-transparent px-3 text-xs font-medium text-ink outline-none disabled:cursor-not-allowed"
          placeholder="نام فونت..."
        />

        <button
          type="button"
          aria-label={
            open
              ? "بستن فهرست فونت‌ها"
              : "نمایش فهرست فونت‌ها"
          }
          title={
            open
              ? "بستن فهرست فونت‌ها"
              : "نمایش فهرست فونت‌ها"
          }
          disabled={disabled}
          onMouseDown={(event) =>
            event.preventDefault()
          }
          onClick={toggleDropdown}
          className="inline-flex h-full w-9 shrink-0 items-center justify-center text-subtext hover:text-brand disabled:cursor-not-allowed"
        >
          <ChevronDownIcon
            className={[
              "h-4 w-4 transition-transform",
              open
                ? "rotate-180"
                : "",
            ].join(" ")}
          />
        </button>
      </div>

      {open && !disabled && (
        <div
          role="listbox"
          aria-label="فهرست فونت‌ها"
          className="absolute right-0 z-50 mt-1 w-72 overflow-hidden rounded-xl border border-lineborder bg-card shadow-xl sm:w-80"
        >
          <div className="border-b border-lineborder px-3 py-2 text-[10px] text-subtext">
            {loading
              ? "در حال دریافت فونت‌ها..."
              : `${matchingFonts.length.toLocaleString(
                  "fa-IR",
                )} فونت`}
          </div>

          <div className="max-h-72 overflow-y-auto p-1">
            {loading &&
            fonts.length === 0 ? (
              <div className="px-3 py-5 text-center text-xs text-subtext">
                در حال بارگذاری
                فونت‌ها...
              </div>
            ) : visibleFonts.length >
              0 ? (
              <>
                {visibleFonts.map(
                  (
                    font,
                    index,
                  ) => (
                    <button
                      key={`${font.source}-${font.family}`}
                      type="button"
                      role="option"
                      aria-selected={
                        font.family ===
                        value
                      }
                      onMouseDown={(
                        event,
                      ) =>
                        event.preventDefault()
                      }
                      onMouseEnter={() =>
                        setHighlightedIndex(
                          index,
                        )
                      }
                      onClick={() =>
                        chooseFont(
                          font,
                        )
                      }
                      className={[
                        "flex w-full items-center rounded-lg px-3 py-2 text-right text-xs transition",
                        index ===
                        highlightedIndex
                          ? "bg-brand/10 text-brand dark:bg-brand/15"
                          : "text-ink hover:bg-brand/10",
                        font.family ===
                        value
                          ? "font-bold"
                          : "",
                      ].join(" ")}
                    >
                      <span
                        className="min-w-0 flex-1 truncate"
                        style={{
                          fontFamily:
                            font.source ===
                              "google" &&
                            font.family !==
                              value
                              ? undefined
                              : font.family,
                        }}
                      >
                        {
                          font.family
                        }
                      </span>
                    </button>
                  ),
                )}

                {visibleCount <
                  matchingFonts.length && (
                  <button
                    type="button"
                    onMouseDown={(
                      event,
                    ) =>
                      event.preventDefault()
                    }
                    onClick={() =>
                      setVisibleCount(
                        (
                          current,
                        ) =>
                          current +
                          LOAD_MORE_STEP,
                      )
                    }
                    className="mt-1 w-full rounded-lg border border-dashed border-brand/30 px-3 py-2 text-xs font-bold text-brand transition hover:bg-brand/10 dark:border-brand/40"
                  >
                    نمایش فونت‌های
                    بیشتر
                  </button>
                )}
              </>
            ) : (
              <button
                type="button"
                onMouseDown={(event) =>
                  event.preventDefault()
                }
                onClick={
                  commitTypedFont
                }
                className="w-full rounded-lg px-3 py-3 text-right text-xs text-brand hover:bg-brand/10"
              >
                استفاده از «
                {query.trim()}»
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function EditorToolbar({
  disabled = false,
  fontFamily,
  fontSize,
  lineHeight,
  onFontFamilyChange,
  onFontSizeChange,
  onLineHeightChange,
  onToggleBold,
  onToggleItalic,
  onToggleUnderline,
  onAlignLeft,
  onAlignCenter,
  onAlignRight,
  onToggleList,
  onUndo,
  onRedo,
  onClear,
  activeFormats = DEFAULT_ACTIVE_FORMATS,
}: EditorToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-lineborder bg-card px-4 py-3">
      <FontCombobox
        value={fontFamily}
        onChange={
          onFontFamilyChange
        }
        disabled={disabled}
      />

      <ToolbarSelect
        label="اندازه فونت"
        value={fontSize}
        options={
          FONT_SIZE_OPTIONS
        }
        onChange={
          onFontSizeChange
        }
        disabled={disabled}
        icon={
          <FontSizeIcon className="h-7 w-4" />
        }
      />

      <ToolbarSelect
        label="فاصله خطوط"
        value={lineHeight}
        options={
          LINE_HEIGHT_OPTIONS
        }
        onChange={
          onLineHeightChange
        }
        disabled={disabled}
        icon={
          <LineHeightIcon className="h-4 w-4" />
        }
      />

      <span className="mx-1 hidden h-7 w-px bg-slate-200 sm:block" />

      <div className="flex items-center gap-0.5">
        <ToolbarButton
          label="پررنگ"
          onClick={
            onToggleBold
          }
          disabled={disabled}
          active={
            activeFormats.bold
          }
        >
          <BoldIcon className="h-4.5 w-4.5" />
        </ToolbarButton>

        <ToolbarButton
          label="مورب"
          onClick={
            onToggleItalic
          }
          disabled={disabled}
          active={
            activeFormats.italic
          }
        >
          <ItalicIcon className="h-4.5 w-4.5" />
        </ToolbarButton>

        <ToolbarButton
          label="زیرخط"
          onClick={
            onToggleUnderline
          }
          disabled={disabled}
          active={
            activeFormats.underline
          }
        >
          <UnderlineIcon className="h-4.5 w-4.5" />
        </ToolbarButton>
      </div>

      <span className="mx-1 hidden h-7 w-px bg-slate-200 sm:block" />

      <div className="flex items-center gap-0.5">
        <ToolbarButton
          label="راست‌چین"
          onClick={
            onAlignRight
          }
          disabled={disabled}
          active={
            activeFormats.alignment ===
            "right"
          }
        >
          <AlignRightIcon className="h-4.5 w-4.5" />
        </ToolbarButton>

        <ToolbarButton
          label="وسط‌چین"
          onClick={
            onAlignCenter
          }
          disabled={disabled}
          active={
            activeFormats.alignment ===
            "center"
          }
        >
          <AlignCenterIcon className="h-4.5 w-4.5" />
        </ToolbarButton>

        <ToolbarButton
          label="چپ‌چین"
          onClick={
            onAlignLeft
          }
          disabled={disabled}
          active={
            activeFormats.alignment ===
            "left"
          }
        >
          <AlignLeftIcon className="h-4.5 w-4.5" />
        </ToolbarButton>
      </div>

      <span className="mx-1 hidden h-7 w-px bg-slate-200 sm:block" />

      <ToolbarButton
        label="فهرست نشانه‌دار"
        onClick={onToggleList}
        disabled={disabled}
        active={
          activeFormats.unorderedList
        }
      >
        <ListIcon className="h-4.5 w-4.5" />
      </ToolbarButton>

      <span className="mx-1 hidden h-7 w-px bg-slate-200 sm:block" />

      <div className="flex items-center gap-0.5">
        <ToolbarButton
          label="بازگردانی"
          onClick={onUndo}
          disabled={disabled}
        >
          <UndoIcon className="h-4.5 w-4.5" />
        </ToolbarButton>

        <ToolbarButton
          label="انجام دوباره"
          onClick={onRedo}
          disabled={disabled}
        >
          <RedoIcon className="h-4.5 w-4.5" />
        </ToolbarButton>

        <ToolbarButton
          label="پاک‌کردن متن"
          onClick={onClear}
          disabled={disabled}
        >
          <EraserIcon className="h-4.5 w-4.5" />
        </ToolbarButton>
      </div>
    </div>
  );
}
