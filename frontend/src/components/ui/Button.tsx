import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-primary text-white hover:bg-primary-hover focus-visible:ring-primary disabled:bg-disabled disabled:text-text-secondary disabled:cursor-not-allowed',
  secondary:
    'border border-primary text-primary bg-surface hover:bg-chip-bg focus-visible:ring-primary disabled:border-disabled disabled:text-text-secondary disabled:cursor-not-allowed',
  ghost:
    'text-text-secondary hover:bg-border/60 focus-visible:ring-primary disabled:text-disabled disabled:cursor-not-allowed',
}

export function Button({
  variant = 'primary',
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex min-h-11 cursor-pointer items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
