#!/usr/bin/env python3
# PDF OCR to Markdown Converter for Obsidian
# This script processes PDF files using Mistral AI's OCR service and converts them to Markdown format
# suitable for use in Obsidian with properly formatted image links.

import json
import base64
import shutil
import os
from pathlib import Path
from mistralai import Mistral, DocumentURLChunk
from dotenv import load_dotenv
from split_pdf import split_pdf_by_size

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    # Fallback to hardcoded API key (not recommended for security reasons)
    api_key = "your_api_key_here"
    print("API 키가 환경 변수에 없습니다. 기본값을 사용합니다.")
else:
    print(f"API 키를 환경 변수에서 불러왔습니다: {api_key[:5]}...")

# Validate API Key
try:
    client = Mistral(api_key=api_key)
    # Validate API key using models property
    models = client.models.list()
    print("API 키 유효성 검사에 성공했습니다")
    # print(f"Available models: {[model.id for model in models.data]}")
except Exception as e:
    print(f"API 키 유효성 검사에 실패했습니다: {str(e)}")
    exit(1)

# Print API key information (masked)
print(f"API 키를 사용합니다: {api_key[:5]}...")

# Define directories
INPUT_DIR = Path("pdfs_to_process")   # Folder where the user places the PDFs to be processed
DONE_DIR = Path("pdfs-done")          # Folder where processed PDFs will be moved
OUTPUT_ROOT_DIR = Path("ocr_output")  # Root folder for conversion results

# Ensure directories exist
INPUT_DIR.mkdir(exist_ok=True)
DONE_DIR.mkdir(exist_ok=True)
OUTPUT_ROOT_DIR.mkdir(exist_ok=True)

# Maximum size for PDF files (in bytes)
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """
    This function replaces base64 encoded images directly in the markdown...
    """
    for image_id, image_data in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{image_id}]({image_id})",
            f"![{image_id}]({image_data})"
        )
    return markdown_str

def get_combined_markdown(markdown_list: list) -> str:
    """
    This function combines multiple markdown strings into a single string
    """
    markdowns = []
    for markdown in markdown_list:
        markdowns.append(markdown)
    
    return "\n\n".join(markdowns)

def process_image(image_obj, pdf_base, counter, images_dir):
    """
    This function processes a single image from OCR response and saves it to disk
    Returns: (new_image_name, updated_counter)
    """
    # base64 to image
    base64_str = image_obj.image_base64
    if base64_str.startswith("data:"):
        base64_str = base64_str.split(",", 1)[1]
    image_bytes = base64.b64decode(base64_str)
    
    # image extensions
    ext = Path(image_obj.id).suffix if Path(image_obj.id).suffix else ".png"
    new_image_name = f"{pdf_base}_img_{counter}{ext}"
    
    # save in subfolder
    image_output_path = images_dir / new_image_name
    with open(image_output_path, "wb") as f:
        f.write(image_bytes)
    
    return new_image_name, counter + 1

def process_ocr_response(ocr_response, pdf_base, images_dir, start_counter=1):
    """
    This function processes OCR response to extract images and create markdown
    Returns: (markdown_pages, final_counter)
    """
    counter = start_counter
    markdown_pages = []
    
    for page in ocr_response.pages:
        updated_markdown = page.markdown
        for image_obj in page.images:
            new_image_name, counter = process_image(image_obj, pdf_base, counter, images_dir)
            
            # Update markdown with wikilink: ![[nombre_imagen]]
            updated_markdown = updated_markdown.replace(
                f"![{image_obj.id}]({image_obj.id})",
                f"![[{new_image_name}]]"
            )
        markdown_pages.append(updated_markdown)
    
    return markdown_pages, counter

