import os
import json
import argparse
from tabulate import tabulate
from datetime import datetime

def load_json_data(json_path):
    """
    Load JSON data from file
    
    Args:
        json_path (str): Path to the JSON file
        
    Returns:
        dict: Loaded JSON data
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def display_metadata(metadata):
    """
    Display metadata from the JSON file
    
    Args:
        metadata (dict): Metadata dictionary
    """
    print("\n=== 메타데이터 ===")
    print(f"원본 파일: {metadata.get('source_file', 'N/A')}")
    print(f"추출 일시: {metadata.get('extraction_date', 'N/A')}")
    print(f"항목 수: {metadata.get('entries_count', 0)}")
    print(f"이미지 디렉토리: {metadata.get('image_directory', 'N/A')}")
    print()

def display_entries_summary(entries):
    """
    Display a summary of the entries
    
    Args:
        entries (list): List of entry dictionaries
    """
    summary_data = []
    
    for i, entry in enumerate(entries):
        # Get a subset of fields for the summary
        summary_row = [
            i + 1,
            entry.get("라인", ""),
            entry.get("설비번호", ""),
            entry.get("설비명", ""),
            entry.get("작업 일자", ""),
            entry.get("담당자", ""),
            entry.get("작업명", ""),
            len(entry.get("작업사진", [])),
            entry.get("페이지번호", "")
        ]
        summary_data.append(summary_row)
    
    headers = ["번호", "라인", "설비번호", "설비명", "작업일자", "담당자", "작업명", "이미지 수", "페이지"]
    
    print("\n=== 항목 요약 ===")
    print(tabulate(summary_data, headers=headers, tablefmt="grid"))
    print()

def display_entry_details(entry, index, output_dir=None):
    """
    Display detailed information about a specific entry
    
    Args:
        entry (dict): Entry dictionary
        index (int): Entry index
        output_dir (str): Output directory for image paths
    """
    print(f"\n=== 항목 #{index+1} 상세정보 ===")
    
    # Display all fields except images and image descriptions
    for field, value in entry.items():
        if field not in ["작업사진", "이미지설명"]:
            print(f"{field}: {value}")
    
    # Display image information with descriptions
    images = entry.get("작업사진", [])
    image_descriptions = entry.get("이미지설명", {})
    print(f"\n이미지 ({len(images)}개):")
    
    if output_dir and images:
        image_dir = os.path.join(output_dir, "images")
        for i, img in enumerate(images):
            img_path = os.path.join(image_dir, img)
            exists = os.path.exists(img_path)
            status = "존재함" if exists else "찾을 수 없음"
            size = os.path.getsize(img_path) if exists else 0
            print(f"  {i+1}. {img} ({status}, {size/1024:.1f} KB)")
            
            # Display image description if available
            description = image_descriptions.get(img, "")
            if description:
                # Format the description with proper indentation and word wrapping
                wrapped_desc = '\n    '.join([line.strip() for line in description.split('\n')])
                print(f"    설명: {wrapped_desc}")
    else:
        for i, img in enumerate(images):
            print(f"  {i+1}. {img}")
            # Display image description if available
            description = image_descriptions.get(img, "")
            if description:
                # Format the description with proper indentation and word wrapping
                wrapped_desc = '\n    '.join([line.strip() for line in description.split('\n')])
                print(f"    설명: {wrapped_desc}")
            
    print("\n" + "="*50 + "\n")

def list_all_json_files(output_dir):
    """
    List all JSON files in the output directory
    
    Args:
        output_dir (str): Path to the output directory
        
    Returns:
        list: List of JSON file paths
    """
    json_files = []
    for file in os.listdir(output_dir):
        if file.endswith('.json'):
            json_files.append(os.path.join(output_dir, file))
    return json_files

def main():
    parser = argparse.ArgumentParser(description="View extracted JSON data from PDF converter")
    parser.add_argument("--json", help="Path to the JSON file", default=None)
    parser.add_argument("--details", help="Show detailed information for specific entry (index)", type=int, default=None)
    parser.add_argument("--all", help="Show detailed information for all entries", action="store_true")
    parser.add_argument("--list", help="List all available JSON files", action="store_true")
    args = parser.parse_args()
    
    # Determine JSON file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir) if script_dir.endswith('scripts') else script_dir
    output_dir = os.path.join(workspace_dir, "output")
    
    # List all JSON files if requested
    if args.list:
        json_files = list_all_json_files(output_dir)
        if json_files:
            print("\n=== 사용 가능한 JSON 파일 ===")
            for i, file_path in enumerate(json_files):
                print(f"  {i+1}. {os.path.basename(file_path)}")
            print("\n사용법: python view_json_results.py --json <json_file_path>")
        else:
            print(f"No JSON files found in {output_dir}")
        return
    
    # Use specified JSON file or default
    json_path = args.json
    if not json_path:
        # Look for default file name or first JSON in directory
        default_path = os.path.join(output_dir, "일일업무일지.json")
        if os.path.exists(default_path):
            json_path = default_path
        else:
            # Use first JSON file found
            json_files = list_all_json_files(output_dir)
            if json_files:
                json_path = json_files[0]
                print(f"Using first available JSON file: {os.path.basename(json_path)}")
            else:
                print(f"No JSON files found in {output_dir}")
                print("Use --list to see available JSON files or specify a path with --json")
                return
    
    # Load JSON data
    data = load_json_data(json_path)
    if not data:
        print(f"Could not load JSON data from {json_path}")
        return
    
    print(f"Viewing data from: {os.path.basename(json_path)}")
    
    # Display metadata
    if "metadata" in data:
        display_metadata(data["metadata"])
    
    # Get entries
    entries = data.get("entries", data)  # Handle both formats
    if not entries:
        print("No entries found in the JSON data")
        return
    
    # Display summary
    display_entries_summary(entries)
    
    # Display details if requested
    if args.details is not None and 0 <= args.details < len(entries):
        display_entry_details(entries[args.details], args.details, output_dir)
    elif args.all:
        for i, entry in enumerate(entries):
            display_entry_details(entry, i, output_dir)

if __name__ == "__main__":
    main() 