import os
import re
import argparse
from pathlib import Path
from collections import defaultdict

def find_markdown_files(vault_path):
    """Find all markdown files in the vault directory."""
    markdown_files = []
    for root, dirs, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    return markdown_files

def extract_note_title(file_path):
    """Extract the title of the note (using filename without extension)."""
    return os.path.splitext(os.path.basename(file_path))[0]

def parse_links(content, file_path):
    """Parse Obsidian-style links in the content."""
    # Match [[Link]] pattern
    wiki_links = re.findall(r'\[\[(.*?)(?:\|.*?)?\]\]', content)
    return wiki_links

def find_text_references(content, note_titles):
    """Find plain text references to other notes (not in link format)."""
    references = []
    for title in note_titles:
        # Avoid short titles (less than 3 chars) to prevent false positives
        if len(title) < 3:
            continue
            
        # Look for exact matches of the title not already in link format
        pattern = r'(?<!\[\[)' + re.escape(title) + r'(?!\]\])'
        if re.search(pattern, content):
            references.append(title)
    
    return references

def generate_backlinks(markdown_files):
    """Generate a map of backlinks for all notes."""
    backlinks = defaultdict(list)
    note_titles = [extract_note_title(f) for f in markdown_files]
    file_title_map = {extract_note_title(f): f for f in markdown_files}
    
    for file_path in markdown_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        source_title = extract_note_title(file_path)
        
        # Find explicit links
        links = parse_links(content, file_path)
        
        # Find text references (optional)
        text_refs = find_text_references(content, note_titles)
        
        # Combine all references
        all_refs = set(links + text_refs)
        
        # Add to backlinks map
        for ref in all_refs:
            if ref in file_title_map:
                target_file = file_title_map[ref]
                backlinks[target_file].append((source_title, file_path))
    
    return backlinks

def update_files_with_backlinks(backlinks, update_mode='append'):
    """Update files with backlinks section."""
    for target_file, references in backlinks.items():
        if not references:
            continue
            
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if backlinks section already exists
        backlink_section_pattern = r'## Backlinks\n\n.*?(?:\n\n|$)'
        existing_section = re.search(backlink_section_pattern, content, re.DOTALL)
        
        # Generate new backlinks section
        new_section = "## Backlinks\n\n"
        for source_title, source_path in references:
            new_section += f"- [[{source_title}]]\n"
        new_section += "\n"
        
        # Update content with new backlinks section
        if existing_section and update_mode == 'replace':
            content = re.sub(backlink_section_pattern, new_section, content, flags=re.DOTALL)
        elif existing_section and update_mode == 'append':
            # Don't do anything, backlinks already exist
            continue
        else:
            # No existing section, append to the end
            if not content.endswith('\n\n'):
                content += '\n\n' if not content.endswith('\n') else '\n'
            content += new_section
        
        # Write updated content back to file
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)

def main():
    parser = argparse.ArgumentParser(description='Generate backlinks for Obsidian vault')
    parser.add_argument('vault_path', help='Path to Obsidian vault directory')
    parser.add_argument('--mode', choices=['append', 'replace'], default='append',
                      help='Mode for updating backlinks (append or replace)')
    parser.add_argument('--text-refs', action='store_true',
                      help='Include plain text references as backlinks')
    args = parser.parse_args()
    
    vault_path = os.path.expanduser(args.vault_path)
    
    print(f"Scanning Obsidian vault at {vault_path}")
    markdown_files = find_markdown_files(vault_path)
    print(f"Found {len(markdown_files)} markdown files")
    
    print("Analyzing links and generating backlinks...")
    backlinks = generate_backlinks(markdown_files)
    
    print("Updating files with backlinks...")
    update_files_with_backlinks(backlinks, args.mode)
    
    print("Done!")

if __name__ == "__main__":
    main()