import streamlit as st
import user.data as data
from user.user_loc import getLocation
from user.user_vector import genre_vector

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
KDC = data.KDC
KDC_REVERSE = {v: k for k, v in KDC.items()}
genres = data.DTL_KDC
dtl = {
    0: [
        "도서학", "서지학", "문헌정보학", "백과사전",
        "강연집·수필집·연설문집",
        "일반연속간행물", "학회·단체·연구기관",
        "신문", "저널리즘", "전집", "총서", "향토자료"
    ],
    1: [
        "형이상학", "인식론·인과론·인간학",
        "철학의 체계", "경학",
        "동양철학·동양사상",
        "서양철학", "논리학",
        "심리학", "윤리학·도덕철학"
    ],
    2: [
        "비교종교", "불교", "기독교", "도교",
        "천도교", "힌두교·브라만교",
        "이슬람교", "기타 종교"
    ],
    3: [
        "통계자료", "경제학", "사회학", "사회문제",
        "정치학", "행정학", "법률·법학",
        "교육학", "풍습·예절·민속학",
        "국방·군사학"
    ],
    4: [
        "수학", "물리학", "화학", "천문학",
        "지학", "광물학", "생명과학",
        "식물학", "동물학"
    ],
    5: [
        "의학", "농업·농학",
        "공학", "공업일반", "토목공학", "환경공학",
        "건축·건축학", "기계공학",
        "전기공학", "전자공학", "통신공학",
        "화학공학", "제조업", "생활과학"
    ],
    6: [
        "조각", "조형미술", "공예",
        "서예", "회화", "도화", "디자인",
        "사진예술", "음악",
        "공연예술", "매체예술",
        "오락", "스포츠"
    ],
    7: [
        "한국어", "중국어", "일본어",
        "아시아 제어", "영어",
        "독일어", "프랑스어",
        "스페인어", "포르투갈어",
        "이탈리아어", "기타 제어"
    ],
    8: [
        "한국문학", "중국문학", "일본문학",
        "아시아 제문학",
        "영미문학", "독일문학",
        "프랑스문학",
        "스페인·포르투갈 문학",
        "이탈리아 문학", "기타 문학"
    ],
    9: [
        "아시아사", "유럽사", "아프리카사",
        "북아메리카사", "남아메리카사",
        "오세아니아사", "지리",
        "전기"
    ]
}

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
        st.session_state.user["gender"] = "F"
        st.session_state.step = 3
        st.rerun()

    if col2.button("👨 남성"):
        st.session_state.user["gender"] = "M"
        st.session_state.step = 3
        st.rerun()

    if col3.button("❓ 선택 안 함"):
        st.session_state.user["gender"] = "ANY"
        st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3: 연령대
# -----------------------------
elif st.session_state.step == 3:
    st.header("연령대를 선택해주세요")

    age_groups = {
        "10대": 15,
        "20대": 25,
        "30대": 35,
        "40대": 45,
        "50대": 55,
        "60대 이상": 65
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
    st.subheader("사용자 선호 벡터")

    st.json(st.session_state.user)

    st.markdown("""
    ✅ 이 벡터가 이후  
    - 도서 KDC  
    - 연령대 통계  
    - 성별 대출 비율  
    과 매칭되어 추천 점수에 사용됩니다.
    """)
    st.write(getLocation())
