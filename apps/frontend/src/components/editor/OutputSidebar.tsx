import { useState } from "react";

import { downloadFinalDocument } from "../../services/editorApi";
import type {
  EditorResult,
  ProcessStatus,
} from "../../types/editor";

import {
  CheckCircleIcon,
  EyeIcon,
  PenIcon,
  ShieldIcon,
  SparklesIcon,
  TextQuoteIcon,
} from "./EditorIcons";

import OutputActionCard from "./OutputActionCard";
import ProcessingStatus from "./ProcessingStatus";
import ResultMetricCard from "./ResultMetricCard";

interface OutputSidebarProps {
  status: ProcessStatus;
  result: EditorResult | null;
  isReady: boolean;
  error: string | null;
}

export default function OutputSidebar({
  status,
  result,
  isReady,
  error,
}: OutputSidebarProps) {
  const [isDownloading, setIsDownloading] =
    useState(false);

  const [downloadError, setDownloadError] =
    useState<string | null>(null);

  const isSuccess =
    status === "success" && Boolean(result);

  const metrics = result?.metrics ?? null;

  const handleDownloadWord = async () => {
    if (!result?.documentId || isDownloading) {
      return;
    }

    try {
      setIsDownloading(true);
      setDownloadError(null);

      await downloadFinalDocument(
        result.documentId,
      );
    } catch (caughtError) {
      console.error(caughtError);

      setDownloadError(
        caughtError instanceof Error
          ? caughtError.message
          : "دانلود فایل با خطا مواجه شد.",
      );
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <aside className="paper-card self-start rounded-[2.25rem] p-5 lg:sticky lg:top-24">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="editorial-title text-2xl">
          دریافت خروجی
        </h2>

        <ProcessingStatus
          status={status}
          isReady={isReady}
        />
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <ResultMetricCard
          title="خطای نگارشی"
          value={metrics?.grammar ?? null}
          icon={
            <PenIcon className="h-4.5 w-4.5" />
          }
          variant="purple"
        />

        <ResultMetricCard
          title="نیم‌فاصله"
          value={metrics?.halfSpace ?? null}
          icon={
            <TextQuoteIcon className="h-4.5 w-4.5" />
          }
          variant="orange"
        />

        <ResultMetricCard
          title="یکدست‌سازی"
          value={metrics?.consistency ?? null}
          icon={
            <ShieldIcon className="h-4.5 w-4.5" />
          }
          variant="blue"
        />

        <ResultMetricCard
          title="پیشنهادها"
          value={metrics?.suggestions ?? null}
          icon={
            <SparklesIcon className="h-4.5 w-4.5" />
          }
          variant="green"
        />
      </div>

      {status === "processing" && (
        <div className="mt-4 rounded-2xl border border-brand/20 bg-brand/5 p-4 dark:border-brand/35 dark:bg-brand/10">
          <div className="mb-2 flex items-center justify-between text-xs font-bold text-brand">
            <span>تحلیل هوشمند متن</span>
            <span>در حال انجام</span>
          </div>

          <div className="h-2 overflow-hidden rounded-full bg-brand/10 dark:bg-white/10">
            <div className="h-full w-2/3 animate-pulse rounded-full bg-brand" />
          </div>

          <p className="mt-2 text-[11px] leading-5 text-brand/80 dark:text-white/65">
            شناسایی خطاها، ناهماهنگی‌ها و
            پیشنهادهای اصلاحی در حال انجام است.
          </p>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs leading-6 text-rose-700">
          {error}
        </div>
      )}

      {downloadError && (
        <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs leading-6 text-rose-700">
          {downloadError}
        </div>
      )}

      <div className="mt-4 space-y-2.5">
        <OutputActionCard
          title={
            isDownloading
              ? "در حال آماده‌سازی فایل..."
              : "دانلود فایل نهایی Word"
          }
          description={
            isDownloading
              ? "در حال دریافت خروجی از سرور"
              : "دریافت نسخه ویرایش‌شده در قالب Word"
          }
          icon={
            <span
              className="text-base font-black text-blue-700"
              aria-hidden
            >
              W
            </span>
          }
          disabled={
            !isSuccess || isDownloading
          }
          onClick={handleDownloadWord}
        />

        <OutputActionCard
          title="گزارش تغییرات PDF"
          description="این قابلیت در نسخه بعدی فعال می‌شود"
          icon={
            <span
              className="text-xs font-black text-rose-600"
              aria-hidden
            >
              PDF
            </span>
          }
          disabled
          onClick={() => undefined}
        />

        <OutputActionCard
          title="مشاهده آنلاین تغییرات"
          description="این قابلیت در نسخه بعدی فعال می‌شود"
          icon={
            <EyeIcon className="h-5 w-5" />
          }
          actionIcon={
            <EyeIcon className="h-4.5 w-4.5" />
          }
          disabled
          onClick={() => undefined}
        />
      </div>

      <div className="mt-4 rounded-2xl border border-lineborder bg-card p-4">
        <h3 className="text-sm font-extrabold text-ink">
          خروجی نهایی شامل
        </h3>

        <ul className="mt-3 grid gap-2 text-xs text-subtext">
          {[
            "فایل ویرایش‌شده",
            "گزارش تفصیلی اصلاحات",
            "پیش‌نمایش آنلاین",
          ].map((item) => (
            <li
              key={item}
              className="flex items-center gap-2"
            >
              <CheckCircleIcon className="h-4 w-4 text-emerald-600" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
