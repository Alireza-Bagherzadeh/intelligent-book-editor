import { BookMarked } from "lucide-react";
import { footerLinks } from "@/data/homeContent";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer id="about" className="border-t border-lineborder bg-paper">
      <div className="container-page py-12 lg:py-16">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] lg:items-start">
          {/* Brand */}
          <div className="max-w-sm">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-paper">
                <BookMarked className="h-5 w-5" />
              </span>
              <span className="text-base font-extrabold text-ink">
                ویراستار هوشمند کتاب
              </span>
            </div>
            <p className="mt-4 text-sm leading-7 text-subtext">
              دستیار هوشمند ویراستاری و صفحه‌آرایی کتاب‌های فارسی
            </p>
          </div>

          {/* Organizational identity */}
          <div className="flex flex-col items-start rounded-3xl border border-brand/20 bg-card px-6 py-5 shadow-[0_18px_45px_-30px_rgb(var(--brand)/.7)] md:items-center">
            <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-3xl border-2 border-brand/20 bg-white p-2 shadow-[0_16px_35px_-22px_rgb(var(--brand)/.7)]">
              <img
                src="/LogoJahad.png"
                alt="لوگوی جهاد دانشگاهی"
                className="h-full w-full object-contain"
                loading="lazy"
              />
            </div>
            <div className="mt-4 h-1 w-12 rounded-full bg-gold" />
            <p className="mt-3 max-w-64 text-right text-sm font-extrabold leading-7 text-ink md:text-center">
              مرکز راهبری پژوهش و پیشرفت هوش مصنوعی
            </p>
          </div>

          {/* Links */}
          <nav className="flex flex-wrap gap-x-8 gap-y-3 md:justify-end lg:justify-self-end">
            {footerLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="btn-focus rounded-md text-sm font-medium text-subtext transition-colors hover:text-ink"
              >
                {link.label}
              </a>
            ))}
          </nav>
        </div>

        <div className="mt-10 border-t border-lineborder pt-6">
          <p className="text-xs leading-6 text-subtext">
            این محصول توسط تیم مرکز راهبری پژوهش و پیشرفت هوش مصنوعی در حال توسعه است.
          </p>
          <p className="mt-3 text-xs text-subtext">
            © {year} ویراستار هوشمند کتاب. تمام حقوق محفوظ است.
          </p>
        </div>
      </div>
    </footer>
  );
}
