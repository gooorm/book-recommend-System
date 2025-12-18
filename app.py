import streamlit as st
import requests
from user.user_loc import getLocation
from user.user_vector import genre_vector
from datetime import datetime, timedelta
import json
from config import NARU_API_KEY
import os
import user.data as code_data
print("CONFIG KEY:", repr(NARU_API_KEY))
# -----------------------------
# 초기 세션 상태
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

if "user" not in st.session_state:
    st.session_state.user = {}

# -----------------------------
# KDC 대분류
# -----------------------------
KDC = code_data.KDC
KDC_REVERSE = {v: k for k, v in KDC.items()}
genres = code_data.DTL_KDC

# ---------------------------
# 도서 조회 함수
# ---------------------------
def get_popular_books(user_prefs):
    """
    사용자 선호도를 기반으로 인기 도서 조회
    """
    # API URL
    base_url = "http://data4library.kr/api/loanItemSrch"

    # 날짜 설정 (최근 1개월)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # 파라미터 구성
    params = {
        "authKey": NARU_API_KEY,
        "format": "json",
        "pageNo": 1,
        "pageSize": 20,  # 한 번에 가져올 도서 수
    }

    # 사용자 선호도 추가
    if "gender" in user_prefs and user_prefs["gender"]:
        params["gender"] = user_prefs["gender"]

    if "age" in user_prefs and user_prefs["age"]:
        params["age"] = user_prefs["age"]

    if "kdc" in user_prefs and user_prefs["kdc"]:
        params["kdc"] = user_prefs["kdc"]

    if "dtl_kdc" in user_prefs and user_prefs["dtl_kdc"]:
        params["dtl_kdc"] = user_prefs["dtl_kdc"]

    # 날짜 추가
    params["startDt"] = start_date.strftime("%Y-%m-%d")
    params["endDt"] = end_date.strftime("%Y-%m-%d")

    try:
        # API 요청
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        # JSON 파싱
        data = response.json()

        # 응답 데이터 확인
        if "response" in data and "docs" in data["response"]:
            books = data["response"]["docs"]
            return books, None
        else:
            return [], "응답 데이터 형식이 올바르지 않습니다."

    except requests.exceptions.Timeout:
        return [], "API 요청 시간 초과"
    except requests.exceptions.RequestException as e:
        return [], f"API 요청 실패: {str(e)}"
    except json.JSONDecodeError:
        return [], "응답 데이터 파싱 실패"


def display_book_card(book, location):
    """
    도서 정보를 카드 형태로 표시
    """
    # 도서 정보 추출
    book_info = book.get("doc", {})

    bookname = book_info.get("bookname", "제목 없음")
    authors = book_info.get("authors", "저자 미상")
    publisher = book_info.get("publisher", "출판사 미상")
    publication_year = book_info.get("publication_year", "")
    book_image_url = book_info.get("bookImageURL", "")
    isbn13 = book_info.get("isbn13", "")
    loan_count = book_info.get("loan_count", "0")
    ranking = book_info.get("ranking", "")

    # 카드 레이아웃
    col1, col2 = st.columns([1, 3])

    with col1:
        # 책 표지 이미지
        if book_image_url:
            st.image(book_image_url, use_container_width=True)
        else:
            st.markdown("📚")

    with col2:
        # 도서 정보
        st.markdown(f"### {bookname}")
        st.markdown(f"**저자**: {authors}")
        st.markdown(f"**출판사**: {publisher} ({publication_year})")

        if ranking:
            st.markdown(f"🏆 순위: {ranking}위 | 대출 {loan_count}회")
        else:
            st.markdown(f"📊 대출 {loan_count}회")

        # 도서관 찾기 버튼
        if st.button(f"가까운 도서관 찾기", key=f"btn_{isbn13}"):
            if location:
                st.session_state.selected_book = {
                    "isbn13": isbn13,
                    "bookname": bookname,
                    "location": location
                }
                st.rerun()
            else:
                st.error("위치 정보를 가져올 수 없습니다.")

    st.divider()


