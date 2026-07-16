"""Hierarchical semantic README chunking at GitHub import."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Callable

from backend.app.config import settings

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^```[\w-]*\s*$", re.MULTILINE)
FENCE_BLOCK_RE = re.compile(r"^```[\w-]*\s*$.*?^```\s*$", re.MULTILINE | re.DOTALL)


def _mask_fenced_blocks(text: str) -> tuple[str, dict[str, str]]:
    """Replace fenced blocks with placeholders so inner # lines are not headings."""
    placeholders: dict[str, str] = {}

    def replacer(match: re.Match[str]) -> str:
        key = f"__FENCE_{len(placeholders)}__"
        placeholders[key] = match.group(0)
        return key

    masked = FENCE_BLOCK_RE.sub(replacer, text)
    return masked, placeholders


def _unmask_fenced_blocks(text: str, placeholders: dict[str, str]) -> str:
    for key, block in placeholders.items():
        text = text.replace(key, block)
    return text


def count_tokens(text: str) -> int:
    """Approximate token count (~4 chars/token, floor on word count)."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(len(stripped) // 4, len(stripped.split()))


@dataclass
class ParentSection:
    heading_path: str
    parent_heading: str
    content: str
    source_start: int
    source_end: int


@dataclass
class BoundaryUnit:
    text: str
    token_count: int
    atomic: bool = False


@dataclass
class ReadmeChunk:
    id: str
    chunk_type: str
    parent_heading: str | None
    heading_path: str
    content: str
    embed_text: str
    token_count: int
    source_start: int | None
    source_end: int | None
    chunk_index: int


@dataclass
class ChunkingResult:
    parents: list[ParentSection] = field(default_factory=list)
    units: list[BoundaryUnit] = field(default_factory=list)
    chunks: list[ReadmeChunk] = field(default_factory=list)


def _chunking_cfg() -> dict:
    cfg = settings.chunking_config
    return {
        "child_target_min": int(cfg.get("child_target_min", 350)),
        "child_max_tokens": int(cfg.get("child_max_tokens", 500)),
        "child_min_tokens": int(cfg.get("child_min_tokens", 120)),
        "overlap_tokens": int(cfg.get("overlap_tokens", 50)),
        "similarity_threshold": float(cfg.get("similarity_threshold", 0.55)),
    }


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _centroid(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dim = len(vectors[0])
    sums = [0.0] * dim
    for vec in vectors:
        for i, val in enumerate(vec):
            sums[i] += val
    n = float(len(vectors))
    return [v / n for v in sums]


def build_embed_text(
    project_name: str,
    stack_tags: list[str],
    heading_path: str,
    content: str,
) -> str:
    stack = ", ".join(stack_tags) if stack_tags else "unknown"
    return (
        f"Project: {project_name}\n"
        f"Stack: {stack}\n"
        f"Section: {heading_path}\n"
        f"Content: {content.strip()}"
    )


def _extract_atomic_blocks(text: str) -> list[tuple[str, bool]]:
    """Split text into alternating prose and atomic (code/table) blocks."""
    lines = text.splitlines(keepends=True)
    blocks: list[tuple[str, bool]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if FENCE_RE.match(line.rstrip("\n")):
            fence_lines = [line]
            i += 1
            while i < len(lines):
                fence_lines.append(lines[i])
                if FENCE_RE.match(lines[i].rstrip("\n")) and len(fence_lines) > 1:
                    i += 1
                    break
                i += 1
            blocks.append(("".join(fence_lines), True))
            continue
        if line.strip().startswith("|") and "|" in line:
            table_lines = [line]
            i += 1
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            blocks.append(("".join(table_lines), True))
            continue
        prose_lines = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if FENCE_RE.match(nxt.rstrip("\n")) or (
                nxt.strip().startswith("|") and "|" in nxt
            ):
                break
            prose_lines.append(nxt)
            i += 1
        blocks.append(("".join(prose_lines), False))
    return [(b, atomic) for b, atomic in blocks if b.strip()]


def _split_prose_units(prose: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", prose) if p.strip()]
    units: list[str] = []
    for para in paragraphs:
        if count_tokens(para) <= 180:
            units.append(para)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        buf: list[str] = []
        buf_tokens = 0
        for sentence in sentences:
            st = count_tokens(sentence)
            if buf and buf_tokens + st > 180:
                units.append(" ".join(buf))
                buf = [sentence]
                buf_tokens = st
            else:
                buf.append(sentence)
                buf_tokens += st
        if buf:
            units.append(" ".join(buf))
    return units


def _units_from_section(content: str) -> list[BoundaryUnit]:
    units: list[BoundaryUnit] = []
    for block, atomic in _extract_atomic_blocks(content):
        if atomic:
            units.append(
                BoundaryUnit(text=block.strip(), token_count=count_tokens(block), atomic=True)
            )
            continue
        for unit_text in _split_prose_units(block):
            units.append(
                BoundaryUnit(
                    text=unit_text,
                    token_count=count_tokens(unit_text),
                    atomic=False,
                )
            )
    return units


def parse_parent_sections(readme_md: str) -> list[ParentSection]:
    """Split README on Markdown headings into parent sections."""
    masked_md, placeholders = _mask_fenced_blocks(readme_md)
    matches = list(HEADING_RE.finditer(masked_md))
    if not matches:
        content = readme_md.strip()
        if not content:
            return []
        return [
            ParentSection(
                heading_path="Document root",
                parent_heading="Document root",
                content=content,
                source_start=0,
                source_end=len(readme_md),
            )
        ]

    preamble = readme_md[: matches[0].start()].strip()
    sections: list[ParentSection] = []
    if preamble:
        sections.append(
            ParentSection(
                heading_path="Introduction",
                parent_heading="Introduction",
                content=preamble,
                source_start=0,
                source_end=matches[0].start(),
            )
        )

    heading_stack: list[tuple[int, str]] = []
    for idx, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, title))
        path = " > ".join(h for _, h in heading_stack)
        parent_heading = heading_stack[0][1] if heading_stack else title
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(masked_md)
        body_masked = masked_md[start:end].strip()
        body = _unmask_fenced_blocks(body_masked, placeholders).strip()
        if not body:
            continue
        sections.append(
            ParentSection(
                heading_path=path,
                parent_heading=parent_heading,
                content=body,
                source_start=start,
                source_end=end,
            )
        )
    return sections


def _overlap_tail(text: str, overlap_tokens: int) -> str:
    if overlap_tokens <= 0:
        return ""
    words = text.split()
    approx_words = max(1, overlap_tokens)
    tail = " ".join(words[-approx_words:])
    return tail.strip()


def _pack_units_greedy(
    units: list[BoundaryUnit],
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Paragraph packing fallback when embeddings are unavailable."""
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for unit in units:
        if unit.atomic and unit.token_count > max_tokens:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_tokens = 0
            chunks.append(unit.text)
            continue
        if current and current_tokens + unit.token_count > max_tokens:
            chunk_text = "\n\n".join(current)
            chunks.append(chunk_text)
            overlap = _overlap_tail(chunk_text, overlap_tokens)
            current = [overlap, unit.text] if overlap else [unit.text]
            current_tokens = count_tokens("\n\n".join(current))
        else:
            current.append(unit.text)
            current_tokens += unit.token_count
    if current:
        chunks.append("\n\n".join(current))
    return [c for c in chunks if c.strip()]


