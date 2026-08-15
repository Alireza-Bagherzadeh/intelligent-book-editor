import { audienceCards } from "@/data/homeContent";
import SectionReveal from "@/components/common/SectionReveal";
import libraryPicture from "@/assets/home/pictures/library.jpg";

export default function TargetAudienceSection() {
  return (
    <section id="audience" className="bg-paper py-16 lg:py-24">
      <div className="container-page">
        <SectionReveal className="paper-rip overflow-hidden rounded-[2rem] bg-card">
          <div className="grid min-h-[25rem] lg:grid-cols-2">
            <div className="flex flex-col justify-center px-7 py-12 text-right sm:px-10 lg:px-14">
              <span className="w-fit rounded-full border border-brand/25 bg-brand/10 px-3.5 py-1.5 text-xs font-semibold text-brand">
                کاربران محصول
              </span>
              <h2 className="mt-5 text-3xl font-extrabold leading-[1.7] text-ink sm:text-4xl">
                طراحی‌شده برای زنجیره حرفه‌ای تولید کتاب
              </h2>
              <p className="mt-4 text-sm leading-8 text-subtext sm:text-base">
                از نخستین نسخهٔ نویسنده تا فایل نهایی ناشر، هر نقش همان اطلاعاتی را می‌بیند که برای تصمیم بهتر لازم دارد.
              </p>
            </div>
            <div className="relative min-h-80 overflow-hidden lg:min-h-full">
              <img
                src={libraryPicture}
                alt="راهروی کتابخانه با قفسه‌های کتاب و نور گرم"
                loading="lazy"
                decoding="async"
                className="absolute inset-0 h-full w-full object-cover transition duration-700 hover:scale-[1.03]"
              />
              <div className="absolute inset-0 bg-gradient-to-l from-transparent to-ink/20" />
            </div>
          </div>
        </SectionReveal>

        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {audienceCards.map((card) => {
            const Icon = card.icon;
            return (
              <SectionReveal
                key={card.title}
                as="article"
                className="group flex flex-col rounded-2xl border border-lineborder bg-card p-6 transition-all duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-[0_12px_40px_-16px_rgba(24,36,58,0.18)]"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-ink text-paper transition-colors group-hover:bg-brand">
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
