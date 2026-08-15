import { ArrowLeft, HandHeart } from "lucide-react";
import SectionReveal from "@/components/common/SectionReveal";
import bookPicture from "@/assets/home/pictures/book.jpg";
import { Link } from "react-router-dom";



export default function FinalCTASection() {
  return (
    <section id="contact" className="py-16 lg:py-24">
      <div className="container-page">
        <SectionReveal className="relative overflow-hidden rounded-3xl bg-ink px-6 py-14 text-center lg:px-16 lg:py-20">
          {/* Background image */}
          <img
            src={bookPicture}
            alt="کتابی باز با ورق‌های در حال حرکت"
            loading="lazy"
            decoding="async"
            className="absolute inset-0 h-full w-full object-cover"
          />
          <div
            aria-hidden="true"
            className="absolute inset-0"
            style={{ background: "linear-gradient(105deg, rgba(0,71,0,.97), rgba(0,71,0,.82) 58%, rgba(0,71,0,.6))" }}
          />

          <div className="relative mx-auto max-w-2xl">
            <h2 className="!text-[#fff8ef] text-2xl font-extrabold leading-tight sm:text-3xl lg:text-[2rem]">
              بیایید فرایند آماده‌سازی کتاب را هوشمندتر کنیم
            </h2>
            <p className="mt-4 text-base leading-8 text-[#f2e6da]/80">
              این محصول اکنون در مرحله توسعه دموی اولیه است و بازخورد ویراستاران، صفحه‌آراها و ناشران در شکل‌گیری نسخه نهایی آن نقش مهمی دارد.
            </p>

            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
              
                to="/editor"
                className="btn-focus inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand px-6 py-3.5 text-sm font-semibold text-brand-foreground shadow-sm transition-all hover:bg-brand/90 hover:shadow-lg  sm:w-auto"
              >
                
                مشاهده دموی اولیه
                <ArrowLeft className="h-4 w-4" />
              
              </Link>
              <a
                href="mailto:AIRAC.ACECR@Gmail.com"
                onClick={(e) => {
                  e.preventDefault();
                  document.querySelector("#contact")?.scrollIntoView({ behavior: "smooth", block: "end" });
                }}
                className="btn-focus inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/30 bg-white/10 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur-sm transition-colors hover:bg-white/15 sm:w-auto"
              >
                <HandHeart className="h-4 w-4" />
                همکاری در تست محصول
              </a>
            </div>
          </div>
        </SectionReveal>
      </div>
    </section>
  );
}
