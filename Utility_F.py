# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author：Lyon.Fan
File：Utility.py
Date：2021/09/24
"""
import numpy as np
import pandas as pd
import re
import itertools
import datetime
import dateutil.relativedelta
import os
from os import path

def scaner_file(p_url: str):
    """
    遍历当前路径下所有文件
    :param p_url:要扫描的目录
    :return: 文件列表
    """
    list_file = []
    file = os.listdir(p_url)
    for f in file:
        # 字符串拼接
        real_url = path.join(p_url, f)
        list_file.append(real_url)
    return list_file

def u_get_cell(str_model: str, p_str_pre: str = "【", p_str_suf: str = "】") -> list:
    """
    将模板拆解，得到要遍历的字段
    :param str_model:模板，样式如'【时间字段】近【N】月，随机分类为【随机分类】，【度量】的【计算方法】'
    :param p_str_pre:前一个分隔符，默认'【'
    :param p_str_suf:后一个分隔符，默认'】'
    :return:得到字段list，例如['【时间字段】','【】'，'【随机N分类】'，'【度量】'，'【计算方法】']
    """
    a = str_model
    tmp_list = []
    while a.find(p_str_pre) >= 0:
        p1 = a.find(p_str_pre)
        p2 = a.find(p_str_suf)
        tmp_list.append(a[p1: p2+1])
        a = a[p2+1:]
    return tmp_list

def u_get_space(c: int) -> str:
    """
    返回c个空格键，用于SQL格式化
    :param c:
    :return:
    """
    return " " * c

def u_get_dict(cond_key, cond_value,glob_dict: dict):
    """_summary_
        根据给定的条件的key和value，从g_glob_dict中查的对应的内容
    Args:
        cond_key (_type_): 条件中的key
        cond_value (_type_): 条件中的value
    result:
        a (_type_): 字段名称
        b (_type_): 字段取值
    """
    if glob_dict[cond_key]["type"] == "other":
        a = "" # 占位符
        b = glob_dict[cond_key]["values"][cond_value] # 字段名称
    elif glob_dict[cond_key]["type"] == "Dim":
        a = glob_dict[cond_key]["ename"] # 字段名称
        b = glob_dict[cond_key]["values"][cond_value] # 字段取值
    return a, b
    
def u_get_date_delta_sql(delta_type: str, base_date_col, date_col: str) -> str:
    """
    根据时间单位不同 返回不同的date_delta的SQL语句
    :param delta_type: 时间单位
    :param base_date_col: 基础日期字段名称
    :param date_col: 计算日期字段名称 也可以是固定的日期字符串，格式为8位日期字段 如：20220831
    :return:date_delta的SQL语句
    """
    str_return = ""

    if delta_type not in ["日", "月"]:
        print("时间间隔单位仅支持[‘日’,‘月’]")
        return str_return

    if delta_type == "月":
        str_return = f"         (cast(substr({base_date_col},1,4) as int)*12+cast(substr({base_date_col},5,2) as int) \n" \
                     + f"         - \n" \
                     + f"         cast(substr({date_col},1,4) as int)*12+cast(substr({date_col},5,2) as int)) \n" \
                     + f"         as date_delta "
    elif delta_type == "日":
        str_return = f"         datediff( \n"\
                     + f"         concat(substr({base_date_col},1,4)),'-',substr({base_date_col},5,2)),'-',substr({base_date_col},7,2))) \n"\
                     + f"         ,concat(substr({date_col},1,4)),'-',substr({date_col},5,2)),'-',substr({date_col},7,2))) \n"\
                     + f"         ) as date_delta "

    return str_return

def get_date_interval(p_clac_name: str, p_delta1: int, p_delta2: int=-1):
    """
    根据日期得到时间段，时间段可能是一个，也可能是两个
    普通时间段如近3个月 是一个返回值 如{0：['0','3']}
    同比、环比时间段是两个 如{0：['0','3'],1：['4','6']}
    :param p_clac_name:计算方法
    :param p_delta1:日期间隔数量
    :return:【分子时间段，分母时间段】
    """
    # 同比
    if "同比" in p_clac_name:
        return f"(0<=date_delta and date_delta < {p_delta1})", f"({12}<=date_delta and date_delta < {12 + p_delta1})"
    # 环比
    elif "环比" in p_clac_name:
        return f"(0<=date_delta and date_delta < {p_delta1})", f"({p_delta1}<=date_delta and date_delta < {2 * p_delta1})"
    # 增长率
    elif "增长率" in p_clac_name:
        return f"(0<=date_delta and date_delta < {p_delta1})", f"({p_delta1}<=date_delta and date_delta < {2 * p_delta1})"
    # 极差
    elif "极差" in p_clac_name:
        return f"(0<=date_delta and date_delta < {p_delta1})", f"((0<=date_delta and date_delta < {p_delta1})"
    elif "占比" in p_clac_name:
        return f"(0<=date_delta and date_delta < {p_delta1})", f"(0<=date_delta and date_delta < {p_delta2})"
    # 普通
    else:
        return f"(0<=date_delta and date_delta < {p_delta1})",None

def u_get_clac_string(clac_name1: str) -> str:
    # ****************************2P****************************
    # 环比
    if clac_name1 == "最大值环比" or clac_name1 == "最大值占比":
        return ",max(\n{})\n/max(\n{}) as {}"
    elif clac_name1 == "最小值环比" or clac_name1 == "最小值占比":
        return ",min(\n{})\n/min(\n{}) as {}"
    elif clac_name1 == "合计值环比" or clac_name1 == "合计值占比":
        return ",sum(\n{})\n/sum(\n{}) as {}"
    elif clac_name1 == "平均值环比" or clac_name1 == "平均值占比":
        return ",avg(\n{})\n/avg(\n{}) as {}"
    elif clac_name1 == "中位数环比" or clac_name1 == "中位数占比":
        return ",appx_median(\n{})\n/appx_median(\n{}) as {}"
    elif clac_name1 == "次数环比" or clac_name1 == "次数占比":
        return ",count(\n{})\n/count(\n{}) as {}"
    elif clac_name1 == "去重次数环比" or clac_name1 == "去重次数占比":
        return ",count(\ndistinct(\n{}))\n/count(\ndistinct(\n{})) as {}"
    # 同比
    elif clac_name1 == "最大值同比":
        return ",max(\n{})\n/max(\n{}) as {}"
    elif clac_name1 == "最小值同比":
        return ",min(\n{})\n/min(\n{}) as {}"
    elif clac_name1 == "合计值同比":
        return ",sum(\n{})\n/sum(\n{}) as {}"
    elif clac_name1 == "平均值同比":
        return ",avg(\n{})\n/avg(\n{}) as {}"
    elif clac_name1 == "中位数同比":
        return ",appx_median(\n{})\n/appx_median(\n{}) as {}"
    elif clac_name1 == "次数同比":
        return ",count(\n{})\n/count(\n{}) as {}"
    elif clac_name1 == "去重次数同比":
        return ",count(\ndistinct(\n{}))\n/count(\ndistinct(\n{})) as {}"
    # 极差
    elif clac_name1 == "极差":
        return ",max(\n{})\n-min(\n{}) as {}"
    # 增长
    if clac_name1 == "最大值增长率":
        return ",max(\n{})\n/max(\n{})-1 as {}"
    elif clac_name1 == "最小值增长率":
        return ",min(\n{})\n/min(\n{})-1 as {}"
    elif clac_name1 == "合计值增长率":
        return ",sum(\n{})\n/sum(\n{})-1 as {}"
    elif clac_name1 == "平均值增长率":
        return ",avg(\n{})\n/avg(\n{})-1 as {}"
    elif clac_name1 == "中位数增长率":
        return ",appx_median(\n{})\n/appx_median(\n{})-1 as {}"
    elif clac_name1 == "次数增长率":
        return ",count(\n{})\n/count(\n{})-1 as {}"
    elif clac_name1 == "去重次数增长率":
        return ",count(\ndistinct(\n{}))\n/count(\ndistinct(\n{}))-1 as {}"

    # ****************************1P ****************************
    elif clac_name1 == "最大值":
        return ",max(\n{}) as {}"
    elif clac_name1 == "最小值":
        return ",min(\n{}) as {}"
    elif clac_name1 == "合计值":
        return ",sum(\n{}) as {}"
    elif clac_name1 == "平均值":
        return ",avg(\n{}) as {}"
    elif clac_name1 == "中位数":
        return ",appx_median(\n{}) as {}"
    elif clac_name1 == "次数":
        return ",count(\n{}) as {}"
    elif clac_name1 == "去重次数":
        return ",count(\ndistinct({})) as {}"

    else:
        print("【{}】未实现，请检查".format(clac_name))