def _semantic_split_units(
    units: list[BoundaryUnit],
    embed_fn: Callable[[list[str]], list[list[float]]],
    cfg: dict,
) -> list[str]:
    max_tokens = cfg["child_max_tokens"]
    overlap_tokens = cfg["overlap_tokens"]
    threshold = cfg["similarity_threshold"]

    if not units:
        return []

    total_tokens = sum(u.token_count for u in units)
    if total_tokens <= max_tokens:
        return ["\n\n".join(u.text for u in units)]

    texts = [u.text for u in units]
    try:
        vectors = embed_fn(texts)
    except Exception:
        return _pack_units_greedy(units, max_tokens, overlap_tokens)

    if len(vectors) != len(units):
        return _pack_units_greedy(units, max_tokens, overlap_tokens)

    child_texts: list[str] = []
    group_units: list[BoundaryUnit] = []
    group_vectors: list[list[float]] = []
    group_tokens = 0

    def flush_group() -> None:
        nonlocal group_units, group_vectors, group_tokens
        if not group_units:
            return
        child_texts.append("\n\n".join(u.text for u in group_units))
        group_units = []
        group_vectors = []
        group_tokens = 0

    for unit, vec in zip(units, vectors):
        if unit.atomic and unit.token_count > max_tokens:
            flush_group()
            child_texts.append(unit.text)
            continue

        if not group_units:
            group_units = [unit]
            group_vectors = [vec]
            group_tokens = unit.token_count
            continue

        centroid = _centroid(group_vectors)
        similarity = _cosine_similarity(centroid, vec)
        would_exceed = group_tokens + unit.token_count > max_tokens

        if would_exceed or similarity < threshold:
            prev = "\n\n".join(u.text for u in group_units)
            flush_group()
            overlap = _overlap_tail(prev, overlap_tokens)
            if overlap:
                group_units = [BoundaryUnit(overlap, count_tokens(overlap))]
                group_vectors = [vec]
                group_tokens = count_tokens(overlap)
            group_units.append(unit)
            group_vectors.append(vec)
            group_tokens += unit.token_count
        else:
            group_units.append(unit)
            group_vectors.append(vec)
            group_tokens += unit.token_count

    flush_group()
    return [c for c in child_texts if c.strip()]


