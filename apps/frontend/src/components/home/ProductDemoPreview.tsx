import { Sparkles, Check, Type, AlignJustify, MoveHorizontal } from "lucide-react";
import { mockupToolbar, statsMock } from "@/data/homeContent";

const toolbarIcons = [Type, AlignJustify, MoveHorizontal];

export default function ProductDemoPreview() {
  return (
    <div className="relative w-full">
      {/* Soft glow accent */}
      <div
        aria-hidden="true"
        className="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-tr from-brand/10 via-brandgreen/5 to-gold/10 blur-2xl"
      />

      <div className="overflow-hidden rounded-2xl border border-lineborder bg-card shadow-[0_20px_60px_-20px_rgba(24,36,58,0.25)]">
        {/* Window chrome */}
        <div className="flex items-center justify-between border-b border-lineborder bg-paper/60 px-4 py-2.5">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-errred/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-gold/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-brandgreen/70" />
          </div>
          <span className="text-[11px] font-medium text-subtext">
            ویراستار هوشمند کتاب — پیش‌نمایش محیط کار
          </span>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-2 border-b border-lineborder bg-paper/40 px-4 py-3">
          {mockupToolbar.map((item, i) => {
            const Icon = toolbarIcons[i] || Type;
            return (
              <span
                key={item}
                className="inline-flex items-center gap-1.5 rounded-lg border border-lineborder bg-card px-2.5 py-1.5 text-[11px] font-medium text-subtext"
              >
                <Icon className="h-3.5 w-3.5 text-brand" />
                {item}
              </span>
            );
          })}
          <span className="mr-auto inline-flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-[11px] font-semibold text-brand-foreground">
            <Sparkles className="h-3.5 w-3.5" />
            تحلیل هوشمند
          </span>
        </div>

        {/* Body: text + suggestions */}
        <div className="grid gap-px bg-lineborder sm:grid-cols-2">
          {/* Original text */}
          <div className="bg-card p-4 sm:p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold text-ink">متن اولیه</span>
              <span className="rounded-md bg-errred/10 px-2 py-0.5 text-[10px] font-medium text-errred">
                خطا شناسایی شد
              </span>
            </div>
            <p className="text-sm leading-8 text-bodytext">
              این{" "}
              <mark className="rounded bg-errred/15 px-0.5 text-errred decoration-errred/40 underline decoration-wavy underline-offset-4">
                نرم افزار
              </mark>
              می
              <mark className="rounded bg-errred/15 px-0.5 text-errred decoration-errred/40 underline decoration-wavy underline-offset-4">
                تواند
              </mark>{" "}
              کتاب
              <mark className="rounded bg-errred/15 px-0.5 text-errred decoration-errred/40 underline decoration-wavy underline-offset-4">
                ها
              </mark>{" "}
              را سریع
              <mark className="rounded bg-errred/15 px-0.5 text-errred decoration-errred/40 underline decoration-wavy underline-offset-4">
                تر
              </mark>{" "}
              ویرایش کند{" "}
              <mark className="rounded bg-errred/15 px-0.5 text-errred">.</mark>
            </p>
          </div>

          {/* Suggestions / corrected */}
          <div className="bg-paper/40 p-4 sm:p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold text-ink">پیشنهادهای اصلاحی</span>
              <span className="rounded-md bg-brandgreen/10 px-2 py-0.5 text-[10px] font-medium text-brandgreen">
                اصلاح شد
              </span>
            </div>
            <p className="text-sm leading-8 text-bodytext">
              این{" "}
              <mark className="rounded bg-brandgreen/15 px-0.5 text-brandgreen">
                نرم‌افزار
              </mark>
              می{" "}
              <mark className="rounded bg-brandgreen/15 px-0.5 text-brandgreen">
                ‌تواند
              </mark>{" "}
              کتاب{" "}
              <mark className="rounded bg-brandgreen/15 px-0.5 text-brandgreen">
                ‌ها
              </mark>{" "}
              را سریع
              <mark className="rounded bg-brandgreen/15 px-0.5 text-brandgreen">
                ‌تر
              </mark>{" "}
              ویرایش کند{" "}
              <mark className="rounded bg-brandgreen/15 px-0.5 text-brandgreen">.</mark>
            </p>

            {/* Stats card */}
            <div className="mt-4 rounded-xl border border-lineborder bg-card p-3">
              <div className="grid grid-cols-3 gap-2 text-center">
                {statsMock.map((stat) => (
                  <div key={stat.label} className="px-1">
                    <div className="text-base font-extrabold text-ink">
                      {stat.value}
                    </div>
                    <div className="mt-0.5 text-[10px] leading-tight text-subtext">
                      {stat.label}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-center gap-1.5 rounded-lg bg-brandgreen/10 py-1.5 text-[11px] font-medium text-brandgreen">
                <Check className="h-3.5 w-3.5" />
                وضعیت: آماده بازبینی
              </div>
            </div>
          </div>
        </div>

        {/* Page preview strip */}
        <div className="border-t border-lineborder bg-paper/40 px-4 py-3">
          <div className="flex items-center gap-2 text-[11px] text-subtext">
            <span className="font-semibold text-ink">پیش‌نمایش صفحه کتاب</span>
            <span className="mr-auto">صفحه ۱ از فصل اول</span>
          </div>
          <div className="mt-2 rounded-lg border border-lineborder bg-card p-4">
            <div className="space-y-2">
              <div className="mx-auto h-1.5 w-1/2 rounded-full bg-ink/15" />
              <div className="h-1.5 w-full rounded-full bg-ink/10" />
              <div className="h-1.5 w-full rounded-full bg-ink/10" />
              <div className="h-1.5 w-11/12 rounded-full bg-ink/10" />
              <div className="h-1.5 w-full rounded-full bg-ink/10" />
              <div className="h-1.5 w-3/4 rounded-full bg-ink/10" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}