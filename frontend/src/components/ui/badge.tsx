import { cva, type VariantProps } from 'class-variance-authority'
import type * as React from 'react'
import { cn } from '~/lib/utils'

export const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-[6px] px-2 py-0.5 text-xs font-medium anim-spring-in',
  {
    variants: {
      variant: {
        default:  'bg-surface-subtle text-muted-foreground',
        success:  'bg-success-surface text-success',
        warning:  'bg-warning-surface text-warning',
        danger:   'bg-danger-surface text-danger',
        primary:  'bg-[var(--amber-soft)] text-primary',
        outline:  'border border-[var(--border-strong)] text-foreground',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<'span'> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
