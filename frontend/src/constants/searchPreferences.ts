export type SearchWorkMode = 'remote' | 'onsite' | 'both'
export type SearchJobAge = '24h' | 'week' | 'month'

export const SEARCH_COUNTRIES = [
  'United States',
  'United Kingdom',
  'Canada',
  'Australia',
  'Germany',
  'France',
  'Netherlands',
  'Pakistan',
  'India',
  'United Arab Emirates',
  'Singapore',
  'Saudi Arabia',
] as const

export type SearchCountry = (typeof SEARCH_COUNTRIES)[number]

export const SEARCH_MAX_LISTING_OPTIONS = [4, 6, 8, 10, 12, 16] as const

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
