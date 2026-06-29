import { Link } from 'react-router-dom'
import { CvUpload } from '../components/profile/CvUpload'
import { GitHubComingSoon } from '../components/profile/GitHubComingSoon'
import { GmailStrip } from '../components/profile/GmailStrip'
import { ProjectsList } from '../components/profile/ProjectsList'
import { RolesInput } from '../components/profile/RolesInput'
import { SkillsInput } from '../components/profile/SkillsInput'
import { Button } from '../components/ui/Button'
import { ProgressBar } from '../components/ui/ProgressBar'
import { useProfile } from '../context/ProfileContext'

export function ProfilePage() {
  const { gate } = useProfile()
  const completeness = Math.round((gate.requiredComplete / gate.requiredTotal) * 100)

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">Profile Setup</h1>
        <p className="mt-2 text-sm text-text-secondary">
          Build your profile so JobPilot can tailor searches and applications.
        </p>
      </header>

      <div className="rounded-lg border border-warning/30 bg-hitl-bg p-4 text-sm text-hitl-text">
        You approve before anything is sent. JobPilot acts as your assistant, not your
        replacement.
      </div>

      <section>
        <div className="mb-2 flex items-end justify-between">
          <h2 className="text-base font-semibold text-text-primary">Profile completeness</h2>
          <span className="text-sm font-bold text-primary">{completeness}%</span>
        </div>
        <ProgressBar value={gate.requiredComplete} max={gate.requiredTotal} />
      </section>

      <CvUpload />
      <SkillsInput />
      <RolesInput />
      <GitHubComingSoon />
      <ProjectsList />
      <GmailStrip />

      <div className="flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:justify-end">
        <Link to="/" className="w-full sm:w-auto">
          <Button variant="ghost" className="w-full">
            Back to welcome
          </Button>
        </Link>
        {gate.isComplete ? (
          <Link to="/search" className="w-full sm:w-auto">
            <Button className="w-full">Continue to Search</Button>
          </Link>
        ) : (
          <Button disabled className="w-full sm:w-auto">
            Complete required fields to continue
          </Button>
        )}
      </div>
    </div>
  )
}