def search_nearby_libraries(isbn, location):
    """
    가까운 도서관에서 해당 도서 소장 여부 검색
    (실제 구현시 도서관 정보나눔 API 사용)
    """
    # TODO: 실제 도서관 API 연동
    # http://data4library.kr/api/libSrch (도서관 검색)
    # http://data4library.kr/api/bookExist (소장 도서 검색)

    st.info(f"""
    📍 현재 위치: 위도 {location['latitude']}, 경도 {location['longitude']}

    ISBN: {isbn}

    (가까운 도서관 API 연동 예정)
    """)
# -----------------------------
# STEP 1: 이름
# -----------------------------
if st.session_state.step == 1:
    st.title("📚 도서 추천 설문")
    name = st.text_input("이름을 입력해주세요")

    if st.button("다음"):
        if name:
            st.session_state.user["name"] = name
            st.session_state.step = 2
            st.rerun()

# -----------------------------
# STEP 2: 성별
# -----------------------------
elif st.session_state.step == 2:
    st.header("성별을 선택해주세요")

    col1, col2, col3 = st.columns(3)

    if col1.button("👩 여성"):
        st.session_state.user["gender"] = "1"
        st.session_state.step = 3
        st.rerun()

    if col2.button("👨 남성"):
        st.session_state.user["gender"] = "2"
        st.session_state.step = 3
        st.rerun()

    if col3.button("❓ 선택 안 함"):
        st.session_state.user["gender"] = "2"
        st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3: 연령대
# -----------------------------
elif st.session_state.step == 3:
    st.header("연령대를 선택해주세요")

    age_groups = {
        "영유아(0~5세)": '0',
        "유아(6~7세)": '7',
        "초등(8~13세)": '8',
        "청소년": '14',
        "20대": '20',
        "30대": "30",
        "40대": '40',
        "50대": "50",
        "60대 이상": "60"
    }

    cols = st.columns(3)
    i = 0
    for label, age in age_groups.items():
        if cols[i % 3].button(label):
            st.session_state.user["age"] = age
            st.session_state.step = 4
            st.rerun()
        i += 1

# -----------------------------
# STEP 4: 선호 KDC (다중 선택)
# -----------------------------

elif st.session_state.step == 4:
    st.header("관심 있는 분야를 선택해주세요 (최대 2개)")

    selected = st.multiselect(
        "KDC 대분류",
        list(KDC.values()),   # 👈 보여주는 건 한글
        max_selections=2
    )

    if st.button("다음"):
        if selected:
            weight = 1 / len(selected)

            # ✅ 한글 → KDC 코드 변환
            selected_indices = [
                KDC_REVERSE[name] for name in selected
            ]

            # ✅ {"0": 0.5, "3": 0.5} 이런 형태
            st.session_state.user["kdc"] = {
                idx: weight for idx in selected_indices
            }

            st.session_state.step = 5
            st.rerun()


# -----------------------------
# STEP 5: 장르 성향

# -----------------------------
elif st.session_state.step == 5:
    st.header("세부 관심 장르를 선택해주세요")

    # 세션에 selected_genres 없으면 생성
    if "selected_genres" not in st.session_state:
        st.session_state.selected_genres = set()

    # 선택한 KDC 인덱스
    selected_kdc_indices = st.session_state.user["kdc"].keys()

    # 세부 장르 합치기
    detail_genres = []
    for idx in selected_kdc_indices:
        base = int(idx) * 10  # 0 → 0, 1 → 10
        for i in range(1, 10):
            code = f"{base + i:02d}"  # 01~09, 11~19
            detail_genres.extend([genres[code]])


    # 중복 제거
    detail_genres = list(set(detail_genres))

    # 🎨 전역 CSS 스타일 적용
    st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(2)

    for i, genre_name in enumerate(detail_genres):
        col = cols[i % 2]

        is_selected = genre_name in st.session_state.selected_genres

        # 선택 상태에 따라 버튼 타입과 라벨 변경
        if is_selected:
            button_label = f"✅ {genre_name}"
            button_type = "primary"  # 선택된 상태
        else:
            button_label = genre_name
            button_type = "secondary"  # 기본 상태

        if col.button(
                button_label,
                key=f"genre_{i}_{genre_name}",
                type=button_type,
                use_container_width=True
        ):
            if is_selected:
                st.session_state.selected_genres.remove(genre_name)
            else:
                st.session_state.selected_genres.add(genre_name)
            st.rerun()  # 상태 변경 후 즉시 리렌더링

    st.write("")  # 간격 추가

    # 선택된 장르 표시 (선택사항)
    if st.session_state.selected_genres:
        st.info(
            f"선택됨 ({len(st.session_state.selected_genres)}개): {', '.join(sorted(st.session_state.selected_genres))}")

    if st.button("완료", type="primary", use_container_width=True):
        if st.session_state.selected_genres:
            weight = 1 / len(st.session_state.selected_genres)
            st.session_state.user["genre"] = {
                g: weight for g in st.session_state.selected_genres
            }

            # 정리
            del st.session_state.selected_genres

            st.session_state.step = 6
            st.rerun()
        else:
            st.warning("최소 1개 이상의 장르를 선택해주세요!")



