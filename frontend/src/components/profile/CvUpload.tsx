import { ArrowUpTrayIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import { useRef, useState, type DragEvent } from 'react'
import { useProfile } from '../../context/ProfileContext'

const DOCX_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

export function CvUpload() {
  const { profile, setCv } = useProfile()
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFile = (file: File | undefined) => {
    if (!file) return
    const isDocx =
      file.name.toLowerCase().endsWith('.docx') || file.type === DOCX_MIME
    if (!isDocx) {
      setError('Only .docx files are supported.')
      return
    }
    setError(null)
    setCv(file.name, file.size)
  }

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    handleFile(event.dataTransfer.files[0])
  }

  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <DocumentTextIcon className="h-5 w-5 text-primary" aria-hidden="true" />
        <h3 className="text-base font-semibold text-text-primary">CV &amp; Resume</h3>
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-background px-4 py-8 text-center transition-colors duration-200 hover:border-primary/40 hover:bg-chip-bg/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <ArrowUpTrayIcon className="mb-2 h-10 w-10 text-text-secondary" aria-hidden="true" />
        <p className="text-sm text-text-secondary">
          Drag and drop or click to upload your CV
        </p>
        <p className="mt-1 text-xs text-text-secondary">.docx only</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="sr-only"
        onChange={(e) => handleFile(e.target.files?.[0])}
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
            className="cursor-pointer text-sm font-semibold text-primary transition-colors duration-200 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            onClick={() => inputRef.current?.click()}
          >
            Re-upload
          </button>
        </div>
      ) : null}
    </section>
  )
}
