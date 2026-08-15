import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import {
  correctionChips,
  type CorrectionChipColor,
} from "@/data/homeContent";
import SectionReveal from "@/components/common/SectionReveal";

// Segments of the corrected text; highlighted = changed portion
const correctedSegments = [
  { text: "نویسنده", highlight: false },
  { text: "‌ها", highlight: true },
  { text: " معمولا", highlight: false },
  { text: "ً", highlight: true },
  { text: " برای آماده", highlight: false },
  { text: "‌سازی", highlight: true },
  { text: " کتاب زمان زیادی صرف می", highlight: false },
  { text: "‌کنند", highlight: true },
  { text: ". در این فرایند ممکن است فاصله", highlight: false },
  { text: "‌ها", highlight: true },
  { text: "،", highlight: true },
  { text: " نشانه", highlight: false },
  { text: "‌گذاری", highlight: true },
  { text: " و ساختار متن یکدست نباشد.", highlight: false }
];

const chipColorMap: Record<
  CorrectionChipColor,
  string
> = {
  brand: "border-brand/30 bg-brand/5 text-brand",
  brandgreen:
    "border-brandgreen/30 bg-brandgreen/5 text-brandgreen",
  gold: "border-gold/30 bg-gold/5 text-gold",
  ink: "border-ink/20 bg-ink/5 text-ink",
};
export default function BeforeAfterSection() {
  const [showCorrections, setShowCorrections] = useState(true);

  return (
    <section id="before-after" className="bg-paper py-16 lg:py-24">
      <div className="container-page">
        <SectionReveal className="mx-auto max-w-2xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-brandgreen/30 bg-brandgreen/5 px-3.5 py-1.5 text-xs font-semibold text-brandgreen">
            دموی تعاملی
          </span>
          <h2 className="mt-5 text-2xl font-extrabold leading-tight text-ink sm:text-3xl lg:text-[2rem]">
            تفاوت را در خود متن ببینید
          </h2>
          <p className="mt-4 text-base leading-8 text-subtext">
            پیشنهادهای اصلاحی به‌صورت برجسته نمایش داده می‌شوند. این تعامل صرفاً در مرورگر و با داده نمونه است.
          </p>
        </SectionReveal>

        {/* Toggle */}
        <SectionReveal className="mt-8 flex justify-center">
          <button
            type="button"
            onClick={() => setShowCorrections((v) => !v)}
            className="btn-focus inline-flex items-center gap-2 rounded-xl border border-lineborder bg-card px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-paper"
            aria-pressed={showCorrections}
          >
            {showCorrections ? <Eye className="h-4 w-4 text-brand" /> : <EyeOff className="h-4 w-4 text-subtext" />}
            نمایش اصلاحات
            <span
              className={`mr-1 inline-flex h-5 w-9 items-center rounded-full px-0.5 transition-colors ${
                showCorrections ? "bg-brand" : "bg-lineborder"
              }`}
            >
              <span
                className={`h-4 w-4 rounded-full bg-card transition-transform ${
                  showCorrections ? "-translate-x-4" : "translate-x-0"
                }`}
              />
            </span>
          </button>
        </SectionReveal>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          {/* Original */}
          <SectionReveal as="article" className="rounded-2xl border border-lineborder bg-card p-6 lg:p-8">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-bold text-ink">متن اولیه</h3>
              <span className="rounded-md bg-errred/10 px-2.5 py-1 text-xs font-medium text-errred">
                پیش از اصلاح
              </span>
            </div>
            <p className="text-base leading-[2.2] text-bodytext">
              نویسنده ها معمولا برای آماده سازی کتاب زمان زیادی صرف میکنند . در این فرایند ممکن است فاصله ها ، نشانه گذاری و ساختار متن یکدست نباشد.
            </p>
          </SectionReveal>

          {/* Corrected */}
          <SectionReveal as="article" className="rounded-2xl border border-brandgreen/30 bg-card p-6 lg:p-8">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-bold text-ink">نسخه پیشنهادی</h3>
              <span className="rounded-md bg-brandgreen/10 px-2.5 py-1 text-xs font-medium text-brandgreen">
                پس از اصلاح
              </span>
            </div>
            <p className="text-base leading-[2.2] text-bodytext">
              {correctedSegments.map((seg, i) =>
                seg.highlight && showCorrections ? (
                  <mark
                    key={i}
                    className="rounded bg-brandgreen/15 px-0.5 text-brandgreen"
                  >
                    {seg.text}
                  </mark>
                ) : (
                  <span key={i}>{seg.text}</span>
                )
              )}
            </p>
          </SectionReveal>
        </div>

        {/* Chips */}
        <SectionReveal className="mt-8 flex flex-wrap justify-center gap-2.5">
          {correctionChips.map((chip) => (
            <span
              key={chip.label}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-medium ${chipColorMap[chip.color]}`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {chip.label}
            </span>
          ))}
        </SectionReveal>
      </div>
    </section>
  );
}