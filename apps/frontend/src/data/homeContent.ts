import {
  ArrowLeftRight,
  BookOpen,
  Building2,
  Eye,
  Feather,
  LayoutTemplate,
  PenLine,
  Repeat,
  ShieldCheck,
  Shuffle,
  Sparkles,
  Type,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

export type CorrectionChipColor =
  | "brand"
  | "brandgreen"
  | "gold"
  | "ink";

interface NavigationItem {
  label: string;
  href: string;
}

interface ContentCard {
  title: string;
  description: string;
  icon: LucideIcon;
}

interface WorkflowStep {
  number: string;
  title: string;
  description: string;
}

interface HumanLoopStep {
  label: string;
  icon: LucideIcon;
}

interface CorrectionChip {
  label: string;
  color: CorrectionChipColor;
}

interface StatisticItem {
  label: string;
  value: string;
}

export const navItems: NavigationItem[] = [
  {
    label: "معرفی محصول",
    href: "#product-demo",
  },
  {
    label: "نحوه کار",
    href: "#workflow",
  },
  {
    label: "قابلیت‌ها",
    href: "#features",
  },
  {
    label: "کاربران محصول",
    href: "#audience",
  },
  {
    label: "درباره ما",
    href: "#about",
  },
];

export const problemCards: ContentCard[] = [
  {
    title: "اصلاحات تکراری",
    description:
      "بررسی دستی نیم‌فاصله، نشانه‌گذاری، فاصله‌ها و غلط‌های تایپی زمان زیادی می‌گیرد.",
    icon: Repeat,
  },
  {
    title: "ناهماهنگی متن",
    description:
      "اصطلاحات، تیترها، اعداد، فونت‌ها و ساختار فصل‌ها در طول کتاب یکدست باقی نمی‌مانند.",
    icon: Shuffle,
  },
  {
    title: "رفت‌وبرگشت زیاد",
    description:
      "فایل بارها میان نویسنده، ویراستار، صفحه‌آرا و ناشر جابه‌جا می‌شود.",
    icon: ArrowLeftRight,
  },
  {
    title: "کنترل کیفیت دشوار",
    description:
      "بسیاری از خطاها در مراحل پایانی یا حتی پس از آماده‌شدن نسخه چاپی دیده می‌شوند.",
    icon: ShieldCheck,
  },
];

export const workflowSteps: WorkflowStep[] = [
  {
    number: "۱",
    title: "متن یا فایل را وارد کنید",
    description:
      "متن خود را وارد کنید یا فایل کتاب را برای بررسی آماده سازید.",
  },
  {
    number: "۲",
    title: "پیشنهادهای هوشمند را بررسی کنید",
    description:
      "خطاهای نگارشی، فاصله‌گذاری و ناهماهنگی‌های متن در قالب پیشنهاد نمایش داده می‌شوند.",
  },
  {
    number: "۳",
    title: "نتیجه را بازبینی و آماده کنید",
    description:
      "اصلاحات را تأیید یا رد کنید و پیش‌نمایش صفحه‌آرایی‌شده کتاب را ببینید.",
  },
];

export const featureCards: ContentCard[] = [
  {
    title: "اصلاح نگارشی فارسی",
    description:
      "تشخیص فاصله‌گذاری، نیم‌فاصله، علائم نگارشی و خطاهای رایج تایپی.",
    icon: Type,
  },
  {
    title: "پیشنهاد به‌جای تغییر اجباری",
    description:
      "کاربر می‌تواند هر پیشنهاد را بررسی، تأیید یا رد کند.",
    icon: PenLine,
  },
  {
    title: "یکدست‌سازی متن",
    description:
      "شناسایی ناهماهنگی در اصطلاحات، اعداد، تیترها و الگوهای نوشتاری.",
    icon: LayoutTemplate,
  },
  {
    title: "پیش‌نمایش صفحه کتاب",
    description:
      "نمایش متن در قالب صفحات واقعی با تنظیمات فونت، حاشیه و فاصله خطوط.",
    icon: Eye,
  },
  {
    title: "گزارش کنترل کیفیت",
    description:
      "نمایش تعداد خطاها، نوع پیشنهادها و مواردی که به بازبینی انسانی نیاز دارند.",
    icon: ShieldCheck,
  },
  {
    title: "آماده برای توسعه هوش مصنوعی",
    description:
      "معماری محصول برای اتصال مدل‌های زبانی تخصصی و مدل‌های فاین‌تیون‌شده طراحی می‌شود.",
    icon: Sparkles,
  },
];

export const audienceCards: ContentCard[] = [
  {
    title: "ویراستاران",
    description:
      "کاهش کارهای تکراری و تمرکز بیشتر بر کیفیت زبان و محتوا.",
    icon: PenLine,
  },
  {
    title: "صفحه‌آراها",
    description:
      "شناسایی مشکلات ساختاری و مشاهده پیش‌نمایش صفحات پیش از خروجی نهایی.",
    icon: LayoutTemplate,
  },
  {
    title: "ناشران",
    description:
      "کنترل کیفیت منظم‌تر، کاهش رفت‌وبرگشت و مشاهده وضعیت آماده‌سازی متن.",
    icon: Building2,
  },
  {
    title: "نویسندگان",
    description:
      "دریافت بازخورد روشن‌تر و آماده‌سازی بهتر متن قبل از ورود به فرایند نشر.",
    icon: Feather,
  },
];

export const humanLoopSteps: HumanLoopStep[] = [
  {
    label: "متن اولیه",
    icon: BookOpen,
  },
  {
    label: "تحلیل هوشمند",
    icon: Sparkles,
  },
  {
    label: "پیشنهاد اصلاح",
    icon: PenLine,
  },
  {
    label: "تأیید ویراستار",
    icon: ShieldCheck,
  },
  {
    label: "نسخه نهایی",
    icon: Type,
  },
];

export const humanLoopPoints: string[] = [
  "نمایش دلیل هر پیشنهاد",
  "امکان تأیید یا رد جداگانه",
  "حفظ سبک نویسنده و شیوه‌نامه ناشر",
];

export const correctionChips: CorrectionChip[] = [
  {
    label: "نیم‌فاصله",
    color: "brand",
  },
  {
    label: "فاصله‌گذاری",
    color: "brandgreen",
  },
  {
    label: "نشانه‌گذاری",
    color: "gold",
  },
  {
    label: "یکدست‌سازی",
    color: "ink",
  },
];

export const statsMock: StatisticItem[] = [
  {
    label: "اصلاح فاصله‌گذاری",
    value: "۱۲",
  },
  {
    label: "پیشنهاد نگارشی",
    value: "۴",
  },
  {
    label: "یکدست‌سازی",
    value: "۲",
  },
];

export const mockupToolbar: string[] = [
  "فونت: یکان‌بخ",
  "اندازه: ۱۴pt",
  "فاصله خطوط: ۱.۸",
  "حاشیه: ۲.۵cm",
];

export const footerLinks: NavigationItem[] = [
  {
    label: "معرفی محصول",
    href: "#product-demo",
  },
  {
    label: "قابلیت‌ها",
    href: "#features",
  },
  {
    label: "نحوه کار",
    href: "#workflow",
  },
  {
    label: "ارتباط با ما",
    href: "#contact",
  },
];
