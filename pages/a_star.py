import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from folium import plugins
import time
import heapq
from streamlit_folium import folium_static
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="도서관 찾기", layout="wide")

# 제목
st.title("가장 가까운 도서관")

# 사이드바 - 입력
st.sidebar.header("📍 좌표 입력")

# ✅ 세션 상태 초기화 및 값 가져오기
try:
    # user 딕셔너리 존재 확인
    if "user" not in st.session_state:
        st.session_state.user = {}

    # 출발지 좌표 (기본값 설정)
    if "lat" not in st.session_state.user:
        st.session_state.user["lat"] = 37.3253
    if "lng" not in st.session_state.user:  # ✅ lng로 통일
        st.session_state.user["lng"] = 126.8178

    start_lat = st.session_state.user["lat"]
    start_lon = st.session_state.user["lng"]  # ✅ lng 사용

    # 도착지 좌표 (도서관)
    if "library" in st.session_state.user and st.session_state.user["library"]:
        # ✅ library는 (list, error) 튜플 형태
        library_data = st.session_state.user["library"]

        if isinstance(library_data, tuple) and library_data[0]:
            # ✅ 첫 번째 도서관 정보 가져오기
            nearest_library = library_data[0][0]["library"]
            end_lat = float(nearest_library["latitude"])
            end_lon = float(nearest_library["longitude"])
            library_name = nearest_library.get("libName", "도서관")
        else:
            # 도서관 정보 없음 (기본값)
            end_lat = 37.361570
            end_lon = 126.928288
            library_name = "기본 도서관"
    else:
        # 도서관 정보 없음 (기본값)
        end_lat = 37.361570
        end_lon = 126.928288
        library_name = "기본 도서관"

except Exception as e:
    st.error(f"⚠️ 세션 데이터 로드 실패: {e}")
    # 기본값으로 설정
    start_lat = 37.3253
    start_lon = 126.8178
    end_lat = 37.361570
    end_lon = 126.928288
    library_name = "기본 도서관"

# 📍 현재 좌표 정보 표시
st.sidebar.markdown("### 📍 현재 경로")
st.sidebar.info(f"""
**출발지**  
위도: {start_lat:.6f}  
경도: {start_lon:.6f}

**도착지 ({library_name})**  
위도: {end_lat:.6f}  
경도: {end_lon:.6f}
""")

# 🔍 디버깅 정보 (개발 중에만 사용)
with st.sidebar.expander("🔧 디버그 정보"):
    st.json({
        "user_keys": list(st.session_state.user.keys()) if "user" in st.session_state else [],
        "start": f"({start_lat}, {start_lon})",
        "end": f"({end_lat}, {end_lon})",
        "library_exists": "library" in st.session_state.user,
        "selected_book": st.session_state.get("selected_book", "None")
    })

# 알고리즘 선택
algorithm = st.sidebar.selectbox("알고리즘 선택", ["A* (A-Star)", "Dijkstra", "둘 다 비교"])

# 보행 속도 설정
walking_speed = st.sidebar.slider("보행 속도 (km/h)", 3.0, 6.0, 4.5, 0.5)


# A* 알고리즘 구현
def astar_path(G, source, target, weight='length'):
    """A* 알고리즘으로 최단 경로 찾기"""

    def heuristic(n1, n2):
        # 유클리드 거리 (휴리스틱)
        x1, y1 = G.nodes[n1]['x'], G.nodes[n1]['y']
        x2, y2 = G.nodes[n2]['x'], G.nodes[n2]['y']
        return ox.distance.great_circle(y1, x1, y2, x2)

    # 시작 시간 측정
    start_time = time.time()

    # 초기화
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(source, target), 0, source, [source]))
    visited = set()
    nodes_visited = 0

    while open_set:
        f, g, current, path = heapq.heappop(open_set)

        if current in visited:
            continue

        visited.add(current)
        nodes_visited += 1

        # 목표 도달
        if current == target:
            end_time = time.time()
            return path, g, end_time - start_time, nodes_visited

        # 이웃 노드 탐색
        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                edge_weight = G[current][neighbor][0].get(weight, 1)
                new_g = g + edge_weight
                new_f = new_g + heuristic(neighbor, target)
                heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor]))

    return None, None, None, None


# Dijkstra 알고리즘 구현
def dijkstra_path(G, source, target, weight='length'):
    """Dijkstra 알고리즘으로 최단 경로 찾기"""

    start_time = time.time()

    # 초기화
    open_set = []
    heapq.heappush(open_set, (0, source, [source]))
    visited = set()
    nodes_visited = 0

    while open_set:
        dist, current, path = heapq.heappop(open_set)

        if current in visited:
            continue

        visited.add(current)
        nodes_visited += 1

        # 목표 도달
        if current == target:
            end_time = time.time()
            return path, dist, end_time - start_time, nodes_visited

        # 이웃 노드 탐색
        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                edge_weight = G[current][neighbor][0].get(weight, 1)
                new_dist = dist + edge_weight
                heapq.heappush(open_set, (new_dist, neighbor, path + [neighbor]))

    return None, None, None, None


