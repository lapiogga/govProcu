import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--color-primary)] text-[var(--color-primary-fg)]",
        secondary:
          "bg-[var(--color-bg-muted)] text-[var(--color-fg)]",
        outline:
          "border border-[var(--color-border)] text-[var(--color-fg)]",
        success:
          "bg-[var(--color-success)] text-white",
        warning:
          "bg-[var(--color-warning)] text-white",
        danger:
          "bg-[var(--color-danger)] text-white",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant, className }))} {...props} />;
}
