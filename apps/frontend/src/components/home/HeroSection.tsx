import SectionReveal from "@/components/common/SectionReveal";
import heroPicture from "@/assets/home/pictures/hero-pic.jpg";
import { ArrowLeft, HandHeart } from "lucide-react";
import { Link } from "react-router-dom";

export default function HeroSection() {
  return (
    <section
      id="top"
      className="relative isolate flex min-h-[92vh] items-center overflow-hidden pb-16 pt-32 lg:min-h-screen lg:pb-24 lg:pt-36"
    >
      <img
        src={heroPicture}
        alt=""
        aria-hidden="true"
        className="absolute inset-0 -z-30 h-full w-full scale-[1.03] object-cover"
      />
      <div aria-hidden="true" className="absolute inset-0 -z-20 bg-[linear-gradient(115deg,rgba(0,38,0,.76),rgba(0,0,0,.38)_52%,rgba(0,71,0,.62))]" />
      <div aria-hidden="true" className="absolute inset-x-0 bottom-0 -z-10 h-40 bg-gradient-to-t from-paper to-transparent" />

      <div className="container-page flex justify-center">
        <SectionReveal
          as="div"
          className="relative w-full max-w-3xl overflow-hidden rounded-[2.75rem] border border-white/20 bg-black/50 px-6 py-8 text-center text-white shadow-[0_32px_100px_-38px_rgba(0,0,0,.85)] backdrop-blur-xl sm:px-10 sm:py-10 lg:px-16"
        >
          <div aria-hidden="true" className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-gold/15 blur-3xl" />
          <div aria-hidden="true" className="absolute -bottom-28 -left-20 h-64 w-64 rounded-full bg-brandgreen/15 blur-3xl" />

          <img
            src="/logo white-small size.png"
            alt="نشان مرکز راهبری پژوهش و پیشرفت هوش مصنوعی"
            className="relative mx-auto h-28 w-auto max-w-[12rem] object-contain drop-shadow-[0_10px_28px_rgba(0,0,0,.65)] sm:h-32"
          />

          <p className="relative mt-3 text-xs font-bold leading-6 text-gold sm:text-sm">
            مرکز راهبری پژوهش و پیشرفت هوش مصنوعی
          </p>
          <div className="relative mx-auto mt-3 h-1 w-14 rounded-full bg-gold" />
          <h1 className="relative mt-4 font-display text-4xl font-normal leading-[1.35] tracking-[-.035em] text-white sm:text-5xl">
            هوش مصنوعی، در خدمت
            <span className="block text-gold">زبان و کتاب فارسی</span>
          </h1>
          <p className="relative mx-auto mt-4 max-w-2xl text-sm leading-8 text-white/80 sm:text-base sm:leading-9">
            ویراستار هوشمند کتاب، بازبینی متن و آماده‌سازی صفحه را شفاف‌تر
            می‌کند؛ پیشنهاد می‌دهد و تصمیم نهایی را به متخصص می‌سپارد.
          </p>

          <div className="relative mt-6 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
            <Link
              to="/editor?sample=true"
              className="btn-focus inline-flex items-center justify-center gap-2 rounded-full bg-gold px-7 py-3.5 text-sm font-extrabold text-[#003700] shadow-[0_14px_34px_-16px_rgba(187,220,18,.85)] transition hover:-translate-y-1 hover:bg-white"
            >
              تجربه دموی محصول
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <a
              href="#contact"
              className="btn-focus inline-flex items-center justify-center gap-2 rounded-full border border-gold/55 bg-black/20 px-7 py-3.5 text-sm font-bold text-white backdrop-blur-sm transition hover:-translate-y-1 hover:bg-gold/15"
            >
              <HandHeart className="h-4 w-4 text-gold" />
              مشارکت در توسعه
            </a>
          </div>
        </SectionReveal>
      </div>

      <div aria-hidden="true" className="hero-paper-tear absolute inset-x-0 bottom-0 z-20 h-12 bg-paper sm:h-16" />
    </section>
  );
}
