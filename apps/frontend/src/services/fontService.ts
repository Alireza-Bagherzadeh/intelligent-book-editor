export type FontSource = "local" | "google" | "system";

export interface EditorFont {
  family: string;
  source: FontSource;
  subsets?: string[];
  variants?: string[];
}

interface GoogleFontApiItem {
  family: string;
  subsets?: string[];
  variants?: string[];
}

interface GoogleFontsApiResponse {
  items?: GoogleFontApiItem[];
}

const GOOGLE_FONTS_API_URL =
  "https://www.googleapis.com/webfonts/v1/webfonts";

export const LOCAL_FONTS: EditorFont[] = [
  { family: "Yekan Bakh", source: "local" },
  { family: "IRANYekan", source: "local" },
  { family: "Vazirmatn", source: "local" },
  { family: "IRANSans", source: "local" },
  { family: "IRANSansX", source: "local" },
  { family: "Peyda", source: "local" },
  { family: "Dana", source: "local" },
  { family: "Shabnam", source: "local" },
  { family: "Sahel", source: "local" },
  { family: "Samim", source: "local" },
  { family: "Estedad", source: "local" },
  { family: "B Yekan", source: "local" },
  { family: "B Nazanin", source: "local" },
  { family: "B Mitra", source: "local" },
  { family: "B Titr", source: "local" },
];

export const SYSTEM_FONTS: EditorFont[] = [
  { family: "Tahoma", source: "system" },
  { family: "Arial", source: "system" },
  { family: "Times New Roman", source: "system" },
  { family: "Georgia", source: "system" },
  { family: "Verdana", source: "system" },
  { family: "sans-serif", source: "system" },
  { family: "serif", source: "system" },
];

let cachedCatalog: EditorFont[] | null = null;

function normalizeFamilyName(value: string) {
  return value.trim().toLocaleLowerCase("en-US");
}

function mergeFontCatalogs(
  localFonts: EditorFont[],
  systemFonts: EditorFont[],
  googleFonts: EditorFont[],
) {
  const merged = new Map<string, EditorFont>();

  // Google first, then system, then local.
  // Local fonts intentionally win when the same family also exists in Google Fonts.
  for (const font of googleFonts) {
    merged.set(normalizeFamilyName(font.family), font);
  }

  for (const font of systemFonts) {
    merged.set(normalizeFamilyName(font.family), font);
  }

  for (const font of localFonts) {
    merged.set(normalizeFamilyName(font.family), font);
  }

  return Array.from(merged.values());
}

export async function fetchGoogleFonts(): Promise<EditorFont[]> {
  if (import.meta.env.VITE_ENABLE_REMOTE_FONTS !== "true") {
    return [];
  }

  const apiKey = import.meta.env.VITE_GOOGLE_FONTS_API_KEY?.trim();

  if (!apiKey) {
    return [];
  }

  const url = new URL(GOOGLE_FONTS_API_URL);
  url.searchParams.set("key", apiKey);
  url.searchParams.set("sort", "popularity");

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(
      `Google Fonts API error: ${response.status} ${response.statusText}`,
    );
  }

  const data = (await response.json()) as GoogleFontsApiResponse;

  return (data.items ?? []).map((font) => ({
    family: font.family,
    source: "google" as const,
    subsets: font.subsets ?? [],
    variants: font.variants ?? [],
  }));
}

export async function getFontCatalog(
  forceRefresh = false,
): Promise<EditorFont[]> {
  if (cachedCatalog && !forceRefresh) {
    return cachedCatalog;
  }

  try {
    const googleFonts = await fetchGoogleFonts();

    cachedCatalog = mergeFontCatalogs(
      LOCAL_FONTS,
      SYSTEM_FONTS,
      googleFonts,
    );

    return cachedCatalog;
  } catch (error) {
    console.warn(
      "Google Fonts catalog could not be loaded. Falling back to local/system fonts.",
      error,
    );

    cachedCatalog = mergeFontCatalogs(
      LOCAL_FONTS,
      SYSTEM_FONTS,
      [],
    );

    return cachedCatalog;
  }
}

export function findFont(
  fonts: EditorFont[],
  family: string,
): EditorFont | undefined {
  const normalized = normalizeFamilyName(family);

  return fonts.find(
    (font) => normalizeFamilyName(font.family) === normalized,
  );
}

export function loadGoogleFont(fontFamily: string) {
  const family = fontFamily.trim();

  if (!family) return;

  const id = `google-font-${family
    .toLocaleLowerCase("en-US")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")}`;

  if (document.getElementById(id)) {
    return;
  }

  const link = document.createElement("link");
  const googleFamily = family.replace(/\s+/g, "+");

  link.id = id;
  link.rel = "stylesheet";
  link.href =
    `https://fonts.googleapis.com/css2?family=${googleFamily}` +
    `:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,700&display=swap`;

  link.onerror = () => {
    console.warn(`Google Font could not be loaded: ${family}`);
    link.remove();
  };

  document.head.appendChild(link);
}

export function prepareFont(
  font: EditorFont | undefined,
  typedFamily?: string,
) {
  if (font?.source === "google") {
    loadGoogleFont(font.family);
    return;
  }

  // An arbitrary manually typed font is treated as local/system.
  // We cannot safely know whether it exists in Google Fonts without a catalog match.
  if (!font && typedFamily) {
    return;
  }
}
