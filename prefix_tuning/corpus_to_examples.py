"""
Extract DecisionGraphs from corpus files and save intermediate results.

Processes raw corpus text files (from data/raw/github/) and generates DecisionGraph JSON
via the extraction API or local extractor.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def load_corpus_files(corpus_dir: str = "data/raw/github/") -> List[Tuple[str, str]]:
    """
    Load corpus files from directory.
    
    Returns:
        List of (filename, content) tuples
    """
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


def split_corpus_into_chunks(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split corpus text into overlapping chunks for extraction.
    
    This helps:
    - Avoid token limits during extraction
    - Create multiple training examples from one corpus file
    - Capture different planning contexts within large documents
    
    Args:
        text: Full corpus text
        chunk_size: Approximate chars per chunk
        overlap: Overlap between consecutive chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        
        # Move start position, accounting for overlap
        start = end - overlap
        if start >= text_len:
            break
    
    return [c for c in chunks if len(c) > 500]  # Filter very short chunks


def extract_graph_via_api(text: str, api_url: str = "http://localhost:8000/extract") -> Optional[Dict[str, Any]]:
    """
    Extract decision graph from text via FastAPI endpoint.
    
    Requires: api/main.py running on localhost:8000
    
    Args:
        text: Planning text to extract from
        api_url: FastAPI endpoint URL
    
    Returns:
        DecisionGraph dict, or None if extraction failed
    """
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


def extract_graph_locally(
    text: str,
    use_local_extractor: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Extract decision graph from text using local extractor.
    
    Requires: planninggraph/extractor.py and ANTHROPIC_API_KEY
    
    Args:
        text: Planning text to extract from
        use_local_extractor: If True, use local Claude via extractor module
    
    Returns:
        DecisionGraph dict, or None if extraction failed
    """
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


def process_corpus(
    corpus_dir: str = "data/raw/github/",
    output_dir: str = "data/extracted_graphs/",
    use_api: bool = True,
    use_local: bool = False,
    max_files: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Process all corpus files and extract graphs.
    
    Args:
        corpus_dir: Directory containing corpus .txt files
        output_dir: Directory to save extracted graphs
        use_api: Try to use API endpoint first
        use_local: Fall back to local extractor
        max_files: Limit number of files to process
    
    Returns:
        List of (corpus_file, chunk_idx, extracted_graph, characteristics) tuples
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    corpus_files = load_corpus_files(corpus_dir)
    if max_files:
        corpus_files = corpus_files[:max_files]
    
    extracted_results = []
    
    for file_idx, (filename, content) in enumerate(corpus_files):
        logger.info(f"Processing file {file_idx + 1}/{len(corpus_files)}: {filename}")
        
        # Split into chunks
        chunks = split_corpus_into_chunks(content)
        logger.info(f"  Split into {len(chunks)} chunks")
        
        for chunk_idx, chunk in enumerate(chunks):
            # Try extraction
            graph = None
            if use_api:
                graph = extract_graph_via_api(chunk)
            if graph is None and use_local:
                graph = extract_graph_locally(chunk, use_local_extractor=True)
            
            if graph is None:
                logger.warning(f"  Chunk {chunk_idx}: extraction failed, skipping")
                continue
            
            # Classify graph
            from graph_classifier import classify_graph, build_metadata_from_characteristics
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
            
            # Save individual graph
            output_file = Path(output_dir) / f"{filename.replace('.txt', '')}_chunk_{chunk_idx}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logger.debug(f"  Saved: {output_file}")
    
    logger.info(f"Extraction complete: {len(extracted_results)} graphs extracted")
    return extracted_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Process corpus with API
    results = process_corpus(
        corpus_dir="data/raw/github/",
        output_dir="data/extracted_graphs/",
        use_api=True,
        use_local=True,
        max_files=5,
    )
    
    print(f"\nExtracted {len(results)} graphs")
    for r in results:
        print(f"  {r['corpus_file']} chunk {r['chunk_idx']}: "
              f"{r['characteristics']['routing_profile']}")
