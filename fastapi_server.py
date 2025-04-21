from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Tuple
import numpy as np
from scipy.optimize import minimize
import heapq
import json

app = FastAPI()

# AP 좌표 저장 (
ap_estimated_positions: Dict[str, Tuple[float, float]] = {}

#  건물 데이터 
building_data = {
    "nodes": {
        "문": (0, 0),
        "복도1": (5, 0),
        "복도2": (10, 0),
        "계단": (12, 5),
        "방1": (5, 5),
        "방2": (10, 10)
    },
    "edges": [
        ("문", "복도1"), ("복도1", "복도2"), ("복도2", "계단"),
        ("복도1", "방1"), ("복도2", "방2")
    ],
    "exit": "문"  
}

#  그래프 생성
building_graph = {node: [] for node in building_data["nodes"]}
for n1, n2 in building_data["edges"]:
    building_graph[n1].append(n2)
    building_graph[n2].append(n1)

# RSSI → 거리 변환 함수
def rssi_to_distance(rssi: int, A=-45, n=3):
    return 10 ** ((A - rssi) / (10 * n))

# 삼각측량 
def trilateration(ap_positions, distances):
    def error_func(guess):
        x, y = guess
        return sum((np.sqrt((x - ap_x) ** 2 + (y - ap_y) ** 2) - d) ** 2
                   for (ap_x, ap_y), d in zip(ap_positions, distances))

    initial_guess = np.mean(ap_positions, axis=0)
    result = minimize(error_func, initial_guess, method='L-BFGS-B')

    return tuple(result.x) if result.success else None

# 가장 가까운 노드 찾기
def closest_node(location):
    return min(building_data["nodes"], key=lambda node: (building_data["nodes"][node][0] - location[0]) ** 2 +
                                                          (building_data["nodes"][node][1] - location[1]) ** 2)

#  A* 알고리즘
def a_star(start, goal):
    def heuristic(a, b):
        ax, ay = building_data["nodes"][a]
        bx, by = building_data["nodes"][b]
        return abs(ax - bx) + abs(ay - by)

    open_set = [(0, start)]
    came_from = {}
    g_score = {node: float("inf") for node in building_data["nodes"]}
    g_score[start] = 0
    f_score = {node: float("inf") for node in building_data["nodes"]}
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        for neighbor in building_graph[current]:
            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None

# Wi-Fi 데이터 모델
class WiFiData(BaseModel):
    bssid: str
    level: int

class WiFiRequest(BaseModel):
    wifi_list: List[WiFiData]

# Wi-Fi 데이터를 받아 사용자 위치 & 최단 경로 반환 API
@app.post("/find_path")
async def find_path(data: WiFiRequest):
    if len(data.wifi_list) < 3:
        return {"error": "AP가 최소 3개 이상 필요합니다."}

    # (1) 기존 AP 위치 확인 or 랜덤 초기값
    ap_positions = {bssid: ap_estimated_positions.get(bssid, (np.random.uniform(0, 10), np.random.uniform(0, 10)))
                    for bssid in [wifi.bssid for wifi in data.wifi_list]}

    # (2) RSSI → 거리 변환
    distances = [rssi_to_distance(wifi.level) for wifi in data.wifi_list]

    # (3) 삼각측량으로 사용자 위치 예측
    estimated_position = trilateration(list(ap_positions.values()), distances)

    if estimated_position is None:
        return {"error": "사용자 위치를 찾을 수 없습니다."}

    # (4) 가장 가까운 노드 찾기
    user_node = closest_node(estimated_position)

    # (5) 최단 경로 계산 (A* 알고리즘)
    exit_node = building_data["exit"]
    path = a_star(user_node, exit_node)

    return {
        "user_location": {"x": estimated_position[0], "y": estimated_position[1]},
        "nearest_node": user_node,
        "path": path
    }
