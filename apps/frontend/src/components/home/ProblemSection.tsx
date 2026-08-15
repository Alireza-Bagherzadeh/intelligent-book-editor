import { AlertTriangle } from "lucide-react";
import { problemCards } from "@/data/homeContent";
import SectionReveal from "@/components/common/SectionReveal";
import booksPicture from "@/assets/home/pictures/books.jpg";

export default function ProblemSection() {
  return (
    <section id="problem" className="py-16 lg:py-24">
      <div className="container-page">
        <SectionReveal className="mx-auto max-w-2xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-errred/20 bg-errred/5 px-3.5 py-1.5 text-xs font-semibold text-errred">
            <AlertTriangle className="h-3.5 w-3.5" />
            چالش امروز
          </span>
          <h2 className="mt-5 text-2xl font-extrabold leading-tight text-ink sm:text-3xl lg:text-[2rem]">
            آماده‌سازی کتاب هنوز زمان‌بر و پراشتباه است
          </h2>
          <p className="mt-4 text-base leading-8 text-subtext">
            ویراستاری و صفحه‌آرایی حرفه‌ای به دقت بالایی نیاز دارد؛ اما بخش بزرگی از این فرایند شامل کارهای تکراری، بررسی چندباره متن و اصلاح خطاهایی است که می‌توان آن‌ها را سریع‌تر شناسایی کرد.
          </p>
        </SectionReveal>

        <SectionReveal className="paper-rip mt-12 overflow-hidden rounded-[2rem] bg-card">
          <div className="grid min-h-[25rem] lg:grid-cols-[1.05fr_.95fr]">
            <div className="relative min-h-72 overflow-hidden lg:min-h-full">
              <img
                src={booksPicture}
                alt="مجموعه‌ای از کتاب‌های باز؛ نمادی از بررسی هم‌زمان نسخه‌های مختلف متن"
                loading="lazy"
                decoding="async"
                className="absolute inset-0 h-full w-full object-cover transition duration-700 hover:scale-[1.03]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-ink/45 via-transparent to-transparent" />
            </div>
            <div className="flex flex-col justify-center bg-card px-7 py-10 sm:px-10 lg:px-14">
              <span className="text-xs font-extrabold tracking-[.16em] text-brand">از پراکندگی تا یک جریان روشن</span>
              <h3 className="mt-4 text-2xl font-extrabold leading-[1.7] text-ink sm:text-3xl">
                همهٔ جزئیات کتاب، در یک میز کار واحد
              </h3>
              <p className="mt-4 text-sm leading-8 text-subtext sm:text-base">
                متن، پیشنهادهای ویرایشی، کنترل کیفیت و پیش‌نمایش صفحه کنار هم قرار می‌گیرند؛ بدون رفت‌وبرگشت میان فایل‌ها و ابزارهای پراکنده.
              </p>
              <div className="mt-7 flex flex-wrap gap-2">
                {["بررسی متمرکز", "ردگیری تغییرات", "خروجی آماده ارائه"].map((item) => (
                  <span key={item} className="rounded-full border border-brandgreen/30 bg-brandgreen/15 px-3 py-1.5 text-xs font-bold text-brandgreen">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </SectionReveal>

        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {problemCards.map((card) => {
            const Icon = card.icon;
            return (
              <SectionReveal
                key={card.title}
                as="article"
                className="group rounded-2xl border border-lineborder bg-card p-6 transition-all duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-[0_12px_40px_-16px_rgba(24,36,58,0.18)]"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-paper text-ink ring-1 ring-lineborder transition-colors group-hover:bg-brand group-hover:text-brand-foreground group-hover:ring-brand">
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-bold text-ink">
                  {card.title}
                </h3>
                <p className="mt-2 text-sm leading-7 text-subtext">
                  {card.description}
                </p>
              </SectionReveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
