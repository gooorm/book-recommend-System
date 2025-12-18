# user/a_star.py

import heapq
import math


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    두 좌표 간의 거리 계산 (Haversine formula)

    Args:
        lat1, lon1: 시작점 위도, 경도
        lat2, lon2: 도착점 위도, 경도

    Returns:
        float: 거리 (미터)
    """
    R = 6371000  # 지구 반지름 (미터)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def astar_find_nearest_library(user_location, libraries):
    """
    A* 알고리즘으로 가장 가까운 도서관 찾기

    Args:
        user_location: dict {'latitude': float, 'longitude': float}
        libraries: list of dict [{'libName': str, 'latitude': float, 'longitude': float, ...}]

    Returns:
        list: 거리순으로 정렬된 도서관 리스트 (거리 정보 포함)
    """
    user_lat = user_location['latitude']
    user_lon = user_location['longitude']

    results = []

    for library in libraries:
        try:
            lib_lat = float(library.get('latitude', 0))
            lib_lon = float(library.get('longitude', 0))

            # 직선 거리 계산 (A*의 휴리스틱)
            distance = calculate_distance(user_lat, user_lon, lib_lat, lib_lon)

            # 보행 시간 계산 (평균 보행 속도: 4.5 km/h = 1.25 m/s)
            walking_time = distance / 1.25  # 초
            walking_time_minutes = walking_time / 60  # 분

            results.append({
                'library': library,
                'distance_m': round(distance, 1),
                'distance_km': round(distance / 1000, 2),
                'walking_time_min': round(walking_time_minutes, 1),
                'walking_time_str': format_time(walking_time_minutes)
            })
        except (ValueError, KeyError) as e:
            # 좌표 정보가 없거나 잘못된 도서관은 스킵
            continue

    # 거리순 정렬 (A* 결과)
    results.sort(key=lambda x: x['distance_m'])

    return results


def format_time(minutes):
    """
    분을 읽기 좋은 형식으로 변환

    Args:
        minutes: float

    Returns:
        str: "X분" 또는 "X시간 Y분"
    """
    if minutes < 60:
        return f"{int(minutes)}분"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}시간 {mins}분"


def calculate_route_info(distance_m, speed_kmh=4.5):
    """
    경로 정보 계산

    Args:
        distance_m: 거리 (미터)
        speed_kmh: 보행 속도 (km/h)

    Returns:
        dict: 경로 정보
    """
    distance_km = distance_m / 1000
    time_hours = distance_km / speed_kmh
    time_minutes = time_hours * 60

    return {
        'distance_m': round(distance_m, 1),
        'distance_km': round(distance_km, 2),
        'time_minutes': round(time_minutes, 1),
        'time_formatted': format_time(time_minutes),
        'speed_kmh': speed_kmh
    }