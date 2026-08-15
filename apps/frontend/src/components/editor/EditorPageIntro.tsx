import { Feather, Sparkles } from "lucide-react";

export default function EditorPageIntro() {
  return (
    <section className="mb-8 grid items-end gap-6 border-b border-ink/10 pb-7 lg:grid-cols-[1fr_auto]">
      <div>
        <span className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand/10 px-4 py-1.5 text-xs font-bold text-brand">
          <Sparkles className="h-3.5 w-3.5" />
          تجربه نمایشی هوش ویراستاری
        </span>
        <h1 className="editorial-title mt-4 text-4xl sm:text-5xl">میز کار ویراستار</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-subtext sm:text-base">
          متن را وارد کنید و پیشنهادهای هوشمند را مثل یادداشت‌های یک ویراستار حرفه‌ای، روی صفحه کتاب ببینید.
        </p>
      </div>
      <div className="hidden items-center gap-3 rounded-full border border-lineborder bg-card/70 px-5 py-3 text-xs font-bold text-ink lg:flex">
        <Feather className="h-4 w-4 text-brand" />
        نسخه آفلاین ارائه · داده نمایشی
      </div>
    </section>
  );
}
