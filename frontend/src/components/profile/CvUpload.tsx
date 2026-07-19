import {
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'
import { useRef, useState, type DragEvent } from 'react'
import { DOWNLOADS } from '../../constants/downloads'
import { useProfile } from '../../context/ProfileContext'

const DOCX_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

export function CvUpload() {
  const { profile, uploadCv } = useProfile()
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleFile = async (file: File | undefined) => {
    if (!file) return
    const isDocx = file.name.toLowerCase().endsWith('.docx') || file.type === DOCX_MIME
    if (!isDocx) {
      setError('Only .docx files are supported.')
      return
    }
    setError(null)
    setUploading(true)
    try {
      await uploadCv(file)
    } catch {
      setError('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    void handleFile(event.dataTransfer.files[0])
  }

  const isPending = profile.skillsExtractionStatus === 'pending' || uploading

  return (
    <section className="jp-surface rounded-[1.5rem] p-5 sm:p-6">
      <div className="mb-5 flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-soft text-primary">
          <DocumentTextIcon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <p className="jp-eyebrow">Career evidence</p>
          <h3 className="jp-display mt-1 text-lg font-extrabold tracking-tight text-text-primary">
            Your master CV
          </h3>
        </div>
      </div>

      <div className="mb-5 rounded-2xl border border-primary/15 bg-primary-soft/45 px-4 py-4">
        <p className="text-sm font-semibold text-text-primary">Use the JobPilot CV template</p>
        <p className="mt-1 text-xs leading-5 text-text-secondary">
          Suggested CV changes work best with this layout. Your uploaded original remains the source of truth.
        </p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <a
            href={DOWNLOADS.cvTemplateDocx}
            className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-primary/20 transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary-hover hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
            Download .docx template
          </a>
          <a
            href={DOWNLOADS.cvTemplatePdf}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-xl border border-primary/35 bg-surface px-4 py-2 text-sm font-semibold text-primary transition-colors duration-200 hover:bg-primary-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            Preview PDF layout
          </a>
        </div>
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={() => !isPending && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            if (!isPending) inputRef.current?.click()
          }
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDrop}
        className={`flex min-h-40 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-border-strong bg-surface-muted/55 px-4 py-8 text-center transition-all duration-200 ${
          isPending
            ? 'cursor-wait opacity-60'
            : 'cursor-pointer hover:border-primary/60 hover:bg-primary-soft/55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary'
        }`}
      >
        {isPending ? (
          <>
            <span className="mb-3 inline-block h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-sm font-semibold text-text-primary">Reading your career signal...</p>
            <p className="mt-1 text-xs text-text-secondary">Uploading your CV and extracting skills</p>
          </>
        ) : (
          <>
            <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-surface text-primary shadow-sm">
              <ArrowUpTrayIcon className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="text-sm font-semibold text-text-primary">Drop your CV here, or choose a file</p>
            <p className="mt-1 max-w-sm text-xs leading-5 text-text-secondary">
              .docx only. A clear Projects section and skills list give JobPilot stronger evidence to work with.
            </p>
          </>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="sr-only"
        disabled={isPending}
        onChange={(event) => void handleFile(event.target.files?.[0])}
      />

      {error ? (
        <p className="mt-3 rounded-xl border border-error/20 bg-error-soft px-3 py-2.5 text-sm text-error" role="alert">
          {error}
        </p>
      ) : null}

      {profile.cvFilename ? (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-2xl border border-success/20 bg-success-soft/60 p-3.5">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-success/10 text-success">
              <DocumentTextIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-text-primary">{profile.cvFilename}</span>
              <span className="mt-0.5 block text-xs text-success">Master CV protected</span>
            </span>
          </div>
          <button
            type="button"
            disabled={isPending}
            className="shrink-0 cursor-pointer rounded-lg px-2 py-1 text-sm font-semibold text-primary transition-colors duration-200 hover:bg-success/10 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50"
            onClick={() => inputRef.current?.click()}
          >
            Re-upload
          </button>
        </div>
      ) : null}
    </section>
  )
}
