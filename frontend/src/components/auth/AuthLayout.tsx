import {
  CheckCircleIcon,
  PaperAirplaneIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import type { ReactNode } from 'react'

interface AuthLayoutProps {
  eyebrow: string
  title: string
  description: string
  children: ReactNode
}

export function AuthLayout({ eyebrow, title, description, children }: AuthLayoutProps) {
  return (
    <main className="relative isolate flex min-h-screen overflow-hidden bg-canvas p-4 sm:p-6 lg:p-8">
      <div className="pointer-events-none absolute -left-32 top-1/4 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-0 h-[28rem] w-[28rem] rounded-full bg-secondary/10 blur-3xl" />

      <div className="relative mx-auto grid w-full max-w-[1240px] overflow-hidden rounded-[2rem] border border-border bg-surface shadow-float lg:grid-cols-[0.94fr_1.06fr]">
        <section className="jp-grid-pattern relative hidden min-h-[680px] overflow-hidden bg-sidebar p-9 text-white lg:flex lg:flex-col xl:p-12">
          <div className="pointer-events-none absolute -right-24 top-10 h-72 w-72 rounded-full bg-primary/30 blur-3xl" />
          <div className="pointer-events-none absolute -left-24 bottom-0 h-80 w-80 rounded-full bg-secondary/25 blur-3xl" />

          <div className="relative flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-black/25">
              <PaperAirplaneIcon className="h-5 w-5 -rotate-45" aria-hidden="true" />
            </span>
            <div>
              <p className="jp-display text-xl font-extrabold tracking-tight">JobPilot</p>
              <p className="text-[11px] font-medium uppercase tracking-[0.13em] text-slate-400">
                Career intelligence
              </p>
            </div>
          </div>

          <div className="relative my-auto max-w-md py-14">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/7 px-3 py-1.5 text-xs font-semibold text-teal-100">
              <SparklesIcon className="h-4 w-4" aria-hidden="true" />
              Your career pilot desk
            </span>
            <h1 className="jp-display mt-6 text-4xl font-extrabold leading-[1.08] tracking-tight xl:text-5xl">
              Find high-fit roles. Keep every decision yours.
            </h1>
            <p className="mt-5 text-base leading-7 text-slate-300">
              JobPilot scouts real LinkedIn Posts from your browser, explains the fit, and keeps you
              in control at every step.
            </p>

            <ol className="mt-10 space-y-4">
              {[
                ['Build your signal', 'CV and project evidence become your search profile.'],
                ['Let JobPilot scout', 'Your connected browser finds relevant LinkedIn Posts.'],
                ['Review with confidence', 'See evidence-backed matches before you act.'],
              ].map(([step, detail], index) => (
                <li key={step} className="flex items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-primary/50 bg-primary/15 text-xs font-bold text-teal-100">
                    {index + 1}
                  </span>
                  <span>
                    <span className="block text-sm font-semibold text-white">{step}</span>
                    <span className="mt-0.5 block text-xs leading-5 text-slate-400">{detail}</span>
                  </span>
                </li>
              ))}
            </ol>
          </div>

          <div className="relative flex items-center gap-2 text-xs text-slate-400">
            <ShieldCheckIcon className="h-4 w-4 text-primary" aria-hidden="true" />
            Nothing is submitted automatically.
          </div>
        </section>

        <section className="relative flex min-h-[560px] items-center px-5 py-10 sm:px-10 lg:px-14 xl:px-20">
          <div className="w-full max-w-md">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-white shadow-sm shadow-primary/25">
                <PaperAirplaneIcon className="h-5 w-5 -rotate-45" aria-hidden="true" />
              </span>
              <div>
                <p className="jp-display text-lg font-extrabold tracking-tight text-text-primary">JobPilot</p>
                <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-text-tertiary">
                  Career intelligence
                </p>
              </div>
            </div>

            <div className="mb-8">
              <p className="jp-eyebrow">{eyebrow}</p>
              <h2 className="jp-display mt-3 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
                {title}
              </h2>
              <p className="mt-3 max-w-sm text-sm leading-6 text-text-secondary">{description}</p>
            </div>

            {children}

            <div className="mt-8 flex items-center gap-2 text-xs text-text-tertiary">
              <CheckCircleIcon className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
              Your profile stays private and under your control.
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
