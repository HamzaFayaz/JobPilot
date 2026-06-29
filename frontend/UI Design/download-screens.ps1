# One-time helper used to fetch Stitch exports. Run from repo root if needed.
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot

$screens = @(
  @{
    slug = '01-welcome'
    title = 'JobPilot Welcome Screen'
    route = '/'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLuEEGp8eD_htkHOqhnQh6loPvzogQnsHzMbfAmKjJ_hd4GkkPbPKHOFvOSc-yxPYPxsXaVLYJ-mfh_kW9_--ABkD6MqK49McyMFpP8YlAuw9QXXBMlnVSsETJsf84A6_5tf5ziSTRb9vLp7D5ULw4gSt2468TSO6P1mr1dowYRchKmyzQRlU-w5mHj346wQ0037FYMGjCT0gJKiB0X51_Bq87Y9PYl35YMirIJtfgvFe2HHrp14w6dXR5Q'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2QxYWQ0YWI3NDVmZDQ5OWFiYWM2NzA5YjJjNjFkNzFkEgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '02-profile'
    title = 'JobPilot Profile Setup'
    route = '/profile'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLsCylBuJqTBnaQ5qwt12mOVnBaAFaFVMdS0Bwe5rV1MmkY0RhvhZMkT-Mm0QfKu6Gzf79x8aXwXfqH-9WL01J5CfoK0v_4_hTGKUuD9Ruqrr9eC-Rx9DbsQ5-Q0dSOzsc7tfqq4G13FpfgmHIeWiYgBSQdRkgcv8VE9-zU-R4k-mLuwjAcGqsRzcC9E0TTZqLrSdd4h0DdOfQrUK_uBHIjabQQeUtMebQ0FZfrHJVNVRDS2S9_OWU4wWL0'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzk5NDg5YzMyYmE5NzQyN2Y4YTgxNjgzOWVjOTM5YjVmEgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '03-search'
    title = 'JobPilot New Search'
    route = '/search'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLuY9jhJtk-Yn-g-B4FaaokfpeWIiNIkwLOXDH9Cm9zUb-_8op-luntUr7UBoK_29prxndoTVacYI7H_JvipTuD6EKaHIExwuWpvkzuMKtrQY17KtimyqNogLVOBRY5ynbKu2hm_eo7cUzuzWVl3nUjt-Q6S9FXAOr5etDdWNdqx9SmM2p9CrnOmLHLVXiGxBQGx6U0WPvlkR6RdvgeNnjWYfjhWVurtbZHIPm9Ntf9D-HAIRSwvePQN4mFW'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzc4ZGZkYmNhMDA4NzQ3NzRhMDJlY2Q1MzFmN2M0M2Q4EgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '04-run-progress'
    title = 'JobPilot Run In Progress'
    route = '/runs/:runId'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLvrQgBs8bWG9tLcV-IRba8ZOHfAxjJ7WqEo3LuXTFrY-85QqgAvY0IddICbagSdZNHIzsWKE_w0KY45RO9839HHwu3hWZ-DH3rxJ_PBdpJGOdmPDF32aDtldIdrLf0zBHyVJcH8ZcDYD7yYKCl9Jop-Bc_qkT0ir3Ho4h5GEUE4ch7JrMM-9Vq238h4dHORL-MtovyQV4Cj5mRsOjlC98yeSt4vpkaScprgmMFtZbJ_9xcqiCOVWlF6jw1Q'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2IyYWVlYTliNmQ1YjQzOGZiNzQyMTA1OTdiZjZmZDE0EgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '05-job-list'
    title = 'Job Results List'
    route = '/runs/:runId/jobs'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLs4mn4p0-Te5qAihQcn1207VAGYlPgb0lVGJwjN0RD7lTfy7vwXM_DG8D_-AANx5l0x6xJxKzGTKl0il6yfHnbiQLz6ZSV5K_1_kyrzud5Od8EUGLQQZogiCAEGExGOwkLaBNjzE-KPOQOZF73XN2OmDLDkX6SlO2JZ65xbtcgCIvBbmDGf_RAyk20eG0mv2Bw1ToSHa3d--Ox9CF6uoXPog-XZ4VR0x-FxfACP5rvL_n87Jc4bHdA2Hgc'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzhkOWI4NTJkODIxYzQwNGI4YzA1NTQxMDliYmQ4OGM5EgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '06-job-detail'
    title = 'Job Detail HITL Review'
    route = '/jobs/:id'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLv_vPWT1NWVrBqjHpfqWWcrF6Rkji-ZaJHKI2TNXKxdkUr3xntc6F04zhq91EvIv4thV7WOzm2EYpwytwePuu0N8hpStc9LXS-UHCjzSELOjQvHR9uyHeujAoLnnOJJJbLpQGv8S4o_Po1oducyPumXyGGLaPZu6mciRkXpYLHL-1iaUZEjhdRloV-OymdpMaH5jPNXI99_ivOm2LYgwEnubEUlLARGyfnWBSUz5kOD_din4YU2Zk3dTE9n'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2JhMTA0ODhmOGU2YjQyZmRiNmMwZTk5YmNkOTIyYjJjEgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '07-applications'
    title = 'JobPilot Applications & History'
    route = '/applications'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLv5ARcQOHhqz5TLROQmkHwMCSd1CkObBk9b15IyBFGdIOHxoLnEb6SjrJ6Wvd0LL14PJX_rK5S2UHOYPjthFTvtq54Xx4dujPg_SM_mJwJoBdAJMtLDnPPKaQC0zd9dGXf1ei3XX_cEq4TJpn6CYMmgNzhxffQAHAPtUiNEdQWglqc8-2cYSuuOLtHotg5xsAMAGjMCOjyz-xnAMOV57YhFogd-NY2aXwdWzIrvhzwPxp4X0ljT7nuKS3IC'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzA5M2RmMzk5NmI4ODQ4M2M5YjA2MDJjZTc3ZTgzMWI1EgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  },
  @{
    slug = '08-settings'
    title = 'JobPilot Settings'
    route = '/settings'
    png = 'https://lh3.googleusercontent.com/aida/AP1WRLuwIJ6XASFPdy8yrkLjq5cVCujPQrROo1b8FKTZozXuURXBR1ulLzUftsUgICzxCRawy4k2Ucuvqlv0i-ArsMu_Qkch_8m0LCcwm-m57dCpWGVJin9vxMy9wNGrouZhmEcBhr_BCY7JFmt_yyTp9dzME4vTjsm9J0r2mWTx31UQZixqqpdF1CMYtDKq6120TMGiCSPfX3Hl0opSAGBczv0meqxBlv7iFrDVN1RRMueM_huNpFzz2kcWKou-'
    html = 'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzJhZTVjMzhkMGU0NTQxMjQ5MDRlNGM1MzkzMGZkOTAzEgsSBxCjhIDg0xgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNTYwODk2ODE0NTgwMTcxMTg2Mw&filename=&opi=96797242'
  }
)

foreach ($s in $screens) {
  $dir = Join-Path $base $s.slug
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  Invoke-WebRequest -Uri $s.png -OutFile (Join-Path $dir 'screenshot.png') -UseBasicParsing
  Invoke-WebRequest -Uri $s.html -OutFile (Join-Path $dir 'screen.html') -UseBasicParsing
  @{
    title = $s.title
    route = $s.route
    slug = $s.slug
    files = @('screenshot.png', 'screen.html')
  } | ConvertTo-Json | Set-Content -Path (Join-Path $dir 'meta.json') -Encoding UTF8
  Write-Host "Downloaded $($s.slug)"
}
