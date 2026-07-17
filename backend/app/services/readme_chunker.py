"""Hierarchical semantic README chunking at GitHub import."""

from __future__ import annotations

import re
import string
import uuid
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import Callable

from backend.app.config import settings
from backend.app.observability import instrument

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*\r?$", re.MULTILINE)
FENCE_RE = re.compile(r"^```[\w-]*\s*$", re.MULTILINE)
FENCE_BLOCK_RE = re.compile(r"^```[\w-]*\s*$.*?^```\s*$", re.MULTILINE | re.DOTALL)


def _mask_fenced_blocks(text: str) -> str:
    """Mask fence contents without changing length or newline offsets."""
    masked: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        is_fence = bool(re.match(r"^\s*```", line))
        if is_fence:
            in_fence = not in_fence
        if in_fence or is_fence:
            masked.append("".join(char if char in "\r\n" else " " for char in line))
        else:
            masked.append(line)
    return "".join(masked)


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
    source_start: int = 0
    source_end: int = 0


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
    short_chunk_reason: str | None = None
    oversize_reason: str | None = None


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


def _extract_atomic_blocks(text: str) -> list[tuple[int, int, bool]]:
    """Split text into alternating prose and atomic (code/table) blocks."""
    lines = text.splitlines(keepends=True)
    blocks: list[tuple[int, int, bool]] = []
    offset = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        block_start = offset
        if FENCE_RE.match(line.rstrip("\n")):
            fence_lines = [line]
            offset += len(line)
            i += 1
            while i < len(lines):
                fence_lines.append(lines[i])
                offset += len(lines[i])
                if FENCE_RE.match(lines[i].rstrip("\n")) and len(fence_lines) > 1:
                    i += 1
                    break
                i += 1
            blocks.append((block_start, offset, True))
            continue
        if line.strip().startswith("|") and "|" in line:
            table_lines = [line]
            offset += len(line)
            i += 1
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                offset += len(lines[i])
                i += 1
            blocks.append((block_start, offset, True))
            continue
        prose_lines = [line]
        offset += len(line)
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if FENCE_RE.match(nxt.rstrip("\n")) or (
                nxt.strip().startswith("|") and "|" in nxt
            ):
                break
            prose_lines.append(nxt)
            offset += len(nxt)
            i += 1
        blocks.append((block_start, offset, False))
    return [(start, end, atomic) for start, end, atomic in blocks if text[start:end].strip()]


def _split_prose_units(prose: str, base_offset: int) -> list[BoundaryUnit]:
    units: list[BoundaryUnit] = []
    for paragraph in re.finditer(r"\S(?:.*?\S)?(?=(?:\r?\n){2,}|\Z)", prose, re.DOTALL):
        para = paragraph.group(0)
        para_start = base_offset + paragraph.start()
        if count_tokens(para) <= 180:
            units.append(
                BoundaryUnit(
                    text=para,
                    token_count=count_tokens(para),
                    source_start=para_start,
                    source_end=para_start + len(para),
                )
            )
            continue
        sentence_matches = list(re.finditer(r".+?(?:[.!?](?=\s+|$)|$)", para, re.DOTALL))
        group_start = 0
        group_end = 0
        group_tokens = 0
        for sentence in sentence_matches:
            sentence_text = sentence.group(0).strip()
            if not sentence_text:
                continue
            start = sentence.start() + len(sentence.group(0)) - len(sentence.group(0).lstrip())
            end = sentence.end() - (len(sentence.group(0)) - len(sentence.group(0).rstrip()))
            sentence_tokens = count_tokens(sentence_text)
            if group_tokens and group_tokens + sentence_tokens > 180:
                text = para[group_start:group_end]
                units.append(
                    BoundaryUnit(
                        text=text,
                        token_count=count_tokens(text),
                        source_start=para_start + group_start,
                        source_end=para_start + group_end,
                    )
                )
                group_start = start
                group_tokens = 0
            if not group_tokens:
                group_start = start
            group_end = end
            group_tokens += sentence_tokens
        if group_tokens:
            text = para[group_start:group_end]
            units.append(
                BoundaryUnit(
                    text=text,
                    token_count=count_tokens(text),
                    source_start=para_start + group_start,
                    source_end=para_start + group_end,
                )
            )
    return units


def _units_from_section(content: str) -> list[BoundaryUnit]:
    units: list[BoundaryUnit] = []
    for start, end, atomic in _extract_atomic_blocks(content):
        block = content[start:end]
        if atomic:
            edge_start = start + len(block) - len(block.lstrip())
            edge_end = end - (len(block) - len(block.rstrip()))
            text = content[edge_start:edge_end]
            units.append(
                BoundaryUnit(
                    text=text,
                    token_count=count_tokens(text),
                    atomic=True,
                    source_start=edge_start,
                    source_end=edge_end,
                )
            )
            continue
        units.extend(_split_prose_units(block, start))
    return units


