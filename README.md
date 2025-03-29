# PDF OCR 파이프라인 - Mistral AI를 이용한 PDF에서 마크다운 변환

이 프로젝트는 **Mistral AI의 OCR API**를 사용하여 PDF 파일에서 텍스트와 이미지를 추출하고, Obsidian에서 사용할 수 있는 마크다운 형식으로 변환하는 파이썬 스크립트입니다.

## 주요 기능
- **대용량 PDF 처리:** 50MB 이상의 대용량 PDF 파일을 자동으로 분할하여 처리
- **일괄 처리:** 입력 폴더에 여러 PDF 파일을 넣고 한 번에 처리
- **텍스트 추출:** 스캔된 PDF를 구조화된 마크다운 형식으로 변환
- **이미지 추출:** 이미지를 별도로 저장하고 Obsidian 호환 `![[이미지-이름]]` 형식으로 링크
- **자동 정리:** 처리된 각 PDF는 자체 출력 폴더를 가지며, 완료된 PDF는 `pdfs-done` 폴더로 복사됨
- **OCR 캐싱:** OCR 응답을 JSON으로 저장하여 중복 API 호출 방지

## 설치 방법
Python 3.9 이상이 설치되어 있는지 확인한 후 다음 의존성 패키지를 설치하세요:

```sh
pip install mistralai python-dotenv PyPDF2
```

## 사용 방법
### 1. API 키 설정

