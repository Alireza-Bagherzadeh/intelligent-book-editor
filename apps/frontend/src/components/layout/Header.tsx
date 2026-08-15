import { useEffect, useState } from "react";
import { Menu, Moon, Sparkles, Sun, X } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { navItems } from "@/data/homeContent";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  const savedTheme = window.localStorage.getItem("book-editor-theme");
  if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const location = useLocation();
  const isEditorPage = location.pathname === "/editor";

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 18);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("book-editor-theme", theme);
  }, [theme]);

  const navHref = (href: string) => (isEditorPage ? `/${href}` : href);
  const toggleTheme = () => setTheme((value) => (value === "light" ? "dark" : "light"));

  return (
    <header className={`fixed inset-x-0 top-0 z-50 px-4 transition-all duration-300 ${scrolled ? "pt-3" : "pt-5"}`}>
      <div className="container-page flex h-16 items-center justify-between rounded-full border border-lineborder bg-card/90 px-4 shadow-[0_16px_45px_-28px_rgb(var(--ink)/.65)] backdrop-blur-xl transition-all lg:px-6">
        <Link to="/" className="btn-focus flex items-center gap-3 rounded-full" aria-label="ویراستار هوشمند کتاب">
          <span className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-full border border-brand/20 bg-white p-1.5 shadow-sm">
            <img src="/LogoJahad.png" alt="لوگوی جهاد دانشگاهی" className="h-full w-full object-contain" />
          </span>
          <span className="hidden leading-tight sm:block">
            <span className="block text-sm font-extrabold text-ink">ویراستار هوشمند کتاب</span>
            <span className="mt-1 hidden text-[9px] font-semibold text-subtext xl:block">مرکز راهبری پژوهش و پیشرفت هوش مصنوعی</span>
          </span>
        </Link>

        {!isEditorPage && (
          <nav className="hidden items-center gap-5 lg:flex">
            {navItems.slice(0, 4).map((item) => (
              <a key={item.href} href={item.href} className="text-xs font-semibold text-subtext transition hover:text-brand">
                {item.label}
              </a>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            className="btn-focus flex h-10 w-10 items-center justify-center rounded-full border border-lineborder bg-paper text-ink transition hover:-translate-y-0.5 hover:bg-brand hover:text-brand-foreground"
            aria-label={theme === "light" ? "فعال‌کردن حالت تیره" : "فعال‌کردن حالت روشن"}
            title={theme === "light" ? "حالت تیره" : "حالت روشن"}
          >
            {theme === "light" ? <Moon className="h-[18px] w-[18px]" /> : <Sun className="h-[18px] w-[18px]" />}
          </button>

          <div className="hidden items-center gap-3 lg:flex">
            {isEditorPage ? (
              <Link to="/" className="rounded-full border border-lineborder px-5 py-2 text-xs font-bold text-ink transition hover:bg-ink hover:text-paper">بازگشت به معرفی</Link>
            ) : (
              <Link to="/editor?sample=true" className="inline-flex items-center gap-2 rounded-full bg-brand px-5 py-2.5 text-xs font-bold text-brand-foreground shadow-[0_10px_26px_-14px_rgb(var(--brand)/.9)] transition hover:-translate-y-0.5 hover:bg-ink hover:text-paper">
                <Sparkles className="h-4 w-4" />
                اجرای دموی هوشمند
              </Link>
            )}
          </div>

          <button type="button" onClick={() => setOpen((value) => !value)} className="flex h-10 w-10 items-center justify-center rounded-full border border-lineborder text-ink lg:hidden" aria-label={open ? "بستن منو" : "باز کردن منو"}>
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="container-page mt-2 lg:hidden">
          <nav className="paper-card flex flex-col gap-1 rounded-[1.75rem] p-3">
            {navItems.slice(0, 4).map((item) => (
              <a key={item.href} href={navHref(item.href)} onClick={() => setOpen(false)} className="rounded-2xl px-4 py-3 text-sm font-semibold text-ink hover:bg-brand/10">{item.label}</a>
            ))}
            <Link to="/editor?sample=true" onClick={() => setOpen(false)} className="mt-2 rounded-2xl bg-brand px-4 py-3 text-center text-sm font-bold text-brand-foreground">اجرای دمو</Link>
          </nav>
        </div>
      )}
    </header>
  );
}
