import ProductDemoPreview from "@/components/home/ProductDemoPreview";
import SectionReveal from "@/components/common/SectionReveal";

export default function ProductShowcaseSection() {
  return (
    <section
      id="product-demo"
      aria-label="پیش‌نمایش محیط ویراستار هوشمند کتاب"
      className="relative overflow-hidden bg-gradient-to-b from-brand/10 via-gold/10 to-paper py-16 dark:from-black/20 dark:via-gold/5 dark:to-paper lg:py-24"
    >
      <div
        aria-hidden="true"
        className="absolute -right-24 top-1/3 h-80 w-80 rounded-full bg-brand/10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="absolute -left-20 bottom-0 h-72 w-72 rounded-full bg-gold/15 blur-3xl"
      />

      <div className="container-page">
        <SectionReveal as="div" className="book-float relative mx-auto max-w-5xl">
          <div className="absolute -inset-4 -z-10 rotate-2 rounded-[3rem] border border-brand/25 bg-brand/20 shadow-[0_30px_90px_-42px_rgb(var(--brand)/.75)] dark:border-gold/25 dark:bg-gold/10 sm:-inset-7" />
          <div className="product-preview-shell torn-edge paper-card overflow-hidden rounded-t-[2.75rem] px-3 pb-10 pt-3 sm:px-6 sm:pt-6">
            <div className="mb-4 flex items-center justify-between px-3 text-[10px] font-bold tracking-[.2em] text-brand">
              <span>نسخه نمایشی ۱۴۰۵</span>
              <span>EDITORIAL AI</span>
            </div>
            <ProductDemoPreview />
          </div>
        </SectionReveal>
      </div>
    </section>
  );
}
