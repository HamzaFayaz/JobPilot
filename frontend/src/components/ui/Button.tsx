import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'border border-primary bg-primary text-white shadow-sm shadow-primary/20 hover:-translate-y-0.5 hover:bg-primary-hover hover:shadow-md hover:shadow-primary/20 active:translate-y-0 active:scale-[0.98] focus-visible:ring-primary disabled:border-disabled disabled:bg-disabled disabled:text-text-secondary disabled:shadow-none disabled:cursor-not-allowed',
  secondary:
    'border border-border-strong bg-surface text-text-primary shadow-sm hover:-translate-y-0.5 hover:border-primary/45 hover:bg-primary-soft/55 active:translate-y-0 active:scale-[0.98] focus-visible:ring-primary disabled:border-disabled disabled:text-text-secondary disabled:shadow-none disabled:cursor-not-allowed',
  ghost:
    'text-text-secondary hover:bg-surface-muted hover:text-text-primary active:scale-[0.98] focus-visible:ring-primary disabled:text-disabled disabled:cursor-not-allowed',
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
      className={`inline-flex min-h-11 cursor-pointer items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
