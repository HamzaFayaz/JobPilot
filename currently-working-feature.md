# Currently Working On

**Status:** Search Helper (Kimi WebBridge + Qwen agent loop) is **working end-to-end** for the hackathon. LinkedIn **Posts** phase collects listings and the background-tab scroll bug is fixed.

## Hackathon scope (locked — 2 days left)

- **Posts phase only.** Jobs phase stays **disabled**; listings come from Posts (the post body carries the JD). Details → [`job-section-issue.md`](job-section-issue.md)
- **LinkedIn only.** Indeed is **deferred** until the core system is complete. Phase flags live in [`worker/prompts.py`](worker/prompts.py)
- **Do NOT change the working worker/agent logic.** It works now — treat it as frozen. The scroll fix (background-tab → foreground rendering) lives in [`worker/webbridge_scroll.py`](worker/webbridge_scroll.py) (`enable_foreground_rendering`) and [`worker/agent_loop.py`](worker/agent_loop.py) (`_auto_scroll_after_bootstrap`).

## Next step (new chat): package + distribute the worker

Build the Search Helper into a downloadable **`.exe`** and upload it to the server so users can download and run it. Packaging must **wrap** the current worker, not modify its logic.

- Worker run/setup reference → [`worker/README.md`](worker/README.md)
- Server / deploy reference → [`System Design/aws-ec2-deploy.md`](System%20Design/aws-ec2-deploy.md)

## Background (unchanged)

- WebBridge provider & architecture → [`System Design/kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md)
- Search agent contract → [`docs/discussion/search-subgraph-discussion-and-finalization.md`](docs/discussion/search-subgraph-discussion-and-finalization.md)