def run_ocr_on_pdf(pdf_path, client, output_dir=None):
    """
    This function runs OCR on a PDF file using Mistral API
    Returns: OCR response object
    """
    # Convert pdf_path to Path object if it's not already
    if not isinstance(pdf_path, Path):
        pdf_path = Path(pdf_path)
    
    # Ensure output_dir is provided
    if output_dir is None:
        raise ValueError("output_dir must be provided")
    
    # Create JSON file path in output directory
    json_file = output_dir / "ocr_response.json"
    
    # Check if JSON file exists
    if json_file.exists():
        print(f"    - 캐시된 OCR 결과를 찾았습니다: {json_file}")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                import json
                from mistralai.models.ocr import OCRResponse, OCRPage, OCRImage
                
                # Load JSON data
                data = json.load(f)
                
                # Reconstruct OCRResponse object
                response = OCRResponse(
                    id=data.get("id", ""),
                    model=data.get("model", ""),
                    pages=[
                        OCRPage(
                            page_number=page.get("page_number", 0),
                            markdown=page.get("markdown", ""),
                            images=[
                                OCRImage(
                                    id=img.get("id", ""),
                                    image_base64=img.get("image_base64", "")
                                ) for img in page.get("images", [])
                            ]
                        ) for page in data.get("pages", [])
                    ]
                )
                print(f"    - 캐시된 OCR 결과를 성공적으로 불러왔습니다")
                return response
        except Exception as e:
            print(f"    - 캐시된 OCR 결과를 불러오는데 실패했습니다: {str(e)}")
            # Process new if cache loading fails
    
    try:
        print(f"    - 파일 읽기 시작: {pdf_path.name}")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        print(f"    - 파일 업로드 시작: {pdf_path.name}, 크기: {len(pdf_bytes)/1024/1024:.2f}MB")
        uploaded_file = client.files.upload(
            file={
                "file_name": pdf_path.name,
                "content": pdf_bytes,
            },
            purpose="ocr"
        )
        
        print(f"    - 파일 업로드 완료, ID: {uploaded_file.id}")
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
        print(f"    - 서명된 URL을 획득했습니다")
        
        print(f"    - OCR 처리 시작")
        response = client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model="mistral-ocr-latest",
            include_image_base64=True
        )
        print(f"    - OCR 처리 완료")
        
        # Save OCR result as JSON
        try:
            print(f"    - OCR 결과 저장 중...")
            # Debug: Print response structure
            # print(f"    - OCR 응답 구조 디버깅:")
            # print(f"    - 응답 타입: {type(response)}")
            # print(f"    - 응답 속성: {dir(response)}")
            # print(f"    - 페이지 타입: {type(response.pages[0]) if response.pages else 'No pages'}")
            # if response.pages:
            #     print(f"    - 페이지 속성: {dir(response.pages[0])}")
            # if hasattr(response.pages[0], 'images') and response.pages[0].images:
            #     print(f"    - 이미지 타입: {type(response.pages[0].images[0])}")
            #     print(f"    - 이미지 속성: {dir(response.pages[0].images[0])}")
            
            # Convert OCRResponse object to JSON serializable dictionary
            response_dict = {
                "pages": [
                    {
                        "markdown": page.markdown if hasattr(page, 'markdown') else "",
                        "images": [
                            {
                                "id": img.id if hasattr(img, 'id') else f"image_{i}",
                                "image_base64": img.image_base64 if hasattr(img, 'image_base64') else ""
                            } for i, img in enumerate(page.images) if hasattr(page, 'images')
                        ]
                    } for i, page in enumerate(response.pages)
                ]
            }
            
            # Add page_number if it exists
            for i, page in enumerate(response.pages):
                if hasattr(page, 'page_number'):
                    response_dict["pages"][i]["page_number"] = page.page_number
                else:
                    response_dict["pages"][i]["page_number"] = i + 1
            
            # Add id and model if they exist
            if hasattr(response, 'id'):
                response_dict["id"] = response.id
            if hasattr(response, 'model'):
                response_dict["model"] = response.model
            
            # Save JSON file in output directory
            with open(json_file, "w", encoding="utf-8") as f:
                import json
                json.dump(response_dict, f, ensure_ascii=False, indent=2)
            print(f"    - OCR 결과가 저장되었습니다: {json_file}")
        except Exception as e:
            print(f"    - OCR 결과 저장에 실패했습니다: {str(e)}")
        
        return response
    except Exception as e:
        print(f"    - OCR 처리 중 오류 발생: {str(e)}")
        # Print more detailed error information
        import traceback
        print(traceback.format_exc())
        raise

