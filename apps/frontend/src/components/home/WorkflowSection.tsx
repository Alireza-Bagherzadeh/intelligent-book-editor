import { workflowSteps } from "@/data/homeContent";
import SectionReveal from "@/components/common/SectionReveal";

export default function WorkflowSection() {
  return (
    <section id="workflow" className="bg-paper py-16 lg:py-24">
      <div className="container-page">
        <SectionReveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-extrabold leading-tight text-ink sm:text-3xl lg:text-[2rem]">
            از ورود متن تا پیش‌نمایش کتاب در سه گام
          </h2>
          <p className="mt-4 text-base leading-8 text-subtext">
            فرایندی ساده و شفاف که کنترل کامل در دست متخصص باقی می‌ماند.
          </p>
        </SectionReveal>

        <div className="relative mt-14">
          {/* Connecting line (desktop) */}
          <div
            aria-hidden="true"
            className="absolute right-[16.66%] left-[16.66%] top-8 hidden h-px bg-gradient-to-l from-lineborder via-brand/30 to-lineborder lg:block"
          />

          <div className="grid gap-8 lg:grid-cols-3">
            {workflowSteps.map((step) => (
              <SectionReveal
                key={step.number}
                as="article"
                className="relative flex flex-col items-center text-center lg:items-start lg:text-right"
              >
                <span className="flex h-16 w-16 items-center justify-center rounded-2xl border border-lineborder bg-card text-xl font-extrabold text-brand shadow-sm">
                  {step.number}
                </span>
                <h3 className="mt-5 text-lg font-bold text-ink">
                  {step.title}
                </h3>
                <p className="mt-2 max-w-xs text-sm leading-7 text-subtext">
                  {step.description}
                </p>
              </SectionReveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}