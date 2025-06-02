from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from collections import Counter
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

# ==== 양방향 edge 보정 ====
for node, data in graph.items():
    edges = data.get("edges", [])
    valid_edges = []
    for neighbor in edges:
        if neighbor in graph:
            valid_edges.append(neighbor)
            if "edges" not in graph[neighbor]:
                graph[neighbor]["edges"] = []
            if node not in graph[neighbor]["edges"]:
                graph[neighbor]["edges"].append(node)
    graph[node]["edges"] = valid_edges

# ==== 유틸 함수 ====
def rssi_to_distance(rssi: int, A=-45, n=3):
    return 10 ** ((A - rssi) / (10 * n))

def euclidean_distance(p1, p2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

# ==== 층수 추정 ====
def get_floor_from_z(z):
    if z < 0:
        return -1
    elif 0 <= z < 3:
        return 1
    elif 3 <= z < 6:
        return 2
    elif 6 <= z < 9:
        return 3
    elif 9 <= z < 12:
        return 4
    else:
        return 5

def estimate_floor_by_top6_ap(wifi_list, ap_nodes):
    valid_aps = [wifi for wifi in wifi_list if wifi.bssid.lower() in ap_nodes]
    top6 = sorted(valid_aps, key=lambda x: x.level, reverse=True)[:6]
    floors = []
    for wifi in top6:
        bssid = wifi.bssid.lower()
        _, _, z = ap_nodes[bssid]
        floor = get_floor_from_z(z)
        floors.append(floor)
    return Counter(floors).most_common(1)[0][0] if floors else -1

# ==== 위치 추정 (RSSI 가중 평균 방식) ====
def weighted_average_xy(wifi_list, ap_nodes, A=-45, n=3):
    weighted_sum_x = 0
    weighted_sum_y = 0
    total_weight = 0

    for wifi in wifi_list:
        bssid = wifi.bssid.lower()
        if bssid in ap_nodes:
            x, y, _ = ap_nodes[bssid]
        else:
            continue

        distance = rssi_to_distance(wifi.level, A, n)
        weight = 1 / (distance + 1e-6)
        weighted_sum_x += x * weight
        weighted_sum_y += y * weight
        total_weight += weight

    if total_weight == 0:
        return None

    return weighted_sum_x / total_weight, weighted_sum_y / total_weight

# ==== 가장 가까운 노드 찾기 ====
def find_closest_node(pos, graph, floor):
    z_min, z_max = 3 * (floor - 1), 3 * floor
    nodes_in_floor = {n: d for n, d in graph.items() if z_min <= d["pos"][2] < z_max}
    if not nodes_in_floor:
        return None
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
    sorted_ap = sorted(data.apList, key=lambda x: x.level, reverse=True)
    for ap in sorted_ap:
        print(f"  - {ap.ssid} / {ap.bssid.lower()} / RSSI: {ap.level}")

    # 층 추정
    floor = estimate_floor_by_top6_ap(data.apList, ap_nodes)
    print(f"📍 추정된 층수: {floor}")
    if floor == -1:
        return {"error": "층수 추정 실패"}

    # 위치 추정
    xy = weighted_average_xy(data.apList, ap_nodes)
    if not xy:
        return {"error": "위치 추정 실패"}

    user_pos = (xy[0], xy[1], 1.5 + 3 * (floor - 1))
    nearest_node = find_closest_node(user_pos, graph, floor)
    if not nearest_node:
        return {"error": f"층 {floor}에 가까운 노드가 없습니다."}

    shortest_path = []
    for exit in exits:
        path = a_star(nearest_node, exit, graph)
        if path and (not shortest_path or len(path) < len(shortest_path)):
            shortest_path = path

    result = {
        "estimated_location": {
            "x": user_pos[0],
            "y": user_pos[1],
            "z": user_pos[2]
        },
        "floor": floor,
        "closest_node": nearest_node,
        "escape_path": shortest_path
    }

    print("\n📤 응답 데이터:", json.dumps(result, indent=2, ensure_ascii=False))
    return result
