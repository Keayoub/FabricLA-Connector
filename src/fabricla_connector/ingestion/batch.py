"""
Batching and chunking utilities for ingestion.
"""
from typing import List, Dict, Any, Iterator


def chunk_records(records: List[Dict[str, Any]], chunk_size: int) -> Iterator[List[Dict[str, Any]]]:
    """
    Split records into chunks of specified size.
    
    Args:
        records: List of records to chunk
        chunk_size: Maximum size of each chunk
        
    Yields:
            Chunks of records
    """
    for i in range(0, len(records), chunk_size):
        yield records[i:i + chunk_size]


def estimate_payload_size(records: List[Dict[str, Any]]) -> int:
    """
    Estimate payload size in bytes for a list of records.
    
    Args:
        records: List of records
        
    Returns:
        Estimated size in bytes
    """
    import json
    try:
        # Serialize to JSON to get accurate size
        return len(json.dumps(records).encode('utf-8'))
    except:
        # Fallback: rough estimate
        return sum(len(str(r)) for r in records)


def split_by_size(records: List[Dict[str, Any]], max_size_bytes: int = 1_000_000) -> List[List[Dict[str, Any]]]:
    """
    Split records into batches that don't exceed max size.
    
    The Logs Ingestion API has a 1MB limit per request.
    
    Args:
        records: List of records to split
        max_size_bytes: Maximum size per batch (default 1MB)
        
    Returns:
        List of record batches
    """
    import json
    
    batches = []
    current_batch = []
    current_size = 0
    
    for record in records:
        record_size = len(json.dumps(record).encode('utf-8'))
        
        # If single record exceeds limit, add it alone (will fail but we want to track it)
        if record_size > max_size_bytes:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_size = 0
            batches.append([record])
            continue
        
        # If adding this record would exceed limit, start new batch
        if current_size + record_size > max_size_bytes:
            batches.append(current_batch)
            current_batch = [record]
            current_size = record_size
        else:
            current_batch.append(record)
            current_size += record_size
    
    # Add final batch if not empty
    if current_batch:
        batches.append(current_batch)
    
    return batches
