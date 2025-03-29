import os
import io
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path

def split_pdf_by_size(input_pdf, target_size=50*1024*1024, output_prefix="_output_part", output_dir=None):
    """
    Splits a PDF file into chunks of target_size (in bytes) and saves them.
    :param input_pdf: Input PDF file path
    :param target_size: Maximum chunk size (default: 50MB)
    :param output_prefix: Output file name prefix
    :param output_dir: Directory to save output files (default: None, current directory)
    :return: List of generated PDF file paths
    """
    # Extract filename without extension from the input file path
    input_filename = os.path.splitext(os.path.basename(input_pdf))[0]
    
    # Output directory setting
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    else:
        output_dir = Path('.')
    
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    current_pages = []  # Pages to be included in the current chunk
    part_index = 1
    output_files = []  # List of generated file paths

    for i, page in enumerate(reader.pages):
        current_pages.append(page)
        
        # Record current chunk in BytesIO to measure size
        writer = PdfWriter()
        for p in current_pages:
            writer.add_page(p)
        temp_io = io.BytesIO()
        writer.write(temp_io)
        current_size = temp_io.tell()
        
        # If current chunk size exceeds target size
        if current_size > target_size:
            # Remove last page and save current chunk
            current_pages.pop()
            writer = PdfWriter()
            for p in current_pages:
                writer.add_page(p)
            output_filename = f"{input_filename}{output_prefix}_{part_index}.pdf"
            output_file = output_dir / output_filename
            with open(output_file, "wb") as f:
                writer.write(f)
            print(f"    - {output_file}: {len(current_pages)} pages, size: {os.path.getsize(output_file)} bytes")
            output_files.append(output_file)
            
            part_index += 1
            # Start new chunk with the page that exceeded the size
            current_pages = [page]
    
    # If there are remaining pages, save them as the last chunk
    if current_pages:
        writer = PdfWriter()
        for p in current_pages:
            writer.add_page(p)
        output_filename = f"{input_filename}{output_prefix}_{part_index}.pdf"
        output_file = output_dir / output_filename
        with open(output_file, "wb") as f:
            writer.write(f)
    print(f"            - {output_file}: {len(current_pages)} pages, size: {os.path.getsize(output_file)} bytes")
    output_files.append(output_file)
    
    return output_files

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python split_pdf.py input.pdf")
        sys.exit(1)
    input_pdf = sys.argv[1]
    split_pdf_by_size(input_pdf)
