# simple_test.py - Simple direct test

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

print("=== Testing Metadata Parser ===")
print(f"Project root: {project_root}")
print(f"Source path: {src_path}")

# Try to import
try:
    from udio_media_manager.services.metadata_parser import MetadataParser
    print("✅ Import successful")
    
    # Try to create instance
    parser = MetadataParser()
    print("✅ Parser instance created")
    
    # Try to see what methods exist
    methods = [m for m in dir(parser) if not m.startswith('_')]
    print(f"Parser methods: {methods}")
    
    # Create a simple test file
    test_content = "Title: Simple Test\nArtist: Test Artist"
    test_file = Path("simple_test.txt")
    test_file.write_text(test_content)
    
    print("✅ Test file created")
    
    # Try to parse
    try:
        result = parser.parse_txt_file(test_file)
        print(f"✅ Parse successful: {result}")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print("✅ Test file cleaned up")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()

print("=== Test Complete ===")