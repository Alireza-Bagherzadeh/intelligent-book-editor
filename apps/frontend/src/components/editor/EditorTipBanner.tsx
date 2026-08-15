import { EDITOR_TIP_ITEMS } from "../../data/editorContent";
import {
  FileTextIcon,
  LightbulbIcon,
  PenIcon,
  SparklesIcon,
} from "./EditorIcons";

const icons = [
  <PenIcon key="pen" className="h-4.5 w-4.5" />,
  <SparklesIcon key="sparkles" className="h-4.5 w-4.5" />,
  <FileTextIcon key="file" className="h-4.5 w-4.5" />,
];

export default function EditorTipBanner() {
  return (
    <section className="mt-6 rounded-[1.75rem] border border-brand/20 bg-gradient-to-l from-brand/10 to-card px-5 py-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand text-brand-foreground">
            <LightbulbIcon className="h-6 w-6" />
          </span>

          <p className="pt-1 text-sm font-bold leading-7 text-ink">
            نکته: کنترل نهایی تغییرات همچنان در اختیار نویسنده و ویراستار باقی
            می‌ماند.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {EDITOR_TIP_ITEMS.map((item, index) => (
            <span
              key={item}
              className="inline-flex items-center gap-2 rounded-full border border-brand/15 bg-card px-3 py-2 text-xs font-semibold text-subtext"
            >
              <span className="text-brand">{icons[index]}</span>
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
