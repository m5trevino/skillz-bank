#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

def render_all(project_root):
    diagrams_dir = Path(project_root) / 'docs' / 'diagrams'
    if not diagrams_dir.exists():
        print("No diagrams directory found")
        return False
    
    mmd_files = list(diagrams_dir.glob('*.mmd'))
    if not mmd_files:
        print("No .mmd files to render")
        return False
    
    print(f"Found {len(mmd_files)} Mermaid files")
    
    try:
        result = subprocess.run(['npx', 'mmdc', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("mmdc not found")
    except Exception:
        print("\n⚠️  mermaid-cli not found. Install with:")
        print("   npm install -g @mermaid-js/mermaid-cli")
        print("\nOr open .mmd files in browser:")
        print("   https://mermaid.live")
        return False
    
    success = 0
    for mmd_file in mmd_files:
        png_file = mmd_file.with_suffix('.png')
        print(f"\nRendering {mmd_file.name}...")
        try:
            result = subprocess.run([
                'npx', 'mmdc', 
                '-i', str(mmd_file),
                '-o', str(png_file),
                '-b', 'transparent'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✓ {png_file.name}")
                success += 1
            else:
                print(f"  ✗ Failed: {result.stderr[:100]}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✅ Rendered {success}/{len(mmd_files)} diagrams")
    return success == len(mmd_files)

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    render_all(root)
