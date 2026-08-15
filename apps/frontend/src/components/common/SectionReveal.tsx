import type {
  ElementType,
  PropsWithChildren,
} from "react";

import useReveal from "@/hooks/useReveal";

interface SectionRevealProps
  extends PropsWithChildren {
  className?: string;
  as?: ElementType;
}

export default function SectionReveal({
  children,
  className = "",
  as: Tag = "section",
}: SectionRevealProps) {
  const { ref, visible } = useReveal();

  return (
    <Tag
      ref={ref}
      className={[
        "section-reveal",
        visible ? "is-visible" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </Tag>
  );
}