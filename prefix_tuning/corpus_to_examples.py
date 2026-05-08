import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def load_corpus_files(corpus_dir = "data/raw/github/"):
    corpus_path = Path(corpus_dir)
    corpus_files = []
    if not corpus_path.exists():
        logger.warning(f"Corpus directory does not exist: {corpus_dir}")
        return corpus_files
    for file_path in corpus_path.glob("*.txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            corpus_files.append((file_path.name, content))
            logger.info(f"Loaded corpus file: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    return corpus_files

def split_corpus_into_chunks(text, chunk_size = 2000, overlap = 200):
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
        if start >= text_len:
            break
    return [c for c in chunks if len(c) > 500]  # Filter very short chunks

def extract_graph_via_api(text, api_url = "http://localhost:8000/extract"):
    try:
        import requests
    except ImportError:
        logger.error("requests library not installed; cannot call API")
        return None
    try:
        response = requests.post(
            api_url,
            json={"text": text},
            timeout=30,
        )
        response.raise_for_status()
        graph = response.json()
        logger.debug(f"Extracted graph with {len(graph.get('nodes', []))} nodes")
        return graph
    except Exception as e:
        logger.error(f"API extraction failed: {e}")
        return None

def extract_graph_locally(text, use_local_extractor = False):
    if not use_local_extractor:
        return None
    try:
        from planninggraph.extractor import extract_decision_graph
        graph_dict = extract_decision_graph(text)
        logger.debug(f"Extracted graph with {len(graph_dict.get('nodes', []))} nodes")
        return graph_dict
    except Exception as e:
        logger.error(f"Local extraction failed: {e}")
        return None

def process_corpus(corpus_dir = "data/raw/github/", output_dir = "data/extracted_graphs/",
    use_api = True, use_local = False, max_files = None):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    corpus_files = load_corpus_files(corpus_dir)
    if max_files:
        corpus_files = corpus_files[:max_files]
    extracted_results = []
    for file_idx, (filename, content) in enumerate(corpus_files):
        logger.info(f"Processing file {file_idx + 1}/{len(corpus_files)}: {filename}")
        chunks = split_corpus_into_chunks(content)
        logger.info(f"  Split into {len(chunks)} chunks")
        for chunk_idx, chunk in enumerate(chunks):
            graph = None
            if use_api:
                graph = extract_graph_via_api(chunk)
            if graph is None and use_local:
                graph = extract_graph_locally(chunk, use_local_extractor=True)
            if graph is None:
                logger.warning(f"  Chunk {chunk_idx}: extraction failed, skipping")
                continue
            
            # Classify graph
            from prefix_tuning.graph_classifier import classify_graph, build_metadata_from_characteristics
            try:
                characteristics = classify_graph(graph)
                metadata = build_metadata_from_characteristics(characteristics)
            except Exception as e:
                logger.error(f"  Chunk {chunk_idx}: classification failed: {e}")
                continue
            result = {
                "corpus_file": filename,
                "chunk_idx": chunk_idx,
                "graph": graph,
                "characteristics": {
                    "risk_profile": characteristics.risk_profile,
                    "complexity_level": characteristics.complexity_level,
                    "frameworks": characteristics.frameworks,
                    "domains": characteristics.domains,
                    "routing_profile": characteristics.routing_profile,
                    "node_count": characteristics.node_count,
                    "edge_count": characteristics.edge_count,
                },
                "metadata": metadata,
                "chunk_text": chunk[:500] + "..." if len(chunk) > 500 else chunk,  # preview
            }
            extracted_results.append(result)
            output_file = Path(output_dir) / f"{filename.replace('.txt', '')}_chunk_{chunk_idx}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logger.debug(f"  Saved: {output_file}")
    logger.info(f"Extraction complete: {len(extracted_results)} graphs extracted")
    return extracted_results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = process_corpus(
        corpus_dir="data/raw/github/",
        output_dir="data/extracted_graphs/",
        use_api=True,
        use_local=True,
        max_files=5,
    )
    print(f"\nExtracted {len(results)} graphs")
    for r in results:
        print(f"  {r['corpus_file']} chunk {r['chunk_idx']}: {r['characteristics']['routing_profile']}")
