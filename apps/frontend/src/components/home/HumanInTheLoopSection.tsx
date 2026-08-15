import { ChevronDown, ChevronLeft } from "lucide-react";
import { humanLoopSteps, humanLoopPoints } from "@/data/homeContent";
import SectionReveal from "@/components/common/SectionReveal";
import readingPicture from "@/assets/home/pictures/reading.jpg";

export default function HumanInTheLoopSection() {
  return (
    <section id="human-loop" className="bg-gradient-to-b from-paper via-brand/[0.055] to-paper py-16 dark:via-black/10 lg:py-24">
      <div className="container-page">
        <SectionReveal className="mx-auto max-w-2xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-gold/30 bg-gold/5 px-3.5 py-1.5 text-xs font-semibold text-gold">
            انسان در حلقه
          </span>
          <h2 className="mt-5 text-2xl font-extrabold leading-tight text-ink sm:text-3xl lg:text-[2rem]">
            هوش مصنوعی پیشنهاد می‌دهد؛ تصمیم نهایی با متخصص است
          </h2>
          <p className="mt-4 text-base leading-8 text-subtext">
            هدف محصول جایگزین‌کردن ویراستار یا صفحه‌آرا نیست. نرم‌افزار باید کارهای تکراری را کاهش دهد، موارد مشکوک را برجسته کند و کنترل کامل تغییرات را در اختیار متخصص نگه دارد.
          </p>
        </SectionReveal>

        {/* Flow diagram */}
        <SectionReveal className="paper-rip mt-12 overflow-hidden rounded-[2rem] border border-lineborder bg-card">
          <div className="grid lg:grid-cols-[.72fr_1.28fr]">
            <div className="relative min-h-72 overflow-hidden lg:min-h-full">
              <img
                src={readingPicture}
                alt="خواننده‌ای در حال مطالعه؛ نمادی از حفظ تجربه انسانی در فرایند ویرایش"
                loading="lazy"
                decoding="async"
                className="absolute inset-0 h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-ink/65 via-ink/5 to-transparent" />
              <p className="absolute inset-x-6 bottom-7 text-sm font-bold leading-7 text-white">
                فناوری سرعت می‌دهد؛ قضاوت حرفه‌ای مسیر را تعیین می‌کند.
              </p>
            </div>
            <div className="p-5 sm:p-7 lg:p-8">
              <div className="flex flex-col items-stretch lg:flex-row lg:items-center lg:gap-2">
              {humanLoopSteps.map((step, i) => {
                const Icon = step.icon;
                return (
                  <div key={step.label} className="contents">
                    <div className="flex min-h-28 flex-1 flex-col items-center justify-center gap-2 rounded-2xl bg-paper p-4 text-center ring-1 ring-lineborder">
                      <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                        <Icon className="h-5 w-5" />
                      </span>
                      <span className="text-xs font-semibold text-ink sm:text-sm">
                        {step.label}
                      </span>
                    </div>
                    {i < humanLoopSteps.length - 1 && (
                      <span className="flex h-9 items-center justify-center text-subtext lg:h-auto lg:w-5">
                        <ChevronDown className="h-5 w-5 lg:hidden" />
                        <ChevronLeft className="hidden h-5 w-5 lg:block" />
                      </span>
                    )}
                  </div>
                );
              })}
              </div>
            </div>
          </div>
        </SectionReveal>

        {/* Points */}
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {humanLoopPoints.map((point) => (
            <SectionReveal
              key={point}
              as="div"
              className="flex items-center gap-3 rounded-xl border border-lineborder bg-card p-4"
            >
              <span className="flex h-2.5 w-2.5 shrink-0 rounded-full bg-brandgreen" />
              <span className="text-sm font-medium text-ink">{point}</span>
            </SectionReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
