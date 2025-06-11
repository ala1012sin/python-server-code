from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from collections import Counter
import heapq
import math
import json

app = FastAPI()

# ==== 모델 ====
class WiFiData(BaseModel):
    ssid: str
    bssid: str
    level: int

class WiFiRequest(BaseModel):
    apList: List[WiFiData]

# ==== 데이터 로드 ====
with open("building_data.json", "r", encoding="utf-8") as f:
    building_data = json.load(f)

graph = building_data["graph"]
ap_nodes = {bssid.lower(): tuple(data) for bssid, data in building_data["ap_nodes"].items()}
exits = building_data["exits"]

# ==== 양방향 edge 보정 ====
for node, data in graph.items():
    edges = data.get("edges", [])
    valid_edges = []
    for neighbor in edges:
        if neighbor in graph:
            valid_edges.append(neighbor)
            graph.setdefault(neighbor, {}).setdefault("edges", [])
            if node not in graph[neighbor]["edges"]:
                graph[neighbor]["edges"].append(node)
    graph[node]["edges"] = valid_edges

# ==== 유틸 함수 ====
def rssi_to_distance(rssi: int, A=-45, n=3) -> float:
    return 10 ** ((A - rssi) / (10 * n))

def euclidean_distance(p1, p2) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

# ==== 위치 추정 (RSSI 가중 평균 XYZ) ====
def weighted_average_xyz(wifi_list: List[WiFiData], ap_nodes: dict, A=-45, n=3) -> Optional[tuple]:
    sum_x = sum_y = sum_z = total_w = 0.0
    for wifi in wifi_list:
        b = wifi.bssid.lower()
        if b not in ap_nodes:
            continue
        x, y, z = ap_nodes[b]
        dist = rssi_to_distance(wifi.level, A, n)
        w = 1 / (dist + 1e-6)
        sum_x += x * w
        sum_y += y * w
        sum_z += z * w
        total_w += w
    if total_w == 0:
        return None
    return sum_x/total_w, sum_y/total_w, sum_z/total_w

# ==== 가장 가까운 노드 찾기 ====
def find_closest_node(pos, graph, floor):
    if floor == -1:
        z_min, z_max = -4, 0
    else:
        z_min, z_max = 3 * (floor - 1), 3 * floor
    hallway_nodes = {
        name: data for name, data in graph.items()
        if z_min <= data["pos"][2] < z_max and "H" in name
    }
    if not hallway_nodes:
        return None
    return min(hallway_nodes, key=lambda n: euclidean_distance(pos, hallway_nodes[n]["pos"]))

# ==== A* 알고리즘 ====
def a_star(start, goal, graph):
    def heuristic(a, b):
        return euclidean_distance(graph[a]["pos"], graph[b]["pos"])
    open_set = [(0, start)]
    came_from = {}
    g_score = {n: float('inf') for n in graph}
    f_score = {n: float('inf') for n in graph}
    g_score[start] = 0
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
        for neighbor in graph[current].get("edges", []):
            tentative = g_score[current] + heuristic(current, neighbor)
            if tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score[neighbor] = tentative + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

# ==== API 핸들러 ====
@app.post("/locate")
async def locate_user(data: WiFiRequest):
    # 로그 출력
    for ap in sorted(data.apList, key=lambda x: x.level, reverse=True):
        print(f"  - {ap.ssid} / {ap.bssid.lower()} / RSSI: {ap.level}")

    # 위치 추정 (XYZ)
    xyz = weighted_average_xyz(data.apList, ap_nodes)
    if not xyz:
        return {"error": "위치 추정 실패"}
    x, y, z = xyz

    # 층 계산
    if z < 0:
        floor = -1
    else:
        floor = int(z // 3) + 1
    print(f"📍 추정된 위치: x={x:.2f}, y={y:.2f}, z={z:.2f}, floor={floor}")

    # 가장 가까운 노드
    user_pos = (x, y, z)
    nearest_node = find_closest_node(user_pos, graph, floor)
    if not nearest_node:
        return {"error": f"층 {floor}에 가까운 노드가 없습니다."}

    # 최단 경로 탐색
    shortest_path = []
    for exit_node in exits:
        path = a_star(nearest_node, exit_node, graph)
        if path and (not shortest_path or len(path) < len(shortest_path)):
            shortest_path = path

    detailed_path = []
    for node_name in shortest_path:
        pos = graph[node_name]["pos"]
        detailed_path.append({"node": node_name, "x": pos[0], "y": pos[1]})

    result = {
        "estimated_location": {"x": x, "y": y, "z": z},
        "floor": floor,
        "closest_node": nearest_node,
        "escape_path": detailed_path
    }
    print("\n📤 응답 데이터:", json.dumps(result, indent=2, ensure_ascii=False))
    return result