def parse_parent_sections(readme_md: str) -> list[ParentSection]:
    """Split README on Markdown headings into parent sections."""
    masked_md = _mask_fenced_blocks(readme_md)
    matches = list(HEADING_RE.finditer(masked_md))
    if not matches:
        start = len(readme_md) - len(readme_md.lstrip())
        end = len(readme_md.rstrip())
        content = readme_md[start:end]
        if not content:
            return []
        return [
            ParentSection(
                heading_path="Document root",
                parent_heading="Document root",
                content=content,
                source_start=start,
                source_end=end,
            )
        ]

    preamble_start = len(readme_md[: matches[0].start()]) - len(
        readme_md[: matches[0].start()].lstrip()
    )
    preamble_end = len(readme_md[: matches[0].start()].rstrip())
    preamble = readme_md[preamble_start:preamble_end]
    sections: list[ParentSection] = []
    if preamble:
        sections.append(
            ParentSection(
                heading_path="Introduction",
                parent_heading="Introduction",
                content=preamble,
                source_start=preamble_start,
                source_end=preamble_end,
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
        raw_start = match.end()
        raw_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(readme_md)
        raw_body = readme_md[raw_start:raw_end]
        start = raw_start + len(raw_body) - len(raw_body.lstrip())
        end = raw_end - (len(raw_body) - len(raw_body.rstrip()))
        body = readme_md[start:end]
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


def _overlap_units(units: list[BoundaryUnit], overlap_tokens: int) -> list[BoundaryUnit]:
    if overlap_tokens <= 0:
        return []
    selected: list[BoundaryUnit] = []
    total = 0
    for unit in reversed(units):
        selected.insert(0, unit)
        total += unit.token_count
        if total >= overlap_tokens:
            break
    return selected


def _pack_units_greedy(
    units: list[BoundaryUnit],
    max_tokens: int,
    overlap_tokens: int,
) -> list[list[BoundaryUnit]]:
    """Paragraph packing fallback when embeddings are unavailable."""
    chunks: list[list[BoundaryUnit]] = []
    current: list[BoundaryUnit] = []
    current_tokens = 0
    for unit in units:
        if unit.atomic and unit.token_count > max_tokens:
            if current:
                chunks.append(current)
                current = []
                current_tokens = 0
            chunks.append([unit])
            continue
        if current and current_tokens + unit.token_count > max_tokens:
            chunks.append(current)
            overlap = _overlap_units(current, overlap_tokens)
            current = [*overlap, unit]
            current_tokens = sum(item.token_count for item in current)
            while len(current) > 1 and current_tokens > max_tokens:
                current_tokens -= current[0].token_count
                current.pop(0)
        else:
            current.append(unit)
            current_tokens += unit.token_count
    if current:
        chunks.append(current)
    return chunks


def _semantic_split_units(
    units: list[BoundaryUnit],
    embed_fn: Callable[[list[str]], list[list[float]]],
    cfg: dict,
) -> list[list[BoundaryUnit]]:
    max_tokens = cfg["child_max_tokens"]
    target_min = cfg["child_target_min"]
    overlap_tokens = cfg["overlap_tokens"]
    threshold = cfg["similarity_threshold"]

    if not units:
        return []

    total_tokens = sum(u.token_count for u in units)
    if total_tokens <= max_tokens:
        return [units]

    texts = [u.text for u in units]
    try:
        vectors = embed_fn(texts)
    except Exception:
        return _pack_units_greedy(units, max_tokens, overlap_tokens)

    if len(vectors) != len(units):
        return _pack_units_greedy(units, max_tokens, overlap_tokens)

    child_groups: list[list[BoundaryUnit]] = []
    group_units: list[BoundaryUnit] = []
    group_vectors: list[list[float]] = []
    group_tokens = 0

    def flush_group() -> None:
        nonlocal group_units, group_vectors, group_tokens
        if not group_units:
            return
        child_groups.append(group_units)
        group_units = []
        group_vectors = []
        group_tokens = 0

    for unit, vec in zip(units, vectors):
        if unit.atomic and unit.token_count > max_tokens:
            flush_group()
            child_groups.append([unit])
            continue

        if not group_units:
            group_units = [unit]
            group_vectors = [vec]
            group_tokens = unit.token_count
            continue

        centroid = _centroid(group_vectors)
        similarity = _cosine_similarity(centroid, vec)
        would_exceed = group_tokens + unit.token_count > max_tokens

        if would_exceed or (group_tokens >= target_min and similarity < threshold):
            previous_units = list(group_units)
            flush_group()
            overlap = _overlap_units(previous_units, overlap_tokens)
            if overlap:
                group_units = list(overlap)
                group_vectors = [vec for _ in overlap]
                group_tokens = sum(item.token_count for item in overlap)
            group_units.append(unit)
            group_vectors.append(vec)
            group_tokens += unit.token_count
        else:
            group_units.append(unit)
            group_vectors.append(vec)
            group_tokens += unit.token_count

    flush_group()
    return child_groups


def _split_parent_into_children(
    parent: ParentSection,
    embed_fn: Callable[[list[str]], list[list[float]]] | None,
    cfg: dict,
) -> tuple[list[BoundaryUnit], list[list[BoundaryUnit]]]:
    units = _units_from_section(parent.content)
    if not units:
        return [], []

    total = sum(u.token_count for u in units)
    if total <= cfg["child_max_tokens"]:
        return units, [units]

    if embed_fn is None:
        return units, _pack_units_greedy(units, cfg["child_max_tokens"], cfg["overlap_tokens"])

    return units, _semantic_split_units(units, embed_fn, cfg)


def _merge_undersized_groups(
    groups: list[list[BoundaryUnit]],
    content: str,
    minimum: int,
    maximum: int,
) -> list[list[BoundaryUnit]]:
    merged: list[list[BoundaryUnit]] = []
    for group in groups:
        if not group:
            continue
        group_tokens = count_tokens(content[group[0].source_start : group[-1].source_end])
        if group_tokens < minimum and merged:
            combined = [*merged[-1], *[unit for unit in group if unit not in merged[-1]]]
            combined.sort(key=lambda unit: (unit.source_start, unit.source_end))
            combined_tokens = count_tokens(
                content[combined[0].source_start : combined[-1].source_end]
            )
            if combined_tokens <= maximum:
                merged[-1] = combined
                continue
        merged.append(group)
    if len(merged) > 1:
        first_tokens = count_tokens(
            content[merged[0][0].source_start : merged[0][-1].source_end]
        )
        combined = [*merged[0], *[unit for unit in merged[1] if unit not in merged[0]]]
        combined.sort(key=lambda unit: (unit.source_start, unit.source_end))
        if first_tokens < minimum and count_tokens(
            content[combined[0].source_start : combined[-1].source_end]
        ) <= maximum:
            merged[:2] = [combined]
    return merged


@instrument("chunk_readme")
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
        units, child_groups = _split_parent_into_children(parent, embed_fn, cfg)
        child_groups = _merge_undersized_groups(
            child_groups,
            parent.content,
            cfg["child_target_min"],
            cfg["child_max_tokens"],
        )
        all_units.extend(units)
        for child_group in child_groups:
            child_start = child_group[0].source_start
            child_end = child_group[-1].source_end
            child_text = parent.content[child_start:child_end]
            token_count = count_tokens(child_text)
            atomic_oversize = (
                len(child_group) == 1
                and child_group[0].atomic
                and token_count > cfg["child_max_tokens"]
            )
            short_reason = None
            if token_count < cfg["child_target_min"]:
                short_reason = (
                    "atomic_unit"
                    if len(child_group) == 1 and child_group[0].atomic
                    else "section_too_short_to_merge"
                )
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
                    source_start=parent.source_start + child_start,
                    source_end=parent.source_start + child_end,
                    chunk_index=chunk_index,
                    short_chunk_reason=short_reason,
                    oversize_reason="atomic_code_or_table" if atomic_oversize else None,
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
    source_chunks: list[ReadmeChunk] | None = None,
    diagnostics: list[dict] | None = None,
) -> list[ReadmeChunk]:
    """Build evidence_claim rows from Phase 1 evidence_card.evidence[]."""
    stack_tags = stack_tags or []
    source_chunks = source_chunks or []
    diagnostics = diagnostics if diagnostics is not None else []
    source_normalized = [_normalize_dedup_text(chunk.content) for chunk in source_chunks]
    accepted_normalized: list[str] = []
    chunks: list[ReadmeChunk] = []
    for i, claim in enumerate(claims):
        claim_text = claim.get("claim") or claim.get("claim", "")
        if not claim_text:
            continue
        source_section = claim.get("source_section") or claim.get("sourceSection", "Evidence")
        content = claim_text.strip()
        normalized = _normalize_dedup_text(content)
        duplicate_reason = next(
            (
                reason
                for source in [*source_normalized, *accepted_normalized]
                if (reason := _duplicate_reason(normalized, source))
            ),
            None,
        )
        diagnostics.append(
            {
                "source_section": source_section,
                "claim_fingerprint": normalized,
                "outcome": "dropped" if duplicate_reason else "retained",
                "reason": duplicate_reason,
            }
        )
        if duplicate_reason:
            continue
        accepted_normalized.append(normalized)
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


def _normalize_dedup_text(text: str) -> str:
    punctuation = str.maketrans({character: " " for character in string.punctuation})
    return re.sub(r"\s+", " ", text.casefold().translate(punctuation)).strip()


def _duplicate_reason(candidate: str, existing: str) -> str | None:
    if not candidate or not existing:
        return None
    if candidate == existing:
        return "exact_duplicate"
    shorter, longer = sorted((candidate, existing), key=len)
    if len(shorter) >= 24 and shorter in longer:
        return "contained_duplicate"
    left = set(candidate.split())
    right = set(existing.split())
    jaccard = len(left & right) / max(1, len(left | right))
    if jaccard >= 0.85 or SequenceMatcher(None, candidate, existing).ratio() >= 0.9:
        return "near_duplicate"
    return None
