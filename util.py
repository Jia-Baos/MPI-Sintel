# ---------------------------------------------------------------------
# Copyright (c) 2018 TU Berlin, Communication Systems Group
# Written by Tobias Senst <senst@nue.tu-berlin.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------------------------------------------
import copy
import pickle

import cv2
import numpy as np


# passded
def create_config(parameter, filelist):
    config_list = list()
    for id, f in enumerate(filelist):
        file_list = copy.deepcopy(f)
        config_list.append({"files": file_list, "parameter": copy.deepcopy(parameter), "file_index": id})

    return config_list


# passded
def computeEE(src0, src1):
    diff_flow = src0 - src1
    res = (diff_flow[:, :, 0] * diff_flow[:, :, 0]) + (diff_flow[:, :, 1] * diff_flow[:, :, 1])
    return cv2.sqrt(res)


def computer_errors(ee_base, mask):
    # 通过mask剔除不需要统计的像素
    ee_base = ee_base * mask
    ret, R1 = cv2.threshold(src=ee_base, thresh=1, maxval=1, type=cv2.THRESH_BINARY)
    ret, R2 = cv2.threshold(src=ee_base, thresh=2, maxval=1, type=cv2.THRESH_BINARY)
    ret, R3 = cv2.threshold(src=ee_base, thresh=3, maxval=1, type=cv2.THRESH_BINARY)

    ee = cv2.sumElems(ee_base)[0]
    r1_sum = cv2.sumElems(R1)[0]
    r2_sum = cv2.sumElems(R2)[0]
    r3_sum = cv2.sumElems(R3)[0]
    no_p = cv2.sumElems(mask)[0]
    result = {"ee": ee, "R1": r1_sum, "R2": r2_sum, "R3": r3_sum, "noPoints": no_p}
    return result


def compute_error(est_flow, gt_flow, invalid_mask):
    mag_flow = cv2.sqrt(gt_flow[:, :, 0] * gt_flow[:, :, 0] + gt_flow[:, :, 1] * gt_flow[:, :, 1])
    ret, mask_to_large = cv2.threshold(src=mag_flow, thresh=900, maxval=1, type=cv2.THRESH_BINARY_INV)

    total_inp_mask = cv2.cvtColor(invalid_mask, cv2.COLOR_BGR2GRAY)
    ret, fg_mask = cv2.threshold(src=total_inp_mask, thresh=0.5, maxval=1, type=cv2.THRESH_BINARY_INV)
    ret, bg_mask = cv2.threshold(src=total_inp_mask, thresh=0.5, maxval=1, type=cv2.THRESH_BINARY)
    total_mask = cv2.bitwise_or(fg_mask, bg_mask)

    result = dict()
    ee_base = computeEE(est_flow, gt_flow)
    result["FG"] = computer_errors(ee_base, fg_mask * mask_to_large)
    result["BG"] = computer_errors(ee_base, bg_mask * mask_to_large)
    result["Total"] = computer_errors(ee_base, total_mask * mask_to_large)
    return result


def readFlowFiles(filename):
    with open(filename, 'rb') as f:
        magic = np.fromfile(f, np.float32, count=1)
        if 202021.25 != magic:
            print("Magic number incorrect. Invalid .flo file")
        else:
            w = np.fromfile(f, np.int32, count=1)[0]
            h = np.fromfile(f, np.int32, count=1)[0]
            data = np.fromfile(f, np.float32, count=2 * w * h)
            # Reshape data into 3D array (columns, rows, bands)
            data2D = np.resize(data, (h, w, 2))
    return data2D


def writeFlowFile(filename, flow):
    TAG_STRING = np.array(202021.25, dtype=np.float32)
    assert flow.shape[2] == 2
    h = np.array(flow.shape[0], dtype=np.int32)
    w = np.array(flow.shape[1], dtype=np.int32)
    with open(filename, 'wb') as f:
        f.write(TAG_STRING.tobytes())
        f.write(w.tobytes())
        f.write(h.tobytes())
        f.write(flow.tobytes())


