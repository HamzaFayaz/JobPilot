/** Public download paths served by nginx from ECS static/downloads. */
export const DOWNLOADS = {
  searchHelperExe: '/downloads/JobPilot-SearchHelper.exe',
  cvTemplateDocx: '/downloads/JobPilot-CV-Template.docx',
  cvTemplatePdf: '/downloads/JobPilot-CV-Template.pdf',
} as const

/** Support contact shown near Search Helper download / Windows SmartScreen help. */
export const SUPPORT_EMAIL = 'hamza.fayaz.ai@gmail.com'
