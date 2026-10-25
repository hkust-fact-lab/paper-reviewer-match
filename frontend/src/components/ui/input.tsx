import type * as React from 'react'
import { cn } from '~/lib/utils'

export function Input({ className, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      className={cn(
        'flex h-9 w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-surface px-3 text-base text-foreground placeholder:text-[var(--text-tertiary)] outline-none',
        'focus-visible:ring-3 focus-visible:ring-[var(--ring)] focus-visible:border-primary',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'transition-colors duration-[var(--duration-fast)]',
        className,
      )}
      {...props}
    />
  )
}