def _split_parent_into_children(
    parent: ParentSection,
    embed_fn: Callable[[list[str]], list[list[float]]] | None,
    cfg: dict,
) -> tuple[list[BoundaryUnit], list[str]]:
    units = _units_from_section(parent.content)
    if not units:
        return [], []

    total = sum(u.token_count for u in units)
    if total <= cfg["child_max_tokens"]:
        return units, ["\n\n".join(u.text for u in units)]

    if embed_fn is None:
        return units, _pack_units_greedy(units, cfg["child_max_tokens"], cfg["overlap_tokens"])

    return units, _semantic_split_units(units, embed_fn, cfg)


def chunk_readme(
    readme_md: str,
    *,
    project_name: str,
    stack_tags: list[str] | None = None,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
) -> ChunkingResult:
    """Chunk README into parent sections and child retrieval units."""
    cfg = _chunking_cfg()
    stack_tags = stack_tags or []
    parents = parse_parent_sections(readme_md)
    all_units: list[BoundaryUnit] = []
    chunks: list[ReadmeChunk] = []
    chunk_index = 0

    for parent in parents:
        units, child_texts = _split_parent_into_children(parent, embed_fn, cfg)
        all_units.extend(units)
        for child_text in child_texts:
            token_count = count_tokens(child_text)
            chunks.append(
                ReadmeChunk(
                    id=str(uuid.uuid4()),
                    chunk_type="readme_section",
                    parent_heading=parent.parent_heading,
                    heading_path=parent.heading_path,
                    content=child_text,
                    embed_text=build_embed_text(
                        project_name, stack_tags, parent.heading_path, child_text
                    ),
                    token_count=token_count,
                    source_start=parent.source_start,
                    source_end=parent.source_end,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

    return ChunkingResult(parents=parents, units=all_units, chunks=chunks)


def evidence_claim_chunks(
    claims: list[dict],
    *,
    project_name: str,
    stack_tags: list[str] | None = None,
    start_index: int = 0,
) -> list[ReadmeChunk]:
    """Build evidence_claim rows from Phase 1 evidence_card.evidence[]."""
    stack_tags = stack_tags or []
    chunks: list[ReadmeChunk] = []
    for i, claim in enumerate(claims):
        claim_text = claim.get("claim") or claim.get("claim", "")
        if not claim_text:
            continue
        source_section = claim.get("source_section") or claim.get("sourceSection", "Evidence")
        content = claim_text.strip()
        chunks.append(
            ReadmeChunk(
                id=str(uuid.uuid4()),
                chunk_type="evidence_claim",
                parent_heading=source_section.split(" > ")[0],
                heading_path=source_section,
                content=content,
                embed_text=build_embed_text(project_name, stack_tags, source_section, content),
                token_count=count_tokens(content),
                source_start=None,
                source_end=None,
                chunk_index=start_index + i,
            )
        )
    return chunks
