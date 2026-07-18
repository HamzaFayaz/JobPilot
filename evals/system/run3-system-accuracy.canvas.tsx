import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const HOW_TO_READ = [
  {
    term: "JobPilot score",
    meaning:
      "What our system gave this job. First number = fit of the current CV. Second number = fit if the recommended project swap(s) are made.",
  },
  {
    term: "Human fair range",
    meaning:
      "After reading the job post, CV, and projects ourselves, the score we think is honest. If JobPilot’s first number sits inside this range, scoring is calibrated.",
  },
  {
    term: "Our review",
    meaning:
      "Good = accept this job’s analysis. Good, with notes = mostly right but one or two weak spots. Reject = too wrong to trust.",
  },
];

const JOBS = [
  {
    title: "Job 1 — AI Engineer (Azure / Riyadh)",
    scoreNow: 62,
    scoreAfterSwap: 68,
    fairRange: "58 to 68",
    inRange: true,
    review: "Good",
    tone: "success" as const,
    whatWentWell:
      "Correctly said Azure AI Foundry and Azure OpenAI are not on the CV. Only general Azure is partial. Swapping the game aimbot project for JobPilot (+6) makes sense.",
    weakSpot: "Some evidence quotes are shortened with “…”, so they are harder to verify word-for-word.",
  },
  {
    title: "Job 2 — AI-Assisted Web Developer",
    scoreNow: 68,
    scoreAfterSwap: 78,
    fairRange: "62 to 72",
    inRange: true,
    review: "Good, with notes",
    tone: "warning" as const,
    whatWentWell:
      "HTML/CSS correctly treated as only partial (JS/React yes, HTML/CSS not explicit). Tenure used the real date fact (~16 months). Remote matched.",
    weakSpot:
      "Suggested jump from 68→78 (+10) is a bit high. The second swap (Jarvis → WhatsApp) adds little because AI-tool skills were already matched.",
  },
  {
    title: "Job 3 — Junior AI Engineer (Lahore, onsite)",
    scoreNow: 78,
    scoreAfterSwap: 78,
    fairRange: "75 to 82",
    inRange: true,
    review: "Good",
    tone: "success" as const,
    whatWentWell:
      "Kept all four CV projects (no unnecessary swaps). Tenure and degree matched. Honestly marked Lahore onsite as not shown on the CV.",
    weakSpot: "Soft skills are a little strict, but that is acceptable.",
  },
  {
    title: "Job 4 — AI/ML & Generative AI Engineer",
    scoreNow: 78,
    scoreAfterSwap: 82,
    fairRange: "74 to 82",
    inRange: true,
    review: "Good, with notes",
    tone: "warning" as const,
    whatWentWell:
      "Big recovery vs the old broken run that scored this job 15. LangGraph, RAG, and PyTorch are grounded. Bedrock stays partial (listed, not proven in a project).",
    weakSpot:
      "Calling NLP fully “matched” is a stretch (voice/RAG is related, not classic NLP). Swapping Linnworks for JobPilot is okay but drops a strong AWS-titled project.",
  },
];

const QUALITY_PARTS = [
  {
    label: "Did IDs / sources check out?",
    value: 21,
    plain: "Citations used real CV and portfolio IDs — no invented hashes.",
  },
  {
    label: "Were claims true vs JD + CV?",
    value: 20,
    plain: "Azure products and HTML/CSS handled carefully; a few soft over-matches.",
  },
  {
    label: "Were the 0–100 scores fair?",
    value: 20,
    plain: "All four “today CV” scores sit inside the human fair range.",
  },
  {
    label: "Were project swaps sensible?",
    value: 18,
    plain: "No fake portfolio boost on the current score; one weak secondary swap.",
  },
];

