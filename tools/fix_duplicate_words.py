"""
Fix Duplicate Words After Emoji Removal
Cleans up duplicate words that appeared after emoji replacement.
"""
import re
from pathlib import Path
from typing import List, Tuple


def fix_duplicate_words(file_path: Path) -> Tuple[int, List[str]]:
    """
    Fix duplicate words in log messages.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (fixes_made, list_of_changes)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    fixes_made = 0
    
    # Common patterns after emoji removal that create duplicates
    duplicate_patterns = [
        # "INFO: Collecting Collecting" -> "INFO: Collecting"
        (r'(INFO: Collecting)\s+Collecting\b', r'\1'),
        (r'(INFO: Collecting)\s+collecting\b', r'\1'),
        
        # "Found Found" -> "Found"
        (r'\bFound\s+Found\b', 'Found'),
        
        # "SUCCESS: SUCCESS:" -> "SUCCESS:"
        (r'(SUCCESS:|ERROR:|WARNING:|INFO:|TIP:)\s+\1', r'\1'),
        
        # "ERROR: ERROR" -> "ERROR:"
        (r'(SUCCESS|ERROR|WARNING|INFO|TIP):\s+\1\b', r'\1:'),
        
        # General duplicate word pattern (but be careful with intentional duplicates)
        # Only fix if it's at the start of a string or after quotes
        (r'(["\'])(SUCCESS|ERROR|WARNING|INFO|TIP|Found|Collecting):\s+\2\b', r'\1\2:'),
        
        # Fix cases like: print(f"INFO: Collecting Collecting...")
        (r'print\(f?"(INFO|WARNING|ERROR|SUCCESS|TIP):\s+(Collecting|Found|Processing)\s+\2\b', 
         r'print(f"\1: \2'),
    ]
    
    for pattern, replacement in duplicate_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            before_count = len(matches)
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            fixes_made += before_count
            changes.append(f"  - Fixed {before_count} instances of pattern: {pattern[:50]}...")
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes_made, changes


def process_directory(root_dir: Path) -> None:
    """
    Process all Python files in a directory tree.
    
    Args:
        root_dir: Root directory to process
    """
    print("=" * 80)
    print("FIX DUPLICATE WORDS AFTER EMOJI REMOVAL")
    print("=" * 80)
    print(f"\nProcessing directory: {root_dir}\n")
    
    total_files = 0
    total_fixes = 0
    files_modified = []
    
    for py_file in root_dir.rglob('*.py'):
        total_files += 1
        fixes_made, changes = fix_duplicate_words(py_file)
        
        if fixes_made > 0:
            total_fixes += fixes_made
            files_modified.append((py_file, fixes_made, changes))
            print(f"[MODIFIED] {py_file.relative_to(root_dir)}")
            for change in changes:
                print(change)
            print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files scanned: {total_files}")
    print(f"Files modified: {len(files_modified)}")
    print(f"Total fixes applied: {total_fixes}")
    print("\n" + "=" * 80)
    print("COMPLETE - All duplicate words fixed")
    print("=" * 80)


if __name__ == '__main__':
    src_dir = Path(__file__).parent.parent / 'src'
    
    if not src_dir.exists():
        print(f"ERROR: Directory not found: {src_dir}")
        exit(1)
    
    process_directory(src_dir)
