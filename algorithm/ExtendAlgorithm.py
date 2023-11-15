#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import Global
import NetworkInfo as ni
import copy
import util
import math
import random


def extend_deploy(bandwidth_origin, node_list, request_list):
    """扩展部署算法"""

    # 剩余带宽矩阵
    bandwidth = copy.copy(bandwidth_origin)

    # 储存每个请求的带宽消耗矩阵
    flow_matrix_request = {}

    # 实例注册表(每种NF一个子表)
    instance_registry = [[] for i in range(Global.NF_TYPE_NUM)]

    # 每个请求选择的部署位置
    request_placement = []

    # 每个类型nf实例个数
    instance_num = [0] * Global.NF_TYPE_NUM

    # 初始化 request_placement, 并将请求排序(按照流量速率/可用性要求)
    # TODO：排序依据加上NF表长度
    rate_sum = sum(request.rate for request in request_list)
    avail_max = max(request.avail for request in request_list)
    avail_min = min(request.avail for request in request_list)
    for r in request_list:
        request_placement.append([{} for nf in r.nf_list])
        if avail_max == avail_min:
            r.rank = r.rate / float(rate_sum)
        else:
            r.rank = r.rate / float(rate_sum) + (r.avail - avail_min) / (
                avail_max - avail_min
            )
    request_list = sorted(request_list, key=lambda r: r.rank, reverse=True)

    """ 依次部署请求 """
    for request in request_list:
        # 找离源点和汇点最近的Node
        candidate_nodes_distance = []
        for v in range(len(node_list)):
            candidate_nodes_distance.append(
                (
                    v,
                    util.distance(bandwidth, request.src, v)
                    + util.distance(bandwidth, v, request.dst),
                )
            )
        candidate_nodes_distance = sorted(
            sorted(
                candidate_nodes_distance,
                key=lambda n: node_list[n[0]].avail,
                reverse=True,
            ),
            key=lambda n: n[1],
        )
        # 按照距离源汇点距离之和远近进行排序后的Node表
        candidate_nodes = [n[0] for n in candidate_nodes_distance]

        """ 对每个要部署的nf（第i个）放置第一个实例 """
        for i, nf in enumerate(request.nf_list):
            # 在候选表中依次选择
            for v in candidate_nodes:
                # 如果已经有同类实例，且capacity还有剩余
                same_instance = None
                for instance in node_list[v].instances:
                    if instance.type == nf and instance.capacity > 0:
                        same_instance = instance
                if same_instance is not None:
                    # 在表中登记这个新实例
                    request_placement[request.id][i][v] = same_instance
                    break

                # 如果没有同类实例
                elif node_list[v].CPU > Global.NF_CPU_REQUIREMENT[nf]:
                    # 新建一个实例，并放置在当前Node
                    new_instance = ni.Instance(instance_num[nf], nf)
                    instance_num[nf] += 1
                    new_instance.placement = v
                    # 在两个表中登记这个新实例
                    request_placement[request.id][i][v] = new_instance
                    instance_registry[nf].append(new_instance)
                    # 更新Node
                    node_list[v].CPU -= Global.NF_CPU_REQUIREMENT[nf]
                    node_list[v].instances.append(new_instance)
                    break
            # 没有满足资源需求的Node了
            else:
                raise AssertionError("No CPU!")

        # 计算可用性
        avail_bottleneck_index = util.get_avail(request, node_list, request_placement)
        # 所有使用的实例剩余capacity总和
        capacity_bottleneck_index = util.get_rest_capacity(request, request_placement)

        # 可用性拉满
        while 1:
            # 如果可用性不足
            if avail_bottleneck_index > -1:
                util.add_instance(
                    bandwidth,
                    node_list,
                    instance_registry,
                    instance_num,
                    request,
                    request_placement,
                    avail_bottleneck_index,
                )
                # 计算可用性
                avail_bottleneck_index = util.get_avail(
                    request, node_list, request_placement
                )
            else:
                break

        # 剩余capacity拉满
        while 1:
            # 如果capacity不足
            if capacity_bottleneck_index > -1:
                util.add_instance(
                    bandwidth,
                    node_list,
                    instance_registry,
                    instance_num,
                    request,
                    request_placement,
                    capacity_bottleneck_index,
                )
                # 计算可用性
                capacity_bottleneck_index = util.get_rest_capacity(
                    request, request_placement
                )
            else:
                break

        """ 根据部署位置计算链的网络流 """
        flow_matrix = util.get_route(bandwidth, request, request_placement)
        flow_matrix_request[request.id] = flow_matrix
        bandwidth = (np.mat(bandwidth) - np.mat(flow_matrix)).tolist()

    """ 部署完毕 """

    return request_placement, instance_num, bandwidth, flow_matrix_request


def simulated_annealing(
    request_placement,
    instance_num,
    bandwidth,
    flow_matrix_request,
    bandwidth_origin,
    node_list,
):
    """TODO: 模拟退火"""

    old_cost = get_total_cost(request_placement)

    # 初始温度
    T0 = 100
    T = T0
    T_min = 1

    ITER_NUM = 50

    time = 0
    while T > T_min:
        time += 1

        for i in range(ITER_NUM):
            # 找新解
            new_solution = find_next_solution()
            new_cost = get_total_cost(new_solution)

            delta = new_cost - old_cost
            P = math.exp((-1 * delta) / T)
            # 如果新解有改进 or 没改进但满足Metropolis准则
            if delta < 0 or random.uniform() < P:
                # 接受新解
                pass

        T = T0 / (1 + time)

    return


def find_next_solution():
    """TODO: 实例移动到相邻几跳的满足资源约束的node"""

    new_solution = 0

    return new_solution


def get_total_cost(solution):
    """TODO: 计算放置策略的总开销"""

    # (np.mat(bandwidth_origin) - np.mat(bandwidth)).sum()

    cost = 0

    return cost


if __name__ == "__main__":
    bandwidth = [
        [0, 100, 0, 0, 100, 0, 100, 0],
        [100, 0, 100, 0, 100, 100, 0, 0],
        [0, 100, 0, 100, 100, 0, 0, 0],
        [0, 0, 100, 0, 0, 100, 0, 100],
        [100, 100, 100, 0, 0, 100, 100, 0],
        [0, 100, 0, 100, 100, 0, 100, 100],
        [100, 0, 0, 0, 100, 100, 0, 100],
        [0, 0, 0, 100, 0, 100, 100, 0],
    ]

    node_list = [
        ni.Node(0, 100, 0.9),
        ni.Node(1, 100, 0.9),
        ni.Node(2, 100, 0.9),
        ni.Node(3, 100, 0.9),
        ni.Node(4, 100, 0.9),
        ni.Node(5, 100, 0.9),
        ni.Node(6, 100, 0.8),
        ni.Node(7, 100, 0.8),
    ]

    request_list = [
        ni.Request(0, 0, 7, [1, 2, 3], 20, 0.95),
        ni.Request(1, 0, 3, [2, 3], 15, 0.9),
    ]

    # d = distance(bandwidth, 0, 3)

    # r = max_flow(bandwidth, {1: 50, 4: 50}, {3: 20, 7: 80})
    band = extend_deploy(bandwidth, node_list, request_list)
    print(band)