# 경로 찾기 버튼
if st.button("🔍 경로 찾기", type="primary"):

    with st.spinner("OpenStreetMap 데이터 다운로드 중..."):
        try:
            # 중심점 계산
            center_lat = (start_lat + end_lat) / 2
            center_lon = (start_lon + end_lon) / 2

            # 거리 계산 (여유있게 다운로드)
            dist = ox.distance.great_circle(start_lat, start_lon, end_lat, end_lon)

            # OSM 보행자 네트워크 다운로드
            G = ox.graph_from_point(
                (center_lat, center_lon),
                dist=dist * 1.5,  # 여유있게
                network_type='walk'  # 보행자 도로
            )

            st.success(f"✅ 도로 네트워크 다운로드 완료! (노드: {len(G.nodes)}, 엣지: {len(G.edges)})")

        except Exception as e:
            st.error(f"❌ 데이터 다운로드 실패: {e}")
            st.stop()

    # 가장 가까운 노드 찾기
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)

    # 컬럼 레이아웃
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🗺️ 경로 시각화")

        # 지도 생성
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=13,
            tiles='OpenStreetMap'
        )

        # 출발/도착 마커
        folium.Marker(
            [start_lat, start_lon],
            popup="출발지",
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)

        folium.Marker(
            [end_lat, end_lon],
            popup=f"도착지 ({library_name})",
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)

    with col2:
        st.subheader("📊 알고리즘 성능 비교")

    # 알고리즘 실행
    results = []

    if algorithm in ["A* (A-Star)", "둘 다 비교"]:
        with st.spinner("A* 알고리즘 실행 중..."):
            path_astar, dist_astar, time_astar, nodes_astar = astar_path(G, start_node, end_node)

            if path_astar:
                # 경로 좌표 추출
                route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path_astar]

                # 지도에 경로 그리기
                folium.PolyLine(
                    route_coords,
                    color='blue',
                    weight=5,
                    opacity=0.7,
                    popup='A* 경로'
                ).add_to(m)

                # 결과 저장
                results.append({
                    "알고리즘": "A*",
                    "거리 (m)": round(dist_astar, 1),
                    "시간 (분)": round(dist_astar / 1000 / walking_speed * 60, 1),
                    "계산시간 (ms)": round(time_astar * 1000, 2),
                    "탐색 노드": nodes_astar
                })

    if algorithm in ["Dijkstra", "둘 다 비교"]:
        with st.spinner("Dijkstra 알고리즘 실행 중..."):
            path_dijkstra, dist_dijkstra, time_dijkstra, nodes_dijkstra = dijkstra_path(G, start_node, end_node)

            if path_dijkstra:
                # 경로 좌표 추출
                route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path_dijkstra]

                # 지도에 경로 그리기 (비교 시 다른 색)
                color = 'red' if algorithm == "둘 다 비교" else 'blue'
                folium.PolyLine(
                    route_coords,
                    color=color,
                    weight=5,
                    opacity=0.7,
                    popup='Dijkstra 경로'
                ).add_to(m)

                # 결과 저장
                results.append({
                    "알고리즘": "Dijkstra",
                    "거리 (m)": round(dist_dijkstra, 1),
                    "시간 (분)": round(dist_dijkstra / 1000 / walking_speed * 60, 1),
                    "계산시간 (ms)": round(time_dijkstra * 1000, 2),
                    "탐색 노드": nodes_dijkstra
                })

    # 결과 출력
    with col1:
        folium_static(m, width=800, height=600)

    with col2:
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            # 성능 비교
            # 성능 비교
            if len(results) == 2:
                st.markdown("### 🔥 성능 개선")

                # ✅ A*와 Dijkstra 구분
                astar_result = next((r for r in results if r["알고리즘"] == "A*"), None)
                dijkstra_result = next((r for r in results if r["알고리즘"] == "Dijkstra"), None)

                if astar_result and dijkstra_result:
                    # ✅ 올바른 비교: Dijkstra / A*
                    speedup = dijkstra_result["계산시간 (ms)"] / astar_result["계산시간 (ms)"]
                    node_reduction = (1 - astar_result["탐색 노드"] / dijkstra_result["탐색 노드"]) * 100

                    # ✅ 실제로 A*가 빠른지 확인
                    if speedup > 1:
                        st.metric("계산 속도", f"{speedup:.2f}배 빠름", delta="A* 승리 🎉")
                        st.metric("노드 탐색", f"{node_reduction:.1f}% 감소", delta="A* 효율적 ⚡")
                    else:
                        st.metric("계산 속도", f"{1 / speedup:.2f}배 느림", delta="Dijkstra 승리", delta_color="inverse")
                        st.metric("노드 탐색", f"{node_reduction:.1f}% 감소", delta="A*가 더 적게 탐색")

            # 상세 정보
            st.markdown("### 📝 상세 정보")
            for result in results:
                with st.expander(f"{result['알고리즘']} 상세"):
                    st.write(f"**직선거리**: {round(ox.distance.great_circle(start_lat, start_lon, end_lat, end_lon), 1)}m")
                    st.write(f"**실제거리**: {result['거리 (m)']}m")
                    st.write(f"**예상시간**: {result['시간 (분)']}분 (속도: {walking_speed}km/h)")
                    st.write(f"**알고리즘 실행시간**: {result['계산시간 (ms)']}ms")
                    st.write(f"**탐색한 노드 수**: {result['탐색 노드']}개")

# 뒤로가기 버튼
st.divider()
if st.button("⬅️ 도서 목록으로 돌아가기", use_container_width=True):
    st.switch_page("app.py")

# 사이드바 하단 - 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 프로젝트 정보")
st.sidebar.info("""
**데이터 출처**: OpenStreetMap  
**알고리즘**: A*, Dijkstra  
**언어**: Python  
**라이브러리**: osmnx, networkx, folium
""")