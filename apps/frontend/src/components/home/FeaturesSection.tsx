import { featureCards } from "@/data/homeContent";
import SectionReveal from "@/components/common/SectionReveal";

export default function FeaturesSection() {
  return (
    <section id="features" className="bg-brand/[0.045] py-16 dark:bg-black/10 lg:py-24">
      <div className="container-page">
        <SectionReveal className="mx-auto max-w-2xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/5 px-3.5 py-1.5 text-xs font-semibold text-brand">
            قابلیت‌ها
          </span>
          <h2 className="mt-5 text-2xl font-extrabold leading-tight text-ink sm:text-3xl lg:text-[2rem]">
            ابزارهایی برای یک فرایند دقیق‌تر و سریع‌تر
          </h2>
        </SectionReveal>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {featureCards.map((feature) => {
            const Icon = feature.icon;
            return (
              <SectionReveal
                key={feature.title}
                as="article"
                className="group rounded-2xl border border-lineborder bg-card p-6 transition-all duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-[0_12px_40px_-16px_rgba(24,36,58,0.18)]"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand/10 text-brand transition-colors group-hover:bg-brand group-hover:text-brand-foreground">
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-bold text-ink">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-7 text-subtext">
                  {feature.description}
                </p>
              </SectionReveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
