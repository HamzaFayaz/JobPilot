export type SearchWorkMode = 'remote' | 'onsite' | 'both'
export type SearchJobAge = '24h' | 'week' | 'month'

/** Launch scope: only Pakistan is supported / smoke-tested. */
export const SEARCH_COUNTRIES = ['Pakistan'] as const

export type SearchCountry = (typeof SEARCH_COUNTRIES)[number]

export const DEFAULT_SEARCH_COUNTRY: SearchCountry = 'Pakistan'

export const SEARCH_MAX_LISTING_OPTIONS = [4, 6, 8] as const

/** Shown disabled — not offered on current deploy hardware. */
export const SEARCH_MAX_LISTING_UNSUPPORTED = [10, 12, 16] as const

export const DEFAULT_MAX_LISTINGS = 8
export const MAX_SUPPORTED_LISTINGS = 8

export const SEARCH_JOB_AGE_OPTIONS: { value: SearchJobAge; label: string }[] = [
  { value: '24h', label: 'Last 24 hours' },
  { value: 'week', label: 'Last week' },
  { value: 'month', label: 'Last month' },
]

export const SEARCH_WORK_MODE_OPTIONS: { value: SearchWorkMode; label: string }[] = [
  { value: 'remote', label: 'Remote' },
  { value: 'onsite', label: 'On-site' },
  { value: 'both', label: 'Both' },
]
