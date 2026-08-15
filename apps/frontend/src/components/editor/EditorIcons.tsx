import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const commonProps = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

export function PenIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" />
    </svg>
  );
}

export function UploadIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M12 16V4" />
      <path d="m7 9 5-5 5 5" />
      <path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4" />
    </svg>
  );
}

export function CloudUploadIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M16 16l-4-4-4 4" />
      <path d="M12 12v9" />
      <path d="M20.4 17.5A5 5 0 0 0 18 8.2 7 7 0 0 0 4.3 10.7 4.5 4.5 0 0 0 5.5 19H7" />
    </svg>
  );
}

export function SparklesIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="m12 3-1.4 3.6L7 8l3.6 1.4L12 13l1.4-3.6L17 8l-3.6-1.4Z" />
      <path d="m5 14-.8 2.2L2 17l2.2.8L5 20l.8-2.2L8 17l-2.2-.8Z" />
      <path d="m19 13-1 2.5-2.5 1L18 17.5l1 2.5 1-2.5 2.5-1-2.5-1Z" />
    </svg>
  );
}

export function FileTextIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
      <path d="M8 13h8M8 17h6" />
    </svg>
  );
}

export function TrashIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M3 6h18" />
      <path d="M8 6V4h8v2" />
      <path d="m19 6-1 14H6L5 6" />
      <path d="M10 11v5M14 11v5" />
    </svg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="m5 12 4 4L19 6" />
    </svg>
  );
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12 2.5 2.5L16.5 8.5" />
    </svg>
  );
}

export function AlertCircleIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5M12 16h.01" />
    </svg>
  );
}

export function LoaderIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M21 12a9 9 0 1 1-6.2-8.6" />
    </svg>
  );
}

export function TypeIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M4 6V4h16v2" />
      <path d="M9 20h6" />
      <path d="M12 4v16" />
    </svg>
  );
}

export function BoldIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M7 4h6a4 4 0 0 1 0 8H7Z" />
      <path d="M7 12h7a4 4 0 0 1 0 8H7Z" />
    </svg>
  );
}

export function ItalicIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M10 4h8M6 20h8M14 4 10 20" />
    </svg>
  );
}

export function UnderlineIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M6 4v6a6 6 0 0 0 12 0V4" />
      <path d="M4 20h16" />
    </svg>
  );
}

export function AlignRightIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M4 6h16M9 10h11M6 14h14M11 18h9" />
    </svg>
  );
}

export function AlignCenterIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M4 6h16M7 10h10M5 14h14M8 18h8" />
    </svg>
  );
}

export function AlignLeftIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M4 6h16M4 10h11M4 14h14M4 18h9" />
    </svg>
  );
}

export function ListIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M8 6h13M8 12h13M8 18h13" />
      <path d="M3 6h.01M3 12h.01M3 18h.01" />
    </svg>
  );
}

export function UndoIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M9 7 4 12l5 5" />
      <path d="M20 17a8 8 0 0 0-8-8H4" />
    </svg>
  );
}

export function RedoIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="m15 7 5 5-5 5" />
      <path d="M4 17a8 8 0 0 1 8-8h8" />
    </svg>
  );
}

export function EraserIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="m7 21-4-4 11-11a3 3 0 0 1 4 4L7 21Z" />
      <path d="m8 12 4 4" />
      <path d="M3 21h18" />
    </svg>
  );
}

export function DownloadIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M12 3v12" />
      <path d="m7 10 5 5 5-5" />
      <path d="M5 21h14" />
    </svg>
  );
}

export function EyeIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  );
}

export function ShieldIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M12 3 5 6v5c0 4.8 2.8 8.2 7 10 4.2-1.8 7-5.2 7-10V6Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function TextQuoteIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M5 6h14M5 10h14M5 14h9" />
      <path d="M17 14h2v4h-4v-2" />
    </svg>
  );
}
export function FontFamilyIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M4 19 9 5h2l5 14" />
      <path d="M6 14h8" />
    </svg>
  );
}

export function FontSizeIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M4 7V5h8v2" />
      <path d="M8 5v14" />
      <path d="M14 10h6" />
      <path d="M17 7v6" />
    </svg>
  );
}

export function LineHeightIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M8 7h12" />
      <path d="M8 12h12" />
      <path d="M8 17h12" />
      <path d="M4 6v12" />
      <path d="m2 8 2-2 2 2" />
      <path d="m2 16 2 2 2-2" />
    </svg>
  );
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="m7 10 5 5 5-5" />
    </svg>
  );
}

export function LightbulbIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M8.2 14.5A6 6 0 1 1 15.8 14.5c-.8.7-1.3 1.5-1.5 2.5h-4.6c-.2-1-.7-1.8-1.5-2.5Z" />
    </svg>
  );
}

export function RefreshIcon(props: IconProps) {
  return (
    <svg {...commonProps} {...props}>
      <path d="M20 7h-5V2" />
      <path d="M4 17h5v5" />
      <path d="M5.2 9A8 8 0 0 1 18 5l2 2M4 17l2 2a8 8 0 0 0 12.8-4" />
    </svg>
  );
}
