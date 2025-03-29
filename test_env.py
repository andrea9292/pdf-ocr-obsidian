#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# 현재 작업 디렉토리 출력
print(f"현재 작업 디렉토리: {os.getcwd()}")

# .env 파일 존재 여부 확인
env_path = os.path.join(os.getcwd(), '.env')
print(f".env 파일 존재 여부: {os.path.exists(env_path)}")

# 환경 변수 로드 전
print(f"로드 전 API 키: {os.getenv('MISTRAL_API_KEY')}")

# 환경 변수 로드
load_dotenv()

# 환경 변수 로드 후
api_key = os.getenv("MISTRAL_API_KEY")
print(f"로드 후 API 키: {api_key[:5]}..." if api_key else "API 키가 로드되지 않았습니다.")
