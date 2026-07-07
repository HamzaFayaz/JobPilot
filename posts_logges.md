(.venv) D:\Github\AI\AI Agents\JobPilot>"d:/Github/AI/AI Agents/JobPilot/.venv/Scripts/python.exe" "d:/Github/AI/AI Agents/JobPilot/worker/main.py"
2026-07-07 10:30:50,771 INFO [Search Helper] Worker lock acquired (pid=21908)
2026-07-07 10:30:50,771 INFO [Search Helper] JobPilot Search Helper starting (poll every 3.0s)
2026-07-07 10:30:50,772 INFO [Search Helper] Connected to JobPilot at http://43.98.197.132
2026-07-07 10:30:50,772 INFO [Search Helper] Browser provider: webbridge | Qwen model: qwen-max
2026-07-07 10:30:51,377 INFO [Search Helper] WebBridge daemon running — open Chrome so the extension can connect
2026-07-07 10:30:51,807 INFO [Search Helper] Polling for tasks — none pending (pid=21908)
2026-07-07 10:31:00,001 INFO [Search Helper] WebBridge ready — Chrome extension connected
2026-07-07 10:31:31,809 INFO [Search Helper] Received task 41e4669f-7b3c-40bc-b42a-c52c6358fad2 for run 57 (AI Engineer / linkedin)
2026-07-07 10:31:32,638 INFO [Search Helper] Starting WebBridge search: role=AI Engineer platform=linkedin country=Pakistan max=4 age=week
2026-07-07 10:31:32,638 INFO [Search Helper] LinkedIn sequential run: jobs_target=0 posts_target=4 posts_enabled=True phase_max_steps=40
2026-07-07 10:31:32,638 INFO [Search Helper] LinkedIn phase starting: posts
2026-07-07 10:31:32,797 INFO [Search Helper] Starting agent phase=posts max_steps=40 session=jobpilot-run-57-posts run_id=57
2026-07-07 10:31:32,797 INFO [Search Helper] Bootstrap [posts] navigate → https://www.linkedin.com/search/results/content/?keywords=hiring+%22AI+Engineer%22+Pakistan&datePosted=%5B%22past-week%22%5D&sortBy=%5B%22relevance%22%5D&origin=FACETED_SEARCH
2026-07-07 10:31:38,307 INFO [Search Helper] Saved snapshot debug file: D:\Github\AI\AI Agents\JobPilot\worker\debug_snapshots\run-57\posts\full\step-01-navigate.json
2026-07-07 10:31:39,016 INFO [Search Helper] Saved snapshot debug file: D:\Github\AI\AI Agents\JobPilot\worker\debug_snapshots\run-57\posts\full\step-02-snapshot.json
2026-07-07 10:31:39,017 INFO [Search Helper] Saved compressed snapshot debug file: D:\Github\AI\AI Agents\JobPilot\worker\debug_snapshots\run-57\posts\compressed\step-02-snapshot.json
2026-07-07 10:31:40,783 INFO [Search Helper] Saved snapshot debug file: D:\Github\AI\AI Agents\JobPilot\worker\debug_snapshots\run-57\posts\full\step-04-snapshot.json
2026-07-07 10:31:40,784 INFO [Search Helper] Saved compressed snapshot debug file: D:\Github\AI\AI Agents\JobPilot\worker\debug_snapshots\run-57\posts\compressed\step-04-snapshot.json
2026-07-07 10:31:40,785 INFO [Search Helper] Worker scroll [posts] attempt 1: 2 → 2 (target=4)
2026-07-07 10:31:52,503 INFO [Search Helper] LLM [posts] step 1 tokens in=3537 out=349 total=3886 chars=11782 tools=(reply)
2026-07-07 10:31:52,504 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 1 (min_steps=12, hiring_openings=2)
2026-07-07 10:31:57,331 INFO [Search Helper] LLM [posts] step 2 tokens in=3945 out=356 total=4301 chars=13400 tools=(reply)
2026-07-07 10:31:57,331 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 2 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:02,297 INFO [Search Helper] LLM [posts] step 3 tokens in=4360 out=349 total=4709 chars=15038 tools=(reply)
2026-07-07 10:32:02,298 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 3 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:07,290 INFO [Search Helper] LLM [posts] step 4 tokens in=4768 out=349 total=5117 chars=16656 tools=(reply)
2026-07-07 10:32:07,290 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 4 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:12,542 INFO [Search Helper] LLM [posts] step 5 tokens in=5176 out=349 total=5525 chars=18274 tools=(reply)
2026-07-07 10:32:12,542 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 5 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:18,583 INFO [Search Helper] LLM [posts] step 6 tokens in=5584 out=349 total=5933 chars=19892 tools=(reply)
2026-07-07 10:32:18,583 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 6 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:26,365 INFO [Search Helper] LLM [posts] step 7 tokens in=5992 out=349 total=6341 chars=21510 tools=(reply)
2026-07-07 10:32:26,366 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 7 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:31,417 INFO [Search Helper] LLM [posts] step 8 tokens in=6400 out=349 total=6749 chars=23128 tools=(reply)
2026-07-07 10:32:31,417 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 8 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:36,934 INFO [Search Helper] LLM [posts] step 9 tokens in=6808 out=349 total=7157 chars=24746 tools=(reply)
2026-07-07 10:32:36,934 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 9 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:42,026 INFO [Search Helper] LLM [posts] step 10 tokens in=7216 out=349 total=7565 chars=26364 tools=(reply)
2026-07-07 10:32:42,027 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 10 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:47,156 INFO [Search Helper] LLM [posts] step 11 tokens in=7624 out=349 total=7973 chars=27982 tools=(reply)
2026-07-07 10:32:47,157 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 11 (min_steps=12, hiring_openings=2)
2026-07-07 10:32:55,116 INFO [Search Helper] LLM [posts] step 12 tokens in=8032 out=349 total=8381 chars=29600 tools=(reply)
2026-07-07 10:32:55,117 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 12 (min_steps=12, hiring_openings=2)
2026-07-07 10:33:04,410 INFO [Search Helper] LLM [posts] step 13 tokens in=8440 out=349 total=8789 chars=31218 tools=(reply)
2026-07-07 10:33:04,411 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 13 (min_steps=12, hiring_openings=2)
2026-07-07 10:33:13,825 INFO [Search Helper] LLM [posts] step 14 tokens in=8848 out=349 total=9197 chars=32836 tools=(reply)
2026-07-07 10:33:13,825 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 14 (min_steps=12, hiring_openings=2)
2026-07-07 10:33:22,859 INFO [Search Helper] LLM [posts] step 15 tokens in=9256 out=349 total=9605 chars=34454 tools=(reply)
2026-07-07 10:33:22,860 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 15 (min_steps=12, hiring_openings=2)
2026-07-07 10:33:32,088 INFO [Search Helper] LLM [posts] step 16 tokens in=9664 out=349 total=10013 chars=36072 tools=(reply)
2026-07-07 10:33:32,089 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 16 (min_steps=12, hiring_openings=2)
2026-07-07 10:33:41,259 INFO [Search Helper] LLM [posts] step 17 tokens in=10072 out=349 total=10421 chars=37690 tools=(reply)
2026-07-07 10:33:41,259 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 17 (min_steps=12, hiring_openings=2)
2026-07-07 10:33:53,968 INFO [Search Helper] LLM [posts] step 18 tokens in=10480 out=349 total=10829 chars=39308 tools=(reply)
2026-07-07 10:33:53,969 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 18 (min_steps=12, hiring_openings=2)
2026-07-07 10:34:03,383 INFO [Search Helper] LLM [posts] step 19 tokens in=10888 out=349 total=11237 chars=40926 tools=(reply)
2026-07-07 10:34:03,383 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 19 (min_steps=12, hiring_openings=2)
2026-07-07 10:34:12,872 INFO [Search Helper] LLM [posts] step 20 tokens in=11296 out=349 total=11645 chars=42544 tools=(reply)
2026-07-07 10:34:12,872 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 20 (min_steps=12, hiring_openings=2)
2026-07-07 10:34:22,294 INFO [Search Helper] LLM [posts] step 21 tokens in=11704 out=349 total=12053 chars=44162 tools=(reply)
2026-07-07 10:34:22,296 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 21 (min_steps=12, hiring_openings=2)
2026-07-07 10:34:31,733 INFO [Search Helper] LLM [posts] step 22 tokens in=12112 out=349 total=12461 chars=45780 tools=(reply)
2026-07-07 10:34:31,733 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 22 (min_steps=12, hiring_openings=2)
2026-07-07 10:34:42,766 INFO [Search Helper] LLM [posts] step 23 tokens in=12520 out=349 total=12869 chars=47398 tools=(reply)
2026-07-07 10:34:42,766 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 23 (min_steps=12, hiring_openings=2)
2026-07-07 10:34:52,012 INFO [Search Helper] LLM [posts] step 24 tokens in=12928 out=349 total=13277 chars=49016 tools=(reply)
2026-07-07 10:34:52,013 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 24 (min_steps=12, hiring_openings=2)
2026-07-07 10:35:04,004 INFO [Search Helper] LLM [posts] step 25 tokens in=13336 out=349 total=13685 chars=50634 tools=(reply)
2026-07-07 10:35:04,004 INFO [Search Helper] Agent phase=posts rejected early empty JSON at llm_step 25 (min_steps=12, hiring_openings=2)