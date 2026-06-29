import { CodeBracketIcon } from '@heroicons/react/24/outline'
import { Button } from '../ui/Button'

export function GitHubComingSoon() {
  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <CodeBracketIcon className="mt-0.5 h-6 w-6 text-primary" aria-hidden="true" />
          <div>
            <h3 className="text-base font-semibold text-text-primary">Import from GitHub</h3>
            <p className="text-sm text-text-secondary">
              Auto-import repositories as projects. Add projects manually for now.
            </p>
          </div>
        </div>
        <span title="GitHub import is coming soon">
          <Button variant="secondary" disabled className="w-full sm:w-auto">
            Coming soon
          </Button>
        </span>
      </div>
    </section>
  )
}