# -----------------------------
# STEP 6: 결과 확인 (벡터)
# -----------------------------
elif st.session_state.step == 6:
    st.success("설문 완료! 🎉")

    # 사용자 선호 벡터 표시
    # with st.expander("📊 사용자 선호 벡터 보기"):
    #     st.json(st.session_state.user)
    #
    #     st.markdown("""
    #         ✅ 이 벡터가 이후
    #         - 도서 KDC
    #         - 연령대 통계
    #         - 성별 대출 비율
    #         과 매칭되어 추천 점수에 사용됩니다.
    #         """)

    # 위치 정보 가져오기
    location = getLocation()

    st.divider()
    st.header("📚 맞춤 추천 도서")

    # 도서 검색 중 표시
    with st.spinner("당신을 위한 도서를 찾고 있습니다..."):
        books, error = get_popular_books(st.session_state.user)

    # 에러 처리
    if error:
        st.error(f"❌ 도서 조회 실패: {error}")
        st.info("API 키를 확인하거나 나중에 다시 시도해주세요.")

        # 재시도 버튼
        if st.button("🔄 다시 시도"):
            st.rerun()

    # 도서가 없는 경우
    elif not books:
        st.warning("😢 조건에 맞는 도서를 찾지 못했습니다.")
        st.info("다른 선호도를 선택해보시겠어요?")

        if st.button("⬅️ 설문 다시하기"):
            st.session_state.step = 1
            st.rerun()

    # 도서 표시
    else:
        st.success(f"✨ {len(books)}권의 추천 도서를 찾았습니다!")

        # 필터 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox("정렬", ["인기순", "최신순"], key="sort_books")
        with col2:
            show_count = st.slider("표시 개수", 5, 20, 10, key="show_count")
        with col3:
            st.write("")  # 공간 확보

        st.divider()

        # 도서 카드 표시
        display_books = books[:show_count]

        for idx, book in enumerate(display_books):
            display_book_card(book, location)

        # 더보기 버튼
        if len(books) > show_count:
            st.info(f"📖 {len(books) - show_count}권의 도서가 더 있습니다.")

    # 선택된 도서가 있는 경우 도서관 검색
    if "selected_book" in st.session_state:
        st.divider()
        st.header("🏛️ 가까운 도서관")

        selected = st.session_state.selected_book
        st.markdown(f"**선택한 도서**: {selected['bookname']}")

        search_nearby_libraries(
            selected["isbn13"],
            selected["location"]
        )

        # 뒤로가기
        if st.button("⬅️ 도서 목록으로"):
            del st.session_state.selected_book
            st.rerun()

    # 하단 버튼
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 설문 다시하기", use_container_width=True):
            st.session_state.step = 1
            if "selected_book" in st.session_state:
                del st.session_state.selected_book
            st.rerun()

    with col2:
        if st.button("💾 추천 결과 저장", use_container_width=True):
            # TODO: 추천 결과 저장 기능
            st.success("저장되었습니다!")
