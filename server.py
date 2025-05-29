from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from collections import Counter
from scipy.optimize import minimize
import heapq
import math
import json
import numpy as np

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
ap_nodes = building_data["ap_nodes"]
exits = building_data["exits"]

# 양방향 edge 보정
for node, data in graph.items():
    # edges가 없으면 빈 리스트로 초기화
    edges = data.get("edges", [])
    valid_edges = []
    for neighbor in edges:
        if neighbor in graph:
            valid_edges.append(neighbor)
            if "edges" not in graph[neighbor]:
                graph[neighbor]["edges"] = []
            if node not in graph[neighbor]["edges"]:
                graph[neighbor]["edges"].append(node)
    graph[node]["edges"] = valid_edges  # 유효한 노드만 유지

# ==== 유틸 ====
def rssi_to_distance(rssi: int, A=-45, n=3):
    return 10 ** ((A - rssi) / (10 * n))

def euclidean_distance(p1, p2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

# ==== 층수 추정 ====
def estimate_floor_majority(wifi_list, ap_nodes):
    floors = []
    for wifi in wifi_list:
        bssid = wifi.bssid.lower()
        if bssid in ap_nodes:
            _, _, z = ap_nodes[bssid]
            floor = int(z // 3) + 1
            floors.append(floor)
    return Counter(floors).most_common(1)[0][0] if floors else -1

# ==== XY 위치 추정 ====
def trilateration_xy(wifi_list, ap_nodes):
    points, distances = [], []
    for wifi in wifi_list:
        bssid = wifi.bssid.lower()
        if bssid in ap_nodes:
            x, y, _ = ap_nodes[bssid]
        else:
            x, y = np.random.uniform(0, 10), np.random.uniform(0, 10)
        d = rssi_to_distance(wifi.level)
        points.append((x, y))
        distances.append(d)
    if len(points) < 3:
        return None
    def loss(pos):
        return sum((math.dist(pos, (px, py)) - d)**2 for (px, py), d in zip(points, distances))
    result = minimize(loss, np.mean(points, axis=0))
    return tuple(result.x) if result.success else tuple(np.mean(points, axis=0))

# ==== 가장 가까운 노드 찾기 ====
def find_closest_node(pos, graph, floor):
    z_min, z_max = 3 * (floor - 1), 3 * floor
    nodes_in_floor = {n: d for n, d in graph.items() if z_min <= d["pos"][2] < z_max}
    closest = min(nodes_in_floor, key=lambda n: euclidean_distance(pos, nodes_in_floor[n]["pos"]))
    if "door" not in closest:
        base = closest.split("_")[0]
        door_node = base + "_door"
        if door_node in graph:
            return door_node
    return closest

# ==== A* 알고리즘 ====
def a_star(start, goal, graph):
    def heuristic(a, b):
        return euclidean_distance(graph[a]["pos"], graph[b]["pos"])
    open_set = [(0, start)]
    came_from, g_score, f_score = {}, {n: float('inf') for n in graph}, {n: float('inf') for n in graph}
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

# ==== API ====
@app.post("/locate")
async def locate_user(data: WiFiRequest):
    # === 로그: 요청 ===
    print("\n📡 요청된 AP 리스트:")
    sorted_ap = sorted(data.apList, key=lambda x: x.level, reverse=True)
    for ap in sorted_ap:
        print(f"  - {ap.ssid} / {ap.bssid.lower()} / RSSI: {ap.level}")

    # === 상위 6개 AP만 사용 ===
    top_aps = sorted_ap[:6]

    # === 층수, 위치, 노드, 경로 계산 ===
    floor = estimate_floor_majority(top_aps, ap_nodes)
    if floor == -1:
        return {"error": "층수 추정 실패"}

    xy = trilateration_xy(top_aps, ap_nodes)
    if not xy:
        return {"error": "위치 추정 실패"}

    user_pos = (xy[0], xy[1], 1.5 + 3 * (floor - 1))
    nearest_node = find_closest_node(user_pos, graph, floor)

    shortest_path = []
    for exit in exits:
        path = a_star(nearest_node, exit, graph)
        if path and (not shortest_path or len(path) < len(shortest_path)):
            shortest_path = path

    result = {
        "estimated_location": {"x": user_pos[0], "y": user_pos[1], "z": user_pos[2]},
        "floor": floor,
        "closest_node": nearest_node,
        "escape_path": shortest_path
    }

    # === 로그: 응답 ===
    print("\n📤 응답 데이터:", json.dumps(result, indent=2, ensure_ascii=False))

    return result
