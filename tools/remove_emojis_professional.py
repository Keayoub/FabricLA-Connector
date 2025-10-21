"""
Professional Emoji Removal Tool
Removes all emojis from Python source files and replaces them with professional text equivalents.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Emoji to professional text mapping
EMOJI_REPLACEMENTS: Dict[str, str] = {
    # Status indicators
    '✅': 'SUCCESS:',
    '❌': 'ERROR:',
    '⚠️': 'WARNING:',
    '🟢': '[ACTIVE]',
    '🔴': '[STOPPED]',
    '🟡': '[PENDING]',
    '⚪': '[IDLE]',
    '⚙': '[CONFIG]',
    
    # Information and progress
    '🔍': 'INFO: Collecting',
    'ℹ️': 'INFO:',
    '📊': 'Found',
    '💡': 'TIP:',
    '📋': 'INFO:',
    '🎯': 'TARGET:',
    '🎉': 'COMPLETE:',
    
    # Actions and operations
    '🚀': 'STARTING:',
    '🔧': 'FIXING:',
    '🔥': 'CRITICAL:',
    '⚡': 'FAST:',
    '⏱️': 'TIMING:',
    '🤖': 'AGENT:',
    '🧠': 'AI:',
    
    # Resources and items
    '💻': 'COMPUTE:',
    '📈': 'METRICS:',
    '🏠': 'HOME:',
    '📓': 'NOTEBOOK:',
    '📒': 'NOTEBOOK:',
    '📦': 'PACKAGE:',
    '📝': 'NOTE:',
    '📤': 'OUTPUT:',
    '🔗': 'LINK:',
    '⏭️': 'NEXT:',
    '🗄': 'DATABASE:',
    '🔐': 'SECURE:',
}


def remove_emojis_from_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Remove all emojis from a single file and replace with professional text.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (replacements_made, list_of_changes)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    replacements_made = 0
    
    # Replace each emoji with its professional text equivalent
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        if emoji in content:
            count = content.count(emoji)
            if count > 0:
                content = content.replace(emoji, replacement)
                replacements_made += count
                changes.append(f"  - Replaced {count}x '{emoji}' with '{replacement}'")
    
    # Additional cleanup: Handle duplicate markers (e.g., "ERROR: ERROR:")
    # This can happen if emoji was already preceded by text
    content = re.sub(r'(SUCCESS:|ERROR:|WARNING:|INFO:)\s*\1', r'\1', content)
    
    # Clean up spacing issues around replacements
    content = re.sub(r'(\w)\s+(SUCCESS:|ERROR:|WARNING:|INFO:|TIP:|Found)', r'\1 \2', content)
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return replacements_made, changes


def process_directory(root_dir: Path) -> None:
    """
    Process all Python files in a directory tree.
    
    Args:
        root_dir: Root directory to start processing
    """
    total_files = 0
    total_replacements = 0
    files_modified = []
    
    print("=" * 80)
    print("PROFESSIONAL EMOJI REMOVAL TOOL")
    print("=" * 80)
    print(f"\nScanning directory: {root_dir}")
    print()
    
    # Find all Python files
    python_files = list(root_dir.rglob('*.py'))
    print(f"Found {len(python_files)} Python files to process\n")
    
    # Process each file
    for file_path in python_files:
        total_files += 1
        replacements, changes = remove_emojis_from_file(file_path)
        
        if replacements > 0:
            total_replacements += replacements
            files_modified.append((file_path, replacements, changes))
            print(f"[MODIFIED] {file_path.relative_to(root_dir)}")
            for change in changes:
                print(change)
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files scanned: {total_files}")
    print(f"Files modified: {len(files_modified)}")
    print(f"Total emoji replacements: {total_replacements}")
    
    if files_modified:
        print("\nModified files:")
        for file_path, count, _ in files_modified:
            print(f"  - {file_path.relative_to(root_dir)}: {count} replacements")
    
    print("\n" + "=" * 80)
    print("COMPLETE - All emojis replaced with professional text")
    print("=" * 80)


def verify_no_emojis(root_dir: Path) -> None:
    """
    Verify that no emojis remain in the Python files.
    
    Args:
        root_dir: Root directory to check
    """
    print("\n" + "=" * 80)
    print("VERIFICATION - Checking for remaining emojis")
    print("=" * 80 + "\n")
    
    # Unicode ranges for common emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"  # Misc Symbols and Pictographs
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F680-\U0001F6FF"  # Transport and Map
        "\U00002600-\U000027BF"  # Misc symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "]+", 
        flags=re.UNICODE
    )
    
    found_emojis = []
    
    for file_path in root_dir.rglob('*.py'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        matches = emoji_pattern.findall(content)
        if matches:
            found_emojis.append((file_path, matches))
    
    if found_emojis:
        print(f"WARNING: Found {len(found_emojis)} files with remaining emojis:")
        for file_path, emojis in found_emojis:
            print(f"  - {file_path.relative_to(root_dir)}: {set(emojis)}")
    else:
        print("SUCCESS: No emojis found - all files are professionally formatted")
    
    print()


if __name__ == '__main__':
    # Process the src directory
    src_dir = Path(__file__).parent.parent / 'src'
    
    if not src_dir.exists():
        print(f"ERROR: Directory not found: {src_dir}")
        exit(1)
    
    # Remove emojis
    process_directory(src_dir)
    
    # Verify cleanup
    verify_no_emojis(src_dir)
