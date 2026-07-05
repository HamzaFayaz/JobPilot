import { GlobeAltIcon } from '@heroicons/react/24/outline'
import {
  SEARCH_COUNTRIES,
  SEARCH_JOB_AGE_OPTIONS,
  SEARCH_MAX_LISTING_OPTIONS,
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

  return (
    <div className={compact ? 'space-y-5' : 'space-y-6'}>
      <div>
        <label htmlFor="search-country" className="mb-2 block text-sm font-semibold">
          Country
        </label>
        <div className="relative">
          <GlobeAltIcon
            className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-text-secondary"
            aria-hidden="true"
          />
          <select
            id="search-country"
            value={country}
            onChange={(e) => onChange({ searchCountry: e.target.value || null })}
            className="w-full cursor-pointer rounded-lg border border-border bg-surface py-3 pl-10 pr-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:text-sm"
          >
            <option value="">Select one country</option>
            {SEARCH_COUNTRIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
        <p className="mt-1 text-xs text-text-secondary">
          One country per search to keep results fast and focused.
        </p>
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-semibold text-text-primary">Work mode</legend>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {SEARCH_WORK_MODE_OPTIONS.map((item) => (
            <label
              key={item.value}
              className={`flex cursor-pointer items-center justify-between rounded-lg border p-4 transition-colors duration-200 ${
                workMode === item.value
                  ? 'border-primary bg-chip-bg/40'
                  : 'border-border hover:border-primary/40'
              }`}
            >
              <span className="text-sm font-medium">{item.label}</span>
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

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="search-max-listings" className="mb-2 block text-sm font-semibold">
            Max jobs
          </label>
          <select
            id="search-max-listings"
            value={maxListings}
            onChange={(e) => onChange({ searchMaxListings: Number(e.target.value) })}
            className="w-full cursor-pointer rounded-lg border border-border bg-surface px-3 py-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:text-sm"
          >
            {SEARCH_MAX_LISTING_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value} jobs
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="search-job-age" className="mb-2 block text-sm font-semibold">
            Posted within
          </label>
          <select
            id="search-job-age"
            value={jobAge}
            onChange={(e) => onChange({ searchJobAge: e.target.value as SearchJobAge })}
            className="w-full cursor-pointer rounded-lg border border-border bg-surface px-3 py-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:text-sm"
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
