import os
from dotenv import load_dotenv

load_dotenv()

NARU_API_KEY = os.getenv("NARU_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
if not KAKAO_REST_API_KEY:
    raise RuntimeError("KAKAO_REST_API_KEY 없음")
if not NARU_API_KEY:
    raise RuntimeError("NARU_API_KEY 없음")