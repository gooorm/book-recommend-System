import streamlit as st
import requests
import data

KAKAO_REST_API_KEY = "YOUR_KAKAO_KEY"  # 환경변수나 st.secrets로 관리 추천

# 1. 정보나루 지역코드 매핑 (샘플만, 매뉴얼 지역 코드 표에서 필요한 것 더 추가)
#   region: 광역 수준, dtl_region: 시군구 수준
REGION_CODE_MAP = data.REGION_CODE_MAP

DTL_REGION_CODE_MAP = data.DTL_REGION

def kakao_reverse_geocode(lat: float, lon: float):
    """카카오 로컬 coord2regioncode로 위경도 -> 행정구역 정보"""
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "x": lon,  # 경도
        "y": lat,  # 위도
        "input_coord": "WGS84"
    }
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    data = res.json()
    docs = data.get("documents", [])
    if not docs:
        return None
    # 행정동 기준(‘region_type’이 B) 우선 사용
    doc = next((d for d in docs if d.get("region_type") == "B"), docs[0])
    return {
        "sido": doc.get("region_1depth_name"),      # 시·도
        "sigungu": doc.get("region_2depth_name"),   # 시·군·구
        "dong": doc.get("region_3depth_name"),      # 읍·면·동
    }

def to_data4library_region_codes(addr_info):
    """카카오 행정구역 → 정보나루 region / dtl_region 코드 매핑"""
    if not addr_info:
        return None, None

    sido = addr_info["sido"]
    sigungu = addr_info["sigungu"]

    region = REGION_CODE_MAP.get(sido)

    key_dtl1 = f"{sido} {sigungu}"  # 예: "경기도 수원시"
    dtl_region = DTL_REGION_CODE_MAP.get(key_dtl1)

    return region, dtl_region


# ===== Streamlit UI =====
st.title("현재 위치 기반 도서관 검색 (정보나루)")

st.write("사용자 위치(위도, 경도)를 입력하면, 정보나루 지역코드를 자동으로 계산해서 도서관을 조회합니다.")

lat = st.number_input("위도(lat)", format="%.6f")
lon = st.number_input("경도(lon)", format="%.6f")

if st.button("내 위치 기준 도서관 찾기"):
    if not lat or not lon:
        st.error("위도와 경도를 입력해 주세요.")
    else:
        try:
            addr_info = kakao_reverse_geocode(lat, lon)
        except Exception as e:
            st.error(f"위치 → 주소 변환 실패: {e}")
            st.stop()

        if not addr_info:
            st.error("행정구역 정보를 찾을 수 없습니다.")
            st.stop()

        region, dtl_region = to_data4library_region_codes(addr_info)

        st.write("카카오 행정구역 정보:", addr_info)
        st.write("매핑된 정보나루 지역코드:", {"region": region, "dtl_region": dtl_region})

        if not (region or dtl_region):
            st.warning("이 행정구역에 대한 정보나루 지역코드 매핑이 아직 정의되지 않았습니다. 코드표를 보고 DTL_REGION_CODE_MAP을 더 채워야 합니다.")
            st.stop()

        # 정보나루 도서관 조회 API 호출 예시 (region / dtl_region 사용) [file:131]
        AUTH_KEY = "YOUR_DATA4LIBRARY_KEY"
        params = {
            "authKey": AUTH_KEY,
            "format": "json",
            "pageNo": 1,
            "pageSize": 10,
        }
        # 가능한 한 좁은 범위인 dtl_region 우선
        if dtl_region:
            params["dtl_region"] = dtl_region
        elif region:
            params["region"] = region

        api_url = "http://data4library.kr/api/libSrch"
        try:
            r = requests.get(api_url, params=params)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"정보나루 API 호출 실패: {e}")
            st.stop()

        st.subheader("조회 결과")
        st.json(data)