스크립트를 실행하기 전에 Mistral AI API 키를 설정해야 합니다. [Mistral의 API 키 콘솔](https://console.mistral.ai/api-keys)에서 무료로 키를 생성할 수 있습니다.

저장소에 포함된 `env.example` 파일을 편집하여 API 키를 추가하고 `.env`로 이름을 변경하세요.

또는 환경 변수로 직접 설정할 수도 있습니다:

```sh
export MISTRAL_API_KEY='your_api_key_here'  # Linux/macOS
set MISTRAL_API_KEY='your_api_key_here'    # Windows
```

### 2. 디렉토리 구조 확인

스크립트를 처음 실행하기 전에 다음 폴더가 자동으로 생성됩니다:
- `pdfs_to_process`: 처리할 PDF 파일을 이 폴더에 넣으세요
- `pdfs-done`: 처리가 완료된 PDF 파일이 이동합니다
- `ocr_output`: 변환된 마크다운과 이미지가 저장됩니다

### 3. PDF 파일 준비

처리하려는 PDF 파일을 `pdfs_to_process` 폴더에 넣으세요. 대용량 파일(50MB 이상)은 자동으로 분할되어 처리됩니다.

### 4. 스크립트 실행

다음 명령어로 스크립트를 실행하세요:

```sh
python pdf_markdown_ocr.py
```

### 5. 출력 구조
처리된 각 PDF는 `ocr_output` 내에 자체 폴더를 가지며 다음과 같이 구성됩니다:

```
ocr_output/
  ├── MyDocument/
  │   ├── MyDocument.md          # 추출된 마크다운(위키링크 포함)
  │   ├── images/
  │   │   ├── MyDocument_img_1.jpeg
  │   │   ├── MyDocument_img_2.jpeg
  │   ├── ocr_response.json      # OCR 응답 캐시(재사용 가능)
pdfs-done/
  ├── MyDocument.pdf  # OCR 완료 후 복사됨
```

### 6. Obsidian으로 출력물 이동
변환 후, 생성된 마크다운 파일과 이미지 폴더를 **Obsidian vault**로 이동하세요.

**중요:** Obsidian vault가 **위키링크 경로**(`![[이미지-이름]]`)를 처리하도록 설정되어 있는지 확인하세요.

## 작동 방식
1. 스크립트는 `pdfs_to_process`에서 PDF 파일을 스캔합니다.
2. 각 PDF 파일의 크기를 확인하고 필요시 분할합니다.
3. 각 PDF(또는 분할된 청크)는 Mistral AI로 업로드되어 OCR 처리됩니다.
4. 텍스트는 추출되어 마크다운(`.md`)으로 저장됩니다.
5. 이미지는 추출되어 하위 폴더에 저장되고 마크다운에서 `![[이미지-이름]]`으로 참조됩니다.
6. 원본 PDF는 `pdfs-done`으로 복사되고 입력 폴더에서 삭제됩니다.
7. 전체 OCR 응답은 나중에 사용할 수 있도록 각 PDF 출력 폴더에 JSON으로 저장됩니다.

## 주의사항
- 대용량 PDF 파일(50MB 이상)은 자동으로 분할되어 처리됩니다.
- OCR 처리는 인터넷 연결이 필요하며, Mistral AI API를 사용합니다.
- 처리 시간은 PDF 크기와 복잡성에 따라 달라질 수 있습니다.
- OCR 결과는 각 PDF 출력 폴더에 `ocr_response.json` 파일로 저장되어 재사용됩니다.
- 이미 처리된 PDF를 다시 처리하려면 캐시 파일을 삭제하거나 파일 이름을 변경하세요.
- 처리가 완료된 PDF는 자동으로 입력 폴더에서 삭제됩니다.

## 문제 해결
- API 키 오류: `.env` 파일이 올바르게 설정되었는지 확인하세요.
- 파일 처리 오류: 매우 작은 PDF 파일(1MB 미만)은 건너뛸 수 있습니다.
- OCR 품질 문제: 스캔 품질이 낮은 PDF는 OCR 결과가 좋지 않을 수 있습니다.
- 메모리 오류: 매우 큰 PDF 파일을 처리할 때 메모리 부족 오류가 발생할 수 있습니다.

## 기여
개선 사항이나 추가 기능이 있으면 이슈나 풀 리퀘스트를 제출해 주세요.

## 라이선스
이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다.


# PDF OCR Pipeline to Markdown using Mistral AI

This repository contains a Python script that automates the OCR (Optical Character Recognition) process for PDFs using the **Mistral AI** OCR API. It extracts text and images from PDFs and organizes the output into structured markdown documents with images properly linked using Obsidian-style **wikilinks**.

## Features
- **Large PDF handling:** Automatically splits PDFs larger than 50MB for processing
- **Batch processing:** Place multiple PDFs in the input folder and process them automatically
- **Text extraction:** Converts scanned PDFs into structured markdown format while preserving document hierarchy
- **Image extraction:** Saves images separately and links them in the markdown using Obsidian-compatible `![[image-name]]` format
- **Automatic organization:** Each processed PDF gets its own output folder, and completed PDFs are copied to a `pdfs-done` folder
- **OCR caching:** Saves the OCR response as JSON in each PDF's output folder for reuse

## Installation
Ensure you have Python 3.9+ installed, then install dependencies:

```sh
pip install mistralai python-dotenv PyPDF2
```

## Usage
### 1. Set Up API Key

Before running the script, you need to set up a free Mistral API key. Go to [Mistral's API Key Console](https://console.mistral.ai/api-keys) and generate your key—it doesn't cost anything.

An `env.example` file is included in the repository. Edit it to add your API key and rename it to `.env` so the script can use it properly.

Alternatively, you can set it manually as an environment variable:

```sh
export MISTRAL_API_KEY='your_api_key_here'  # For Linux/macOS
set MISTRAL_API_KEY='your_api_key_here'    # For Windows
```

### 2. Directory Structure

Before running the script for the first time, the following folders will be automatically created:
- `pdfs_to_process`: Place the PDFs you want to OCR in this folder
- `pdfs-done`: Processed PDFs will be copied here
- `ocr_output`: Converted markdown and images will be stored here

### 3. Prepare PDF Files

Place the PDFs you want to process in the `pdfs_to_process` folder. Large files (over 50MB) will be automatically split and processed.

### 4. Run the Script

Execute the script with the following command:

```sh
python pdf_markdown_ocr.py
```

### 5. Output Structure
Each processed PDF gets its own folder inside `ocr_output`, structured like this:

```
ocr_output/
  ├── MyDocument/
  │   ├── MyDocument.md          # Extracted markdown with wikilinks
  │   ├── images/
  │   │   ├── MyDocument_img_1.jpeg
  │   │   ├── MyDocument_img_2.jpeg
  │   ├── ocr_response.json      # Cached OCR response for reuse
pdfs-done/
  ├── MyDocument.pdf  # Copied here after OCR completion
```

### 6. Move Output to Obsidian Vault
After conversion, move the generated markdown file and images folder into your **Obsidian vault**.

**Important:** Ensure that your Obsidian vault is set up to handle **wikilink paths** (`![[image-name]]`).

## How It Works
1. The script scans `pdfs_to_process` for PDF files.
2. It checks each PDF's size and splits it if necessary.
3. Each PDF (or split chunk) is uploaded to Mistral AI for OCR processing.
4. The text is extracted and saved as markdown (`.md`).
5. Images are extracted, saved in a subfolder, and referenced in the markdown using `![[image-name]]`.
6. The original PDF is copied to `pdfs-done` and deleted from the input folder.
7. The full OCR response is saved as JSON in each PDF's output folder for later use.

## Notes and Cautions
- Large PDF files (over 50MB) are automatically split and processed in chunks.
- OCR processing requires an internet connection and uses the Mistral AI API.
- Processing time varies depending on PDF size and complexity.
- OCR results are cached in each PDF's output folder as `ocr_response.json` for reuse.
- To reprocess an already processed PDF, delete or rename its cache file.
- Processed PDFs are automatically deleted from the input folder after being copied to `pdfs-done`.

## Troubleshooting
- API key errors: Ensure your `.env` file is properly configured.
- File processing errors: Very small PDF files (less than 1MB) may be skipped.
- OCR quality issues: PDFs with poor scan quality may result in suboptimal OCR.
- Memory errors: Processing very large PDF files may cause out-of-memory errors.

## Contributing
Feel free to submit issues or pull requests if you have improvements or additional features in mind.

## License
This project is licensed under the MIT License.
