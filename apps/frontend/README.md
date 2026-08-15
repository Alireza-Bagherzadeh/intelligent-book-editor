# Intelligent Book Editor — Frontend

رابط نمایشی ویراستار و صفحه‌آرای هوشمند کتاب با React، TypeScript و Vite.

## اجرای نسخه دمو

```bash
npm install
npm run dev
```

نسخه دمو به‌صورت پیش‌فرض آفلاین است: پردازش متن، نتیجه ویراستاری و دریافت خروجی با داده نمایشی اجرا می‌شوند و به Django، مدل زبانی یا Google Fonts وابسته نیستند.

برای اتصال مجدد به backend، فایل `.env` را بر اساس `.env.example` بسازید و مقدار زیر را تغییر دهید:

```env
VITE_USE_REAL_BACKEND=true
```

## کنترل کیفیت

```bash
npm run lint
npm run build
```