def flow2RGB(flow, max_flow_mag=5):
    """
        Color-coded visualization of optical flow fields

        # Arguments
            flow: array of shape [:,:,2] containing optical flow
            max_flow_mag: maximal expected flow magnitude used to normalize. If max_flow_mag < 0 the maximal
            magnitude of the optical flow field will be used
    """
    hsv_mat = np.ones(shape=(flow.shape[0], flow.shape[1], 3), dtype=np.float32) * 255
    ee = cv2.sqrt(flow[:, :, 0] * flow[:, :, 0] + flow[:, :, 1] * flow[:, :, 1])
    angle = np.arccos(flow[:, :, 0] / ee)
    angle[flow[:, :, 0] == 0] = 0
    angle[flow[:, :, 1] == 0] = 6.2831853 - angle[flow[:, :, 1] == 0]
    angle = angle * 180 / 3.141
    hsv_mat[:, :, 0] = angle
    if max_flow_mag < 0:
        max_flow_mag = ee.max()
    hsv_mat[:, :, 1] = ee * 220.0 / max_flow_mag
    ret, hsv_mat[:, :, 1] = cv2.threshold(src=hsv_mat[:, :, 1], maxval=255, thresh=255, type=cv2.THRESH_TRUNC)
    rgb_mat = cv2.cvtColor(hsv_mat.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return rgb_mat


def drawFlowField(filename, flow):
    cv2.imwrite(filename=filename, img=flow2RGB(flow))


def parameter_to_string(parameter_dict):
    """
    将计算光流所使用的方法全部取出生成字符串
    :param parameter_dict: parameter_dict
    :return: out_str
    """
    out_str = str()
    for key in sorted(parameter_dict.keys()):
        try:
            str_value = str(parameter_dict[key])
        except TypeError:
            str_value = parameter_dict[key]

        out_str = out_str + str_value + "_"
    return out_str


def get_sequence_measures(result_list):
    """
    提取计算光流所使用方法的结果
    :param result_list: parameter_str: 计算光流所使用的方法; seq_name: 存放连续帧图片的文件夹
    :return: sequence_list
    """
    sequence_list = dict()
    for item in result_list:
        parameter_str = parameter_to_string(item[0]["parameter"])
        if "dir" in item[0]["files"]:
            seq_name = item[0]["files"]["dir"]
        else:
            seq_name = "None"

        if seq_name.find("_dyn") >= 0:
            continue

        if parameter_str not in sequence_list:
            sequence_list[parameter_str] = dict()

        if seq_name not in sequence_list[parameter_str]:
            sequence_list[parameter_str][seq_name] = list()

        sequence_list[parameter_str][seq_name].append(item[1])

    return sequence_list


def avg_sequence(src):
    sequence_result = dict()
    for seq_keys in src.keys():
        result = dict()
        for item in src[seq_keys]:
            for key in item.keys():
                if key != "FG" and key != "BG" and key != "Total":
                    continue
                if key not in result:
                    result[key] = item[key]
                else:
                    for key1 in item[key].keys():
                        result[key][key1] += item[key][key1]

        for key in result.keys():
            result[key]["ee"] = result[key]["ee"] / result[key]["noPoints"]
            result[key]["R1"] = result[key]["R1"] / result[key]["noPoints"]
            result[key]["R2"] = result[key]["R2"] / result[key]["noPoints"]
            result[key]["R3"] = result[key]["R3"] / result[key]["noPoints"]
        sequence_result[seq_keys] = copy.deepcopy(result)
    return sequence_result


def avg_sequences(sequence_list, use_type):
    res_FG_ee = []
    res_FG_R2 = []
    res_BG_ee = []
    res_BG_R2 = []
    res_total_ee = []
    res_total_R2 = []
    for seq_name in sequence_list.keys():
        if use_type == 1 and seq_name.find("_hDyn") == -1:
            continue
        if use_type == 0 and seq_name.find("_hDyn") >= 0:
            continue
        res_FG_ee.append(sequence_list[seq_name]["FG"]["ee"])
        res_FG_R2.append(sequence_list[seq_name]["FG"]["R2"])
        res_BG_ee.append(sequence_list[seq_name]["BG"]["ee"])
        res_BG_R2.append(sequence_list[seq_name]["BG"]["R2"])
        res_total_ee.append(sequence_list[seq_name]["Total"]["ee"])
        res_total_R2.append(sequence_list[seq_name]["Total"]["R2"])

    return np.mean(res_FG_ee), 100 * np.mean(res_FG_R2), \
        np.mean(res_BG_ee), 100 * np.mean(res_BG_R2), \
        np.mean(res_total_ee), 100 * np.mean(res_total_R2)


def getLatexTable(filename):
    data = pickle.load(open(filename, "rb"))

    str_result = "\\begin{table} \n \\centering " \
                 "\\begin{tabular}{l|crcr|crcr|crcrcr|r} \n" \
                 "\\hline \n " \
                 "\\multicolumn{1}{c|}{} & \\multicolumn{2}{|c}{FG (Static) } & \\multicolumn{2}{c|} { BG (Static)} & " \
                 "\\multicolumn{2}{|c}{FG (Dynamic)} & \\multicolumn{2}{c|}{ BG (Dynamic)} & " \
                 "\\multicolumn{2}{c}{FG($\\varnothing$)}&\multicolumn{2}{c}{BG ($\\varnothing$)} & " \
                 "\\multicolumn{2}{c|}{$\\varnothing$}  \\\\ \n " \
                 "\\multicolumn{1}{c|}{}& EPE & R2[\\%] & EPE & R2[\\%]& EPE & R2[\\%]& EPE & R2[\\%]" \
                 "& EPE & R2[\\%]& EPE & R2[\\%]& EPE & R2[\\%] \\\\ \n "
    result_list = data["result"]
    method_result_list = get_sequence_measures(result_list)
    for method_key in method_result_list.keys():
        sequence_result = avg_sequence(method_result_list[method_key])
        # print(sequence_result)
        ret_static = avg_sequences(sequence_result, 0)
        ret_dynamic = avg_sequences(sequence_result, 1)
        ret_total = avg_sequences(sequence_result, 2)
        name = method_key.replace("/", "")
        name = name.replace("_", "")
        str_out = method_key \
                  + " & {:.3f}".format(ret_static[0]) \
                  + " & {:.2f}".format(ret_static[1]) \
                  + " & {:.3f}".format(ret_static[2]) \
                  + " & {:.2f}".format(ret_static[3]) \
                  + " & {:.3f}".format(ret_dynamic[0]) \
                  + " & {:.2f}".format(ret_dynamic[1]) \
                  + " & {:.3f}".format(ret_dynamic[2]) \
                  + " & {:.2f}".format(ret_dynamic[3]) \
                  + " & {:.3f}".format(ret_total[0]) \
                  + " & {:.3f}".format(ret_total[1]) \
                  + " & {:.3f}".format(ret_total[2]) \
                  + " & {:.2f}".format(ret_total[3]) \
                  + " & {:.3f}".format(ret_total[4]) \
                  + " & {:.2f}".format(ret_total[5]) \
                  + " \\\ "
        str_result = str_result + str_out + "\n"

    str_result = str_result + "\end{tabular} \n " \
                              "\\vspace{0.1cm} \n" \
                              "\\caption{Evaluation results common optical flow metrics. " \
                              "Dynamic comprised sequences with and static without camera motion, " \
                              "BG - background motion vectors and FG - motion vectors located at persons of the crowd.} \n" \
                              "\\end{table}"
    return str_result


def avg_measures(src):
    total_result = dict()
    for seq_keys in src.keys():
        result = dict()
        for item in src[seq_keys]:
            for key in item.keys():
                if key == "time":
                    continue
                if key not in result:
                    result[key] = item[key]
                else:
                    for key1 in item[key].keys():
                        result[key][key1] += int(item[key][key1])

        for key in result.keys():
            result[key]["ee"] = result[key]["ee"] / result[key]["noPoints"]
            result[key]["R1"] = result[key]["R1"] / result[key]["noPoints"]
            result[key]["R2"] = result[key]["R2"] / result[key]["noPoints"]
            result[key]["R3"] = result[key]["R3"] / result[key]["noPoints"]

        if len(total_result) == 0:
            for key in result.keys():
                total_result[key] = dict()
                total_result[key]["ee"] = result[key]["ee"] / len(src)
                total_result[key]["R1"] = result[key]["R1"] / len(src)
                total_result[key]["R2"] = result[key]["R2"] / len(src)
                total_result[key]["R3"] = result[key]["R3"] / len(src)
        else:
            for key in result.keys():
                total_result[key]["ee"] += result[key]["ee"] / len(src)
                total_result[key]["R1"] += result[key]["R1"] / len(src)
                total_result[key]["R2"] += result[key]["R2"] / len(src)
                total_result[key]["R3"] += result[key]["R3"] / len(src)
    return total_result


def avg_measures_no_dict(src):
    total_result = dict()
    for seq_keys in src.keys():
        result = dict()
        for item in src[seq_keys]:
            for key in item.keys():
                if key not in result:
                    result[key] = item[key]
                else:
                    result[key] += item[key]

        result["ee"] = result["ee"] / result["no_points"]
        result["R1"] = result["R1"] / result["no_points"]
        result["R2"] = result["R2"] / result["no_points"]
        result["R3"] = result["R3"] / result["no_points"]

        if len(total_result) == 0:
            for key in result.keys():
                total_result = dict()
                total_result["ee"] = result["ee"] / len(src)
                total_result["R1"] = result["R1"] / len(src)
                total_result["R2"] = result["R2"] / len(src)
                total_result["R3"] = result["R3"] / len(src)
        else:
            for key in result.keys():
                total_result["ee"] += result["ee"] / len(src)
                total_result["R1"] += result["R1"] / len(src)
                total_result["R2"] += result["R2"] / len(src)
                total_result["R3"] += result["R3"] / len(src)
    return total_result
