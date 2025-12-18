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

# 기본 좌표값 (과제에서 제공된 좌표)
# start_lat = st.sidebar.number_input("출발지 위도", value=37.3253, format="%.6f")
# start_lon = st.sidebar.number_input("출발지 경도", value=126.8178, format="%.6f")
# end_lat = st.sidebar.number_input("도착지 위도", value=37.361570, format="%.6f")
# end_lon = st.sidebar.number_input("도착지 경도", value=126.928288, format="%.6f")
if "user" not in st.session_state.user:
    st.session_state.user["lat"] = 37.3253
if "user" not in st.session_state.user:
    st.session_state.user["lon"] = 126.8178
start_lat = st.session_state.user["lat"]
start_lon = st.session_state.user["lon"]
end_lat = float(st.session_state.user["library"][0][0]["library"]["latitude"])
end_lon = float(st.session_state.user["library"][0][0]["library"]["longitude"])

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
            popup="도착지",
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
            if len(results) == 2:
                st.markdown("### 🔥 성능 개선")
                speedup = (results[1]["계산시간 (ms)"] / results[0]["계산시간 (ms)"])
                node_reduction = (1 - results[0]["탐색 노드"] / results[1]["탐색 노드"]) * 100

                st.metric("계산 속도", f"{speedup:.1f}배 빠름", delta="A* 승리")
                st.metric("노드 탐색", f"{node_reduction:.1f}% 감소", delta="A* 효율적")

            # 상세 정보
            st.markdown("### 📝 상세 정보")
            for result in results:
                with st.expander(f"{result['알고리즘']} 상세"):
                    st.write(f"**직선거리**: {round(ox.distance.great_circle(start_lat, start_lon, end_lat, end_lon), 1)}m")
                    st.write(f"**실제거리**: {result['거리 (m)']}m")
                    st.write(f"**예상시간**: {result['시간 (분)']}분 (속도: {walking_speed}km/h)")
                    st.write(f"**알고리즘 실행시간**: {result['계산시간 (ms)']}ms")
                    st.write(f"**탐색한 노드 수**: {result['탐색 노드']}개")

# 사이드바 하단 - 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 프로젝트 정보")
st.sidebar.info("""
**데이터 출처**: OpenStreetMap  
**알고리즘**: A*, Dijkstra  
**언어**: Python  
**라이브러리**: osmnx, networkx, folium
""")
#
# # 메인 설명
# with st.expander("ℹ️ 프로젝트 설명"):
#     st.markdown("""
#     ## 보행자 최단 경로 찾기 시스템
#
#     ### 📌 문제 정의
#     - 실제 도로 네트워크를 기반으로 두 지점 간 보행자 최단 경로 찾기
#     - 다양한 알고리즘의 성능 비교 및 분석
#
#     ### 📊 사용 데이터
#     - **OpenStreetMap (OSM)**: 전 세계 오픈소스 지도 데이터
#     - 도로, 보행로, 건물 등의 실제 지리 정보
#     - `osmnx` 라이브러리를 통한 데이터 다운로드
#
#     ### 🧮 구현 알고리즘
#
#     #### 1. A* (A-Star) 알고리즘
#     - **개념**: f(n) = g(n) + h(n)
#         - g(n): 시작점부터 현재까지의 실제 비용
#         - h(n): 현재부터 목표까지의 예상 비용 (휴리스틱)
#     - **휴리스틱**: Great Circle Distance (구면 거리)
#     - **장점**: 목표 지향적 탐색으로 빠른 속도
#
#     #### 2. Dijkstra 알고리즘
#     - **개념**: 시작점부터 모든 노드까지의 최단 거리 계산
#     - **특징**: 휴리스틱 없이 모든 방향 균등 탐색
#     - **장점**: 확실한 최단 경로 보장
#     - **단점**: A*보다 느림
#
#     ### ⚡ 성능 분석
#     - **시간 복잡도**: O((V + E) log V)
#     - **공간 복잡도**: O(V)
#     - **실제 측정**: 계산 시간, 탐색 노드 수 비교
#
#     ### 🎯 기대 효과
#     - 실제 보행자 내비게이션 시스템 구현 가능
#     - 알고리즘 성능 비교를 통한 최적 선택
#     - 교통약자를 위한 맞춤형 경로 안내 확장 가능
#     """)
#
# with st.expander("🛠️ 사용 방법"):
#     st.markdown("""
#     1. **좌표 입력**: 왼쪽 사이드바에서 출발지/도착지 위경도 입력
#     2. **알고리즘 선택**: A*, Dijkstra, 또는 둘 다 선택
#     3. **보행 속도 설정**: 개인의 보행 속도 조정 (기본 4.5km/h)
#     4. **경로 찾기**: 버튼 클릭으로 실행
#     5. **결과 확인**: 지도에서 경로 확인 및 성능 비교
#
#     **💡 팁**:
#     - "둘 다 비교"를 선택하면 두 알고리즘의 성능 차이를 명확히 볼 수 있습니다!
#     - 파란색 선은 A* 경로, 빨간색 선은 Dijkstra 경로입니다.
#     """)