export default function Run3SystemAccuracy() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>Did JobPilot do well on Run 3?</H1>
        <Text tone="secondary">
          Reviewed against the real job posts, your CV, and portfolio projects.
          Run report: 20260717T184341Z · Model: Qwen Max · Prompt: enrich_job_v4
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="79 / 100" label="Overall system accuracy" tone="success" />
        <Stat value="4 / 4" label="Jobs with a fair current score" tone="success" />
        <Stat value="0" label="Jobs that crashed on bad IDs" tone="success" />
      </Grid>

      <Callout tone="success">
        Short answer: yes. JobPilot’s analysis is trustworthy enough to keep as the
        new baseline. Scores are neither inflated (old Run 1) nor crushed (old Run 2).
        Two jobs are fully good; two are good with small notes.
      </Callout>

      <Card>
        <CardHeader>How to read this page</CardHeader>
        <CardBody>
          <Stack gap={10}>
            {HOW_TO_READ.map((item) => (
              <Stack key={item.term} gap={2}>
                <Text weight="semibold">{item.term}</Text>
                <Text tone="secondary">{item.meaning}</Text>
              </Stack>
            ))}
          </Stack>
        </CardBody>
      </Card>

      <H2>Each job, in plain language</H2>
      <Stack gap={16}>
        {JOBS.map((job) => (
          <Card key={job.title}>
            <CardHeader
              trailing={
                <Pill tone={job.tone} size="sm">
                  {job.review}
                </Pill>
              }
            >
              {job.title}
            </CardHeader>
            <CardBody>
              <Grid columns={3} gap={12}>
                <Stack gap={4}>
                  <Text tone="secondary">JobPilot score</Text>
                  <Text weight="semibold">
                    Today’s CV: {job.scoreNow}
                  </Text>
                  <Text tone="secondary">
                    After suggested swap(s): {job.scoreAfterSwap}
                  </Text>
                </Stack>
                <Stack gap={4}>
                  <Text tone="secondary">Human fair range</Text>
                  <Text weight="semibold">{job.fairRange}</Text>
                  <Text tone="secondary">
                    {job.inRange
                      ? "JobPilot’s today score is inside this range"
                      : "JobPilot’s today score is outside this range"}
                  </Text>
                </Stack>
                <Stack gap={4}>
                  <Text tone="secondary">Our review</Text>
                  <Text weight="semibold">{job.review}</Text>
                  <Text tone="secondary">
                    Based on reading JD + CV + projects
                  </Text>
                </Stack>
              </Grid>
              <Divider style={{ marginTop: 14, marginBottom: 14 }} />
              <Stack gap={8}>
                <Text>
                  <Text weight="semibold">What went well: </Text>
                  {job.whatWentWell}
                </Text>
                <Text>
                  <Text weight="semibold">Weak spot: </Text>
                  {job.weakSpot}
                </Text>
              </Stack>
            </CardBody>
          </Card>
        ))}
      </Stack>

      <H2>Where the 79 / 100 comes from</H2>
      <Text tone="secondary">
        Four equal parts, each worth up to 25 points. Chart shows points earned
        (green) vs points still missing (gray).
      </Text>
      <Card>
        <CardHeader>Quality parts (total 79)</CardHeader>
        <CardBody>
          <BarChart
            categories={QUALITY_PARTS.map((p) => p.label)}
            series={[
              {
                name: "Points earned",
                data: QUALITY_PARTS.map((p) => p.value),
                tone: "success",
              },
              {
                name: "Points missing (to 25)",
                data: QUALITY_PARTS.map((p) => 25 - p.value),
                tone: "neutral",
              },
            ]}
            height={240}
          />
          <Stack gap={8} style={{ marginTop: 12 }}>
            {QUALITY_PARTS.map((p) => (
              <Text key={p.label} tone="secondary">
                {p.label}: {p.value}/25 — {p.plain}
              </Text>
            ))}
          </Stack>
        </CardBody>
      </Card>

      <H2>Compared with earlier runs</H2>
      <Table
        headers={[
          "Run",
          "Average “today CV” score",
          "What that meant",
        ]}
        rows={[
          [
            "Run 1 (old)",
            "80",
            "Too high — weak evidence rules, inflated fit",
          ],
          [
            "Run 2 (rejected)",
            "53.5",
            "Too low — valid CV evidence thrown away (Job4 scored 15)",
          ],
          [
            "Run 3 (this run)",
            "71.5",
            "Balanced — all four scores inside human fair ranges",
          ],
        ]}
      />

      <Divider />

      <H3>To push accuracy toward 90+</H3>
      <Stack gap={6}>
        <Text>1. Prefer exact CV quotes (avoid shortened “…“ cites).</Text>
        <Text>2. Mark borderline skills like NLP as partial, not full match.</Text>
        <Text>3. Don’t recommend a swap that only repeats a skill already matched.</Text>
        <Text>4. When swapping out a strong project, account for what you lose.</Text>
      </Stack>

      <Row gap={8} align="center" wrap>
        <Pill tone="success">Keep this baseline</Pill>
        <Text tone="secondary">Qwen Max + enrich_job_v4 — do not roll back to Run 1 or Run 2</Text>
      </Row>
    </Stack>
  );
}
