import { GlobeAltIcon, MapPinIcon } from '@heroicons/react/24/outline'
import { useEffect } from 'react'
import {
  DEFAULT_MAX_LISTINGS,
  DEFAULT_SEARCH_COUNTRY,
  MAX_SUPPORTED_LISTINGS,
  SEARCH_COUNTRIES,
  SEARCH_JOB_AGE_OPTIONS,
  SEARCH_MAX_LISTING_OPTIONS,
  SEARCH_MAX_LISTING_UNSUPPORTED,
  SEARCH_WORK_MODE_OPTIONS,
  type SearchJobAge,
  type SearchWorkMode,
} from '../../constants/searchPreferences'
import type { Profile } from '../../types/profile'

type SearchPreferencesFieldsProps = {
  profile: Profile
  onChange: (patch: Partial<Profile>) => void
  compact?: boolean
}

export function SearchPreferencesFields({
  profile,
  onChange,
  compact = false,
}: SearchPreferencesFieldsProps) {
  const country = profile.searchCountry ?? ''
  const workMode = profile.searchWorkMode
  const maxListings = profile.searchMaxListings
  const jobAge = profile.searchJobAge

  // Launch scope: lock to Pakistan (migrate any older saved country).
  useEffect(() => {
    if (country !== DEFAULT_SEARCH_COUNTRY) {
      onChange({ searchCountry: DEFAULT_SEARCH_COUNTRY })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- lock country once when mismatched
  }, [country])

  // Cap max jobs to what current server resources support.
  useEffect(() => {
    if (maxListings > MAX_SUPPORTED_LISTINGS) {
      onChange({ searchMaxListings: DEFAULT_MAX_LISTINGS })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- clamp once when over cap
  }, [maxListings])

  const selectMaxListings =
    maxListings > MAX_SUPPORTED_LISTINGS ? DEFAULT_MAX_LISTINGS : maxListings

  return (
    <div className={compact ? 'space-y-5' : 'space-y-6'}>
      <div>
        <label htmlFor="search-country" className="mb-2 block text-sm font-semibold text-text-primary">
          Search region
        </label>
        <div className="relative">
          <GlobeAltIcon
            className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-primary"
            aria-hidden="true"
          />
          <select
            id="search-country"
            value={DEFAULT_SEARCH_COUNTRY}
            disabled
            aria-readonly="true"
            className="jp-input w-full cursor-not-allowed bg-surface-muted py-2.5 pl-11 pr-3 text-base opacity-95 sm:text-sm"
          >
            {SEARCH_COUNTRIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
        <p className="mt-1.5 flex items-center gap-1.5 text-xs text-text-secondary">
          <MapPinIcon className="h-3.5 w-3.5" aria-hidden="true" />
          Pakistan is the currently supported launch region.
        </p>
      </div>

      <fieldset>
        <legend className="mb-3 text-sm font-semibold text-text-primary">Work mode</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {SEARCH_WORK_MODE_OPTIONS.map((item) => (
            <label
              key={item.value}
              className={`flex min-h-12 cursor-pointer items-center justify-between rounded-xl border px-3 py-2.5 transition-all duration-200 ${
                workMode === item.value
                  ? 'border-primary/45 bg-primary-soft/65 text-primary shadow-sm'
                  : 'border-border bg-surface hover:border-primary/30'
              }`}
            >
              <span className="text-sm font-semibold">{item.label}</span>
              <input
                type="radio"
                name="search-work-mode"
                value={item.value}
                checked={workMode === item.value}
                onChange={() => onChange({ searchWorkMode: item.value as SearchWorkMode })}
                className="h-4 w-4 cursor-pointer accent-primary"
              />
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="search-max-listings" className="mb-2 block text-sm font-semibold text-text-primary">
            Review queue size
          </label>
          <select
            id="search-max-listings"
            value={selectMaxListings}
            onChange={(event) => onChange({ searchMaxListings: Number(event.target.value) })}
            className="jp-input w-full cursor-pointer px-3 py-2.5 text-base sm:text-sm"
          >
            {SEARCH_MAX_LISTING_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value} jobs
              </option>
            ))}
            {SEARCH_MAX_LISTING_UNSUPPORTED.map((value) => (
              <option key={value} value={value} disabled>
                {value} jobs (not supported)
              </option>
            ))}
          </select>
          <p className="mt-1.5 text-xs text-text-secondary">
            Up to {MAX_SUPPORTED_LISTINGS} jobs per run on current server resources.
          </p>
        </div>

        <div>
          <label htmlFor="search-job-age" className="mb-2 block text-sm font-semibold text-text-primary">
            Posted within
          </label>
          <select
            id="search-job-age"
            value={jobAge}
            onChange={(event) => onChange({ searchJobAge: event.target.value as SearchJobAge })}
            className="jp-input w-full cursor-pointer px-3 py-2.5 text-base sm:text-sm"
          >
            {SEARCH_JOB_AGE_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
