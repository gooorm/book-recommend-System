import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import requests
import data

# 방법 1: streamlit-geolocation 라이브러리 사용 (안정적!)
def get_user_location():
    """streamlit-geolocation을 사용하여 사용자 위치 받기"""
    location = streamlit_geolocation()
    
    if location is None:
        return None
    
    return {
        'latitude': location.get('latitude'),
        'longitude': location.get('longitude'),
        'accuracy': location.get('accuracy', 0),
        'timestamp': location.get('timestamp', '')
    }
def get_address_name(lat, lon, api_key):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    params = {"x": lon, "y": lat}
    headers = {"Authorization": f"KakaoAK {api_key}"}

    res = requests.get(url, params=params, headers=headers)
    res.raise_for_status()

    docs = res.json().get("documents", [])
    for doc in docs:
        if doc["region_type"] == "H":
            return doc["address_name"]

    return None

# 방법 2: IP 기반 위치 (가장 안정적!)
def get_location_from_ip():
    """IP 주소로 대략적인 위치 파악"""
    import requests

    try:
        # ipapi.co 사용 (무료, 일 1000회 제한)
        response = requests.get('https://ipapi.co/json/', timeout=5)
        data = response.json()

        return {
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'city': data.get('city'),
            'region': data.get('region'),
            'country': data.get('country_name'),
            'accuracy': 'IP-based (대략적)',
            'method': 'ip'
        }
    except Exception as e:
        st.error(f"IP 위치 확인 실패: {e}")
        return None



# ============================================
# 메인 앱
# ============================================

st.set_page_config(page_title="사용자 위치 받기", page_icon="📍")

st.title("📍 사용자 위치 받기")

# 탭으로 구분
tab1, tab2 = st.tabs(["🎯 JavaScript (정확)", "🌐 IP 기반 (간단)"])

# ============================================
# 탭 1: JavaScript Geolocation
# ============================================
with tab1:

    # 버튼으로 제어
    if st.button("📍 내 정확한 위치 가져오기", key="js_btn"):
        st.session_state.js_location_requested = True
    # 위치 요청이 있을 때만 컴포넌트 실행
    if st.session_state.get('js_location_requested', False):

        location_data = get_user_location()

        # 컴포넌트가 값을 반환할 때까지 대기
        if location_data is not None:
            if isinstance(location_data, dict):
                if 'error' in location_data:
                    st.error(f"❌ {location_data['error']}")
                    st.info("💡 팁: 브라우저 주소창 왼쪽의 자물쇠 아이콘을 클릭하여 위치 권한을 확인해보세요.")
                else:
                    #st.success("✅ 위치 정보를 성공적으로 받았습니다!")

                    if location_data["latitude"] is not None and location_data["longitude"] is not None:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("위도", f"{location_data['latitude']:.6f}")
                        with col2:
                            st.metric("경도", f"{location_data['longitude']:.6f}")
                    else:
                        st.metric("주소를 찾을 수 없습니다.")

                    # 세션에 저장
                    st.session_state.user_location = location_data
                    st.session_state.user_location['method'] = 'javascript'

                    # 초기화
                    st.session_state.js_location_requested = False



# ============================================
# 탭 2: IP 기반
# ============================================
with tab2:
    st.info("📌 권한 없이 대략적인 위치를 확인할 수 있습니다.")

    if st.button("🌐 IP로 위치 확인", key="ip_btn"):
        with st.spinner("위치 확인 중..."):
            location = get_location_from_ip()

        if location:
            st.success("✅ 대략적인 위치를 확인했습니다!")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("도시", location['city'] or 'N/A')
            with col2:
                st.metric("지역", location['region'] or 'N/A')
            with col3:
                st.metric("국가", location['country'] or 'N/A')

            if location['latitude'] is not None and location['longitude'] is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("위도", f"{location['latitude']:.6f}")
                with col2:
                    st.metric("경도", f"{location['longitude']:.6f}")
            else:
                st.warning("⚠️ 위도/경도 정보를 받지 못했습니다.")

            st.warning(f"⚠️ {location['accuracy']}")

            # 세션에 저장
            st.session_state.user_location = location

# ============================================
# 역지오코딩
# ============================================
if 'user_location' in st.session_state:
    st.divider()
    st.subheader("🗺️ 역지오코딩 (좌표 → 주소)")

    loc = st.session_state.user_location

    st.write(f"**저장된 위치**: {loc.get('method', 'unknown')} 방식")
    st.write(f"**좌표**: ({loc['latitude']:.6f}, {loc['longitude']:.6f})")

    if st.button("🔄 주소로 변환"):
        with st.spinner("주소 변환 중..."):
            address_data = get_address_name(loc['latitude'], loc['longitude'], data.rest_api)

        if address_data:
            st.success("✅ 주소 변환 완료!")

            # 전체 주소
            st.write(f"**📍 전체 주소**")
            st.info(address_data)

# ============================================
# 디버깅 정보
# ============================================
with st.expander("🔧 세션 상태 (디버깅용)"):
    st.json(st.session_state.to_dict())