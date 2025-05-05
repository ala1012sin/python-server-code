from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Tuple
import heapq
import math
from scipy.optimize import minimize
from collections import Counter

app = FastAPI()

# ==========================
# 데이터 모델 정의
# ==========================
class WiFiData(BaseModel):
    ssid: str
    bssid: str
    level: int

class WiFiRequest(BaseModel):
    wifi_list: List[WiFiData]
    building_id: str
    building_data: Dict  # 건물 그래프와 AP 위치 포함

# ==========================
# RSSI → 거리 변환
# ==========================
def rssi_to_distance(rssi: int, A=-45, n=3):
    return 10 ** ((A - rssi) / (10 * n))

# ==========================
# 유클리드 거리 계산
# ==========================
def euclidean_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

# ==========================
# 3D Trilateration 위치 추정
# ==========================
def trilateration_3d(wifi_list: List[WiFiData], ap_nodes: Dict[str, Tuple[float, float, float]]) -> Tuple[float, float, float]:
    points = []
    distances = []
    for wifi in wifi_list:
        if wifi.bssid not in ap_nodes:
            continue
        x, y, z = ap_nodes[wifi.bssid]
        d = rssi_to_distance(wifi.level)
        points.append((x, y, z))
        distances.append(d)

    if len(points) < 4:
        return weighted_average_position(wifi_list, ap_nodes)

    def loss(pos):
        return sum((euclidean_distance(pos, pt) - d) ** 2 for pt, d in zip(points, distances))

    initial_guess = points[0]
    result = minimize(loss, initial_guess)
    return tuple(result.x)

# ==========================
# AP 가중 평균 방식 (백업용)
# ==========================
def weighted_average_position(wifi_list: List[WiFiData], ap_nodes: Dict[str, Tuple[float, float, float]]) -> Tuple[float, float, float]:
    weighted_x = weighted_y = weighted_z = total_weight = 0.0
    for wifi in wifi_list:
        if wifi.bssid not in ap_nodes:
            continue
        ap_x, ap_y, ap_z = ap_nodes[wifi.bssid]
        distance = rssi_to_distance(wifi.level)
        weight = 1 / (distance + 1e-6)
        weighted_x += ap_x * weight
        weighted_y += ap_y * weight
        weighted_z += ap_z * weight
        total_weight += weight
    if total_weight == 0:
        return None
    return (weighted_x / total_weight, weighted_y / total_weight, weighted_z / total_weight)

# ==========================
# z → 층 변환 함수
# ==========================
def z_to_floor(z: float) -> int:
    if z < 3:
        return 1
    elif z < 6:
        return 2
    elif z < 9:
        return 3
    elif z < 12:
        return 4
    return -1

# ==========================
# 다수결 기반 층 추정
# ==========================
def estimate_floor_majority(wifi_list: List[WiFiData], ap_nodes: Dict[str, Tuple[float, float, float]]) -> int:
    floor_votes = []
    for wifi in wifi_list:
        if wifi.bssid in ap_nodes:
            _, _, ap_z = ap_nodes[wifi.bssid]
            floor = z_to_floor(ap_z)
            floor_votes.append(floor)
    if not floor_votes:
        return -1
    most_common = Counter(floor_votes).most_common(1)
    return most_common[0][0]

# ==========================
# 가장 가까운 노드 찾기
# ==========================
def find_closest_node(pos: Tuple[float, float, float], graph: Dict[str, Dict], floor: int) -> str:
    target_z_min = (floor - 1) * 3
    target_z_max = target_z_min + 3
    filtered_nodes = {
        k: v for k, v in graph.items()
        if target_z_min <= v['pos'][2] < target_z_max
    }
    return min(filtered_nodes.keys(), key=lambda node_id: euclidean_distance(pos, tuple(filtered_nodes[node_id]['pos'])))

# ==========================
# A* 최단 경로
# ==========================
def a_star(start_id: str, goal_id: str, graph: Dict[str, Dict]) -> List[str]:
    def heuristic(n1, n2):
        p1 = graph[n1]['pos']
        p2 = graph[n2]['pos']
        return euclidean_distance(tuple(p1), tuple(p2))

    open_set = [(0, start_id)]
    came_from = {}
    g_score = {node: float('inf') for node in graph}
    g_score[start_id] = 0
    f_score = {node: float('inf') for node in graph}
    f_score[start_id] = heuristic(start_id, goal_id)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal_id:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start_id)
            return path[::-1]
        for neighbor in graph[current]['edges']:
            tentative_g_score = g_score[current] + heuristic(current, neighbor)
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal_id)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

# ==========================
# API: 위치 추정 + 경로 계산
# ==========================
@app.post("/locate")
async def locate_user(data: WiFiRequest):
    graph_data = data.building_data["graph"]     # 노드 + 엣지 정보
    ap_nodes = data.building_data["ap_nodes"]    # AP 위치 (bssid -> (x, y, z))
    exits = data.building_data["exits"]          # 탈출구 노드 ID 목록

    user_pos_raw = trilateration_3d(data.wifi_list, ap_nodes)
    if user_pos_raw is None:
        return {"error": "위치 추정 실패"}

    floor = estimate_floor_majority(data.wifi_list, ap_nodes)
    z_corrected = 1.5 + 3 * (floor - 1)
    user_pos = (user_pos_raw[0], user_pos_raw[1], z_corrected)
    user_node = find_closest_node(user_pos, graph_data, floor)

    # 가장 가까운 탈출구로 경로 탐색
    shortest_path = []
    for exit_node in exits:
        path = a_star(user_node, exit_node, graph_data)
        if path and (not shortest_path or len(path) < len(shortest_path)):
            shortest_path = path

    return {
        "estimated_location": {"x": user_pos[0], "y": user_pos[1], "z": user_pos[2]},
        "floor": floor,
        "closest_node": user_node,
        "escape_path": shortest_path
    }