def process_pdf(pdf_path: Path):
    """
    This function processes a PDF file with OCR and generates markdown
    """
    pdf_base = pdf_path.stem
    output_dir = OUTPUT_ROOT_DIR / pdf_base
    output_dir.mkdir(exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Check file size and split if necessary
    file_size = pdf_path.stat().st_size
    if file_size > MAX_PDF_SIZE:
        print(f"파일 크기가 너무 큽니다: {file_size/1024/1024:.2f}MB. 청크로 처리합니다.")
        
        # Create a temporary directory for split PDFs
        temp_dir = Path("temp_split_pdfs")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Split the PDF into smaller chunks
            input_filename = pdf_path.stem
            
            # Call modified split_pdf_by_size function - directly pass temp directory path
            pdf_chunks = split_pdf_by_size(
                str(pdf_path), 
                MAX_PDF_SIZE, 
                f"_part", 
                output_dir=temp_dir
            )
            
            # Calculate total page count
            total_pages = 0
            for chunk_path in pdf_chunks:
                # Calculate page count using PyPDF2
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(chunk_path)
                    total_pages += len(reader.pages)
                except Exception as e:
                    print(f"  - 페이지 수 계산 중 오류 발생: {str(e)}")
            
            print(f"PDF가 {len(pdf_chunks)}개의 청크로 분할되었습니다. (총 {total_pages} 페이지)")
        except Exception as e:
            print(f"  - PDF 분할 중 오류 발생: {str(e)}")
            return
        
        all_markdown_pages = []
        global_counter = 1
        
        # Process each chunk
        successful_chunks = 0
        for i, chunk_path in enumerate(pdf_chunks):
            print(f"  - 청크 {i+1}/{len(pdf_chunks)} 처리 중: {chunk_path.name}")
            
            try:
                # Check file size
                chunk_size = os.path.getsize(chunk_path)
                print(f"    - 파일 크기: {chunk_size/1024/1024:.2f}MB")
                
                # Skip very small files (less than 1MB)
                if chunk_size < 1024 * 1024:
                    print(f"    - 파일이 너무 작습니다 (1MB 미만). 건너뜁니다.")
                    continue
                
                # Process the chunk with OCR
                ocr_response = run_ocr_on_pdf(chunk_path, client, output_dir)
                
                # Process images and markdown for this chunk
                chunk_markdown_pages, global_counter = process_ocr_response(
                    ocr_response, pdf_base, images_dir, global_counter
                )
                
                all_markdown_pages.extend(chunk_markdown_pages)
                successful_chunks += 1
                print(f"    - 청크 {i+1} 처리 완료")
            except Exception as e:
                print(f"    - 청크 {i+1} 처리 중 오류 발생: {str(e)}")
                import traceback
                print(traceback.format_exc())
                # Continue processing next chunk even if error occurs
                continue
            
        # Check processing results
        if successful_chunks == 0:
            print("  - 모든 청크 처리에 실패했습니다. 중단합니다.")
            return
        
        print(f"  - {len(pdf_chunks)}개 중 {successful_chunks}개의 청크를 성공적으로 처리했습니다")
            
        # Delete only temporary PDF files and keep JSON cache
        for chunk_path in pdf_chunks:
            try:
                os.remove(chunk_path)
            except Exception as e:
                print(f"  - 임시 파일 삭제 중 오류 발생: {str(e)}")
        
        # Delete temporary directory
        try:
            shutil.rmtree(temp_dir)
            print("  - 임시 디렉토리 삭제됨")
        except Exception as e:
            print(f"  - 임시 디렉토리 삭제 중 오류 발생: {str(e)}")
        
        # Combine all markdown pages into a single file
        if all_markdown_pages:
            combined_markdown = get_combined_markdown(all_markdown_pages)
            
            # Write the combined markdown to a file
            markdown_output_path = output_dir / f"{pdf_base}.md"
            with open(markdown_output_path, "w", encoding="utf-8") as f:
                f.write(combined_markdown)
            
            print(f"  - 마크다운 파일 생성됨: {markdown_output_path}")
            
            # Move the original PDF to the done directory
            done_pdf_path = DONE_DIR / pdf_path.name
            shutil.copy2(pdf_path, done_pdf_path)
        else:
            print("  - 처리된 마크다운 페이지가 없습니다. 마크다운 파일이 생성되지 않았습니다.")
        
        return
    
    # For PDFs under the size limit, process normally
    print(f"OCR 처리 중: {pdf_path.name}")
    try:
        ocr_response = run_ocr_on_pdf(pdf_path, client, output_dir)
        
        # Process images and markdown
        markdown_pages, _ = process_ocr_response(ocr_response, pdf_base, images_dir)
        
        # Combine all markdown pages into a single file
        combined_markdown = get_combined_markdown(markdown_pages)
        
        # Write the combined markdown to a file
        markdown_output_path = output_dir / f"{pdf_base}.md"
        with open(markdown_output_path, "w", encoding="utf-8") as f:
            f.write(combined_markdown)
        
        print(f"  - 마크다운 파일 생성됨: {markdown_output_path}")
        
        # Move the original PDF to the done directory
        done_pdf_path = DONE_DIR / pdf_path.name
        shutil.copy2(pdf_path, done_pdf_path)
    except Exception as e:
        print(f"  - PDF 처리 중 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

def main():
    # Process all PDF files in the input directory
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("처리할 PDF 파일이 없습니다. pdfs_to_process 디렉토리에 PDF 파일을 넣어주세요.")
        return
    
    print(f"{len(pdf_files)}개의 PDF 파일을 처리합니다.")
    
    for pdf_file in pdf_files:
        process_pdf(pdf_file)
        # Remove the original file after processing
        os.remove(pdf_file)
    
    print("모든 PDF 파일이 처리되었습니다.")

if __name__ == "__main__":
    main()
