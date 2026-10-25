import { cva, type VariantProps } from 'class-variance-authority'
import type * as React from 'react'
import { cn } from '~/lib/utils'

export const buttonVariants = cva(
  'inline-flex shrink-0 items-center justify-center gap-1.5 whitespace-nowrap rounded-[10px] text-sm font-medium transition-colors outline-none focus-visible:ring-3 focus-visible:ring-[var(--ring)] disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0 press-down cursor-default select-none',
  {
    variants: {
      variant: {
        default:  'bg-primary text-primary-foreground hover:opacity-90 shadow-sm',
        outline:  'border border-[var(--border-strong)] bg-surface hover:bg-surface-subtle text-foreground',
        ghost:    'hover:bg-surface-subtle text-foreground',
        danger:   'bg-danger text-white hover:opacity-90 shadow-sm',
        link:     'text-primary underline-offset-4 hover:underline p-0 h-auto',
      },
      size: {
        default: 'h-9 px-4',
        sm:      'h-[30px] px-3 text-xs rounded-[6px]',
        lg:      'h-11 px-5 text-base',
        icon:    'size-9',
        'icon-sm': 'size-[30px]',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)

export function Button({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<'button'> & VariantProps<typeof buttonVariants>) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
}
