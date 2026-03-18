"""
Exploratory data analysis over the fetched corpus.

Run after fetch_corpus.py has populated data/raw/.

Phases:
  1. Linguistic hedge detection (Assumption node signal)
  2. Node-type keyword density across corpus tiers
  3. Dependency verb patterns (depends_on / consumes edge signal)
  4. Uncategorized sentences (unknown-unknown discovery)

Outputs to data/eda_outputs/:
  hedge_sentences.tsv
  node_type_distribution.json
  dependency_patterns.json
  uncategorized_sample.txt
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "eda_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

HEDGE_PATTERNS: dict[str, list[str]] = {
    "epistemic_modal": [
        r"\bwe assume\b",
        r"\bassuming\b",
        r"\bwe believe\b",
        r"\bprobably\b",
        r"\blikely\b",
        r"\bshould be\b",
        r"\bpresumably\b",
    ],
    "conditional": [
        r"\bif .{0,40} then\b",
        r"\bprovided that\b",
        r"\bas long as\b",
        r"\bgiven that\b",
        r"\bonly if\b",
    ],
    "confidence_qualifier": [
        r"\bin theory\b",
        r"\bin principle\b",
        r"\bideally\b",
        r"\bfor now\b",
        r"\bgood enough\b",
        r"\bsufficient for\b",
        r"\bfor the time being\b",
    ],
    "scope_hedge": [
        r"\bfor our use case\b",
        r"\bin most cases\b",
        r"\bin the common case\b",
        r"\bfor the most part\b",
        r"\bin practice\b",
        r"\bin general\b",
    ],
}

NODE_KEYWORDS: dict[str, list[str]] = {
    "objective": [
        r"\bgoal\b",
        r"\baim\b",
        r"\bpurpose\b",
        r"\bwe want to\b",
        r"\bthe system (should|will|shall)\b",
        r"\bour mission\b",
        r"\bwe need to achieve\b",
    ],
    "requirement": [
        r"\bmust\b",
        r"\bshall\b",
        r"\brequired\b",
        r"\bneeds? to\b",
        r"\bconstraint\b",
        r"\bmandatory\b",
        r"\bhas to\b",
        r"\bexpected to\b",
    ],
    "assumption": [
        r"\bwe assume\b",
        r"\bassuming\b",
        r"\bwe believe\b",
        r"\btake for granted\b",
        r"\bexpect that\b",
        r"\bwe (expect|assumed)\b",
    ],
    "decision": [
        r"\bwe decided\b",
        r"\bwe chose\b",
        r"\bwe went with\b",
        r"\bwe opted for\b",
        r"\binstead of\b",
        r"\bwe use .{0,20} rather than\b",
        r"\bwe selected\b",
        r"\bwe picked\b",
        r"\bwe rejected\b",
    ],
    "component": [
        r"\bmodule\b",
        r"\bservice\b",
        r"\blibrary\b",
        r"\blayer\b",
        r"\bdaemon\b",
        r"\bworker\b",
        r"\bhandler\b",
        r"\bsubsystem\b",
        r"\bpackage\b",
        r"\bplugin\b",
        r"\bcomponent\b",
    ],
    "interface": [
        r"\bapi\b",
        r"\bcontract\b",
        r"\bprotocol\b",
        r"\bendpoint\b",
        r"\bschema\b",
        r"\binterface\b",
        r"\bspecification\b",
        r"\bformat\b",
        r"\bsignature\b",
    ],
    "risk": [
        r"\brisk\b",
        r"\bconcern\b",
        r"\bmight fail\b",
        r"\bcould break\b",
        r"\bbottleneck\b",
        r"\bcaveat\b",
        r"\btradeoff\b",
        r"\bdownside\b",
        r"\bdrawback\b",
        r"\blimitation\b",
        r"\bworry\b",
        r"\bdanger\b",
    ],
}

DEPENDENCY_VERBS: list[str] = [
    r"depends on",
    r"requires",
    r"\buses\b",
    r"calls",
    r"imports from",
    r"is consumed by",
    r"feeds into",
    r"is backed by",
    r"relies on",
    r"is built on",
    r"wraps",
    r"delegates to",
    r"inherits from",
    r"extends",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Sentence:
    source: str   # tier dir name: github, postmortems, stackoverflow
    doc_id: str
    text: str
    matched_types: dict[str, list[str]] = field(default_factory=dict)
    matched_hedges: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Corpus loading + sentence tokenization
# ---------------------------------------------------------------------------

def tokenize_sentences(text: str) -> list[str]:
    """Naive sentence tokenizer — splits on punctuation + newlines."""
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])|[\n]{2,}', text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 6]


def load_corpus() -> list[tuple[str, str, str]]:
    """Returns list of (tier, doc_id, text) for all documents in data/raw/."""
    docs = []
    if not RAW_DIR.exists():
        return docs
    for tier_dir in sorted(RAW_DIR.iterdir()):
        if not tier_dir.is_dir():
            continue
        tier = tier_dir.name
        for f in sorted(tier_dir.rglob("*.txt")):
            try:
                text = f.read_text(errors="ignore").strip()
            except OSError:
                continue
            if text:
                doc_id = str(f.relative_to(RAW_DIR))
                docs.append((tier, doc_id, text))
    return docs


# ---------------------------------------------------------------------------
# Analysis phases
# ---------------------------------------------------------------------------

def phase1_hedge_detection(sentences: list[Sentence]) -> list[dict]:
    """Detect linguistic hedges as signal for Assumption nodes."""
    hits = []
    for s in sentences:
        for category, patterns in HEDGE_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, s.text, re.IGNORECASE):
                    s.matched_hedges.setdefault(category, []).append(pat)
                    hits.append({
                        "source": s.source,
                        "doc_id": s.doc_id,
                        "category": category,
                        "pattern": pat,
                        "sentence": s.text[:300],
                    })
    return hits


def phase2_keyword_density(
    docs: list[tuple[str, str, str]],
    sentences: list[Sentence],
) -> dict:
    """
    Node-type keyword density (hits per 1000 words) per corpus tier.
    Also marks matched_types on each sentence for Phase 4.
    """
    # density[tier][node_type] = list of per-doc densities
    density: dict[str, dict[str, list[float]]] = {}

    for source, doc_id, text in docs:
        tier = source
        wc = max(1, len(text.split()))
        if tier not in density:
            density[tier] = {t: [] for t in NODE_KEYWORDS}

        for node_type, patterns in NODE_KEYWORDS.items():
            count = sum(
                len(re.findall(pat, text, re.IGNORECASE))
                for pat in patterns
            )
            density[tier][node_type].append(count / wc * 1000)

    # Mark matched types on sentences (used by Phase 4)
    for s in sentences:
        for node_type, patterns in NODE_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, s.text, re.IGNORECASE):
                    s.matched_types.setdefault(node_type, []).append(pat)

    # Summarise to mean per tier per type
    summary: dict[str, dict[str, float]] = {}
    for tier, type_densities in density.items():
        summary[tier] = {}
        for node_type, vals in type_densities.items():
            summary[tier][node_type] = round(sum(vals) / len(vals), 4) if vals else 0.0

    return summary


def phase3_dependency_patterns(sentences: list[Sentence]) -> dict:
    """Count dependency verb occurrences as signal for depends_on / consumes edges."""
    counts: dict[str, int] = {}
    for s in sentences:
        for verb_pat in DEPENDENCY_VERBS:
            for match in re.finditer(verb_pat, s.text, re.IGNORECASE):
                verb = match.group(0).lower().strip()
                counts[verb] = counts.get(verb, 0) + 1

    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
    return {
        "top_patterns": [
            {"verb": v, "count": c} for v, c in sorted_counts[:20]
        ]
    }


def phase4_uncategorized(sentences: list[Sentence], n: int = 50) -> list[str]:
    """
    Sample sentences with zero keyword/hedge matches.

    These are the "unknown unknowns" — if you keep seeing the same kind
    of concept in this list that doesn't fit any node type, that's a
    schema gap candidate. Review manually at the schema review meeting.
    """
    uncategorized = [
        s for s in sentences
        if not s.matched_types
        and not s.matched_hedges
        and len(s.text.split()) >= 8
    ]
    random.seed(42)
    sample = random.sample(uncategorized, min(n, len(uncategorized)))
    return [f"[{s.source} / {s.doc_id}]\n  {s.text[:250]}\n" for s in sample]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _print_bar(label: str, value: float, max_width: int = 30, scale: float = 1.0) -> None:
    bar_len = min(max_width, int(value * scale))
    bar = "█" * bar_len
    print(f"  {label:<15} {value:6.3f}  {bar}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading corpus...")
    docs = load_corpus()
    if not docs:
        print("\nNo documents found in data/raw/.")
        print("Run:  python scripts/fetch_corpus.py")
        return

    # Count by tier
    tier_counts: dict[str, int] = {}
    for tier, _, _ in docs:
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    print(f"Loaded {len(docs)} documents across {len(tier_counts)} tiers:")
    for tier, cnt in sorted(tier_counts.items()):
        print(f"  {tier}: {cnt}")

    # Build sentence list
    sentences: list[Sentence] = []
    for tier, doc_id, text in docs:
        for sent_text in tokenize_sentences(text):
            sentences.append(Sentence(source=tier, doc_id=doc_id, text=sent_text))
    print(f"Total sentences: {len(sentences)}\n")

    # ------------------------------------------------------------------
    # Phase 1: Hedge detection
    # ------------------------------------------------------------------
    print("Phase 1: Hedge detection...")
    hedge_hits = phase1_hedge_detection(sentences)

    hedge_tsv = OUT_DIR / "hedge_sentences.tsv"
    with hedge_tsv.open("w") as f:
        f.write("source\tdoc_id\tcategory\tpattern\tsentence\n")
        for h in hedge_hits:
            row = "\t".join([h["source"], h["doc_id"], h["category"], h["pattern"], h["sentence"].replace("\t", " ")])
            f.write(row + "\n")

    hedge_by_cat: dict[str, int] = {}
    for h in hedge_hits:
        hedge_by_cat[h["category"]] = hedge_by_cat.get(h["category"], 0) + 1

    # ------------------------------------------------------------------
    # Phase 2: Keyword density
    # ------------------------------------------------------------------
    print("Phase 2: Keyword density...")
    density = phase2_keyword_density(docs, sentences)

    density_path = OUT_DIR / "node_type_distribution.json"
    density_path.write_text(json.dumps(density, indent=2))

    # ------------------------------------------------------------------
    # Phase 3: Dependency patterns
    # ------------------------------------------------------------------
    print("Phase 3: Dependency patterns...")
    dep_patterns = phase3_dependency_patterns(sentences)

    dep_path = OUT_DIR / "dependency_patterns.json"
    dep_path.write_text(json.dumps(dep_patterns, indent=2))

    # ------------------------------------------------------------------
    # Phase 4: Uncategorized sentences
    # ------------------------------------------------------------------
    print("Phase 4: Uncategorized sentence sampling...")
    uncategorized_sentences = [
        s for s in sentences
        if not s.matched_types and not s.matched_hedges and len(s.text.split()) >= 8
    ]
    sample_lines = phase4_uncategorized(sentences)

    uncategorized_path = OUT_DIR / "uncategorized_sample.txt"
    uncategorized_path.write_text(
        "=== Uncategorized Sentences (manual review) ===\n"
        "These had zero hits across all node type keyword and hedge pattern lists.\n"
        "If you keep seeing the same concept here, consider adding it to the schema.\n\n"
        + "\n".join(sample_lines)
    )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    # Aggregate density across all tiers
    all_density: dict[str, list[float]] = {}
    for tier_data in density.values():
        for node_type, d in tier_data.items():
            all_density.setdefault(node_type, []).append(d)

    sorted_density = sorted(all_density.items(), key=lambda x: -_mean(x[1]))
    rarest = sorted_density[-1][0] if sorted_density else "?"

    print("\n" + "=" * 60)
    print("=== EDA Summary ===")
    print(f"Documents analyzed:  {len(docs)}")
    for tier, cnt in sorted(tier_counts.items()):
        print(f"  {tier}: {cnt}")
    print(f"\nTotal sentences:     {len(sentences)}")
    print(f"Hedge sentences:     {len(hedge_hits)}")
    if hedge_by_cat:
        top_cat = max(hedge_by_cat, key=lambda k: hedge_by_cat[k])
        print(f"  Top category:    {top_cat} ({hedge_by_cat[top_cat]} hits)")
        for cat, cnt in sorted(hedge_by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<25} {cnt}")

    print(f"\nNode keyword density (mean per 1k words across tiers):")
    scale = 200.0 / max((_mean(v) for v in all_density.values()), default=1.0)
    for node_type, vals in sorted_density:
        _print_bar(node_type, _mean(vals), scale=scale)
    print(f"\n  ⚠  Rarest type: '{rarest}' — annotation guidelines should actively surface these.")

    top5_verbs = [p["verb"] for p in dep_patterns["top_patterns"][:5]]
    print(f"\nTop dependency verbs: {', '.join(top5_verbs)}")

    print(f"\nUncategorized sentences: {len(uncategorized_sentences)} total")
    print(f"  → {len(sample_lines)} sampled to {uncategorized_path.name}")
    print(f"    Review this file to spot schema gaps (unknown unknowns).")

    print(f"\nOutputs written to: {OUT_DIR}/")
    print(f"  hedge_sentences.tsv")
    print(f"  node_type_distribution.json")
    print(f"  dependency_patterns.json")
    print(f"  uncategorized_sample.txt")
    print("=" * 60)


if __name__ == "__main__":
    main()
