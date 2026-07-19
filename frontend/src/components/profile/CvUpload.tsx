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
    const isDocx =
      file.name.toLowerCase().endsWith('.docx') || file.type === DOCX_MIME
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
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <DocumentTextIcon className="h-5 w-5 text-primary" aria-hidden="true" />
        <h3 className="text-base font-semibold text-text-primary">CV &amp; Resume</h3>
      </div>

      <div className="mb-4 rounded-lg border border-border bg-background/60 px-4 py-3">
        <p className="text-sm font-medium text-text-primary">Supported CV template</p>
        <p className="mt-1 text-xs text-text-secondary">
          Suggested CV editing works best with this layout. Preview the PDF, or download the
          .docx to fill and upload.
        </p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <a
            href={DOWNLOADS.cvTemplateDocx}
            className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors duration-200 hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
            Download .docx template
          </a>
          <a
            href={DOWNLOADS.cvTemplatePdf}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-lg border border-primary px-4 py-2 text-sm font-semibold text-primary transition-colors duration-200 hover:bg-chip-bg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            Preview PDF layout
          </a>
        </div>
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={() => !isPending && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            if (!isPending) inputRef.current?.click()
          }
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className={`flex min-h-32 flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-background px-4 py-8 text-center transition-colors duration-200 ${
          isPending
            ? 'cursor-wait opacity-60'
            : 'cursor-pointer hover:border-primary/40 hover:bg-chip-bg/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary'
        }`}
      >
        {isPending ? (
          <>
            <span className="mb-2 inline-block h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-sm text-text-secondary">Uploading and extracting skills…</p>
          </>
        ) : (
          <>
            <ArrowUpTrayIcon className="mb-2 h-10 w-10 text-text-secondary" aria-hidden="true" />
            <p className="text-sm text-text-secondary">
              Drag and drop or click to upload your CV
            </p>
            <p className="mt-1 text-xs text-text-secondary">
              .docx only · Best results: clear Projects section, each project title + bullets,
              then Skills
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
        onChange={(e) => void handleFile(e.target.files?.[0])}
      />

      {error ? <p className="mt-2 text-sm text-error">{error}</p> : null}

      {profile.cvFilename ? (
        <div className="mt-4 flex items-center justify-between rounded-lg border border-primary/20 bg-chip-bg/40 p-3">
          <div className="flex items-center gap-3">
            <DocumentTextIcon className="h-5 w-5 text-primary" aria-hidden="true" />
            <span className="text-sm font-medium text-text-primary">{profile.cvFilename}</span>
          </div>
          <button
            type="button"
            disabled={isPending}
            className="cursor-pointer text-sm font-semibold text-primary transition-colors duration-200 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50"
            onClick={() => inputRef.current?.click()}
          >
            Re-upload
          </button>
        </div>
      ) : null}
    </section>
  )
}
