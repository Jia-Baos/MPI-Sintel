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
import glob
import os


class BaseParser:
    """
    Base class
    """

    def __init__(self):
        self.filenames_dict = list()


class MyParser(BaseParser):
    """
    Derived class
    """

    def __init__(self):
        BaseParser.__init__(self)

    def parsefilenames(self, basepaths):
        self.filenames_dict = []
        for dirpath, dirnames, filenames in os.walk(basepaths["images"]):
            for dirs in dirnames:
                image_paths = glob.glob(r"{}/*.png".format(dirpath + dirs))
                image_paths = sorted(image_paths)  # assume filenames are sortable

                # 将路径中的双反斜杠转化为单正斜杠
                for index, value in enumerate(image_paths):
                    image_paths[index] = value.replace("\\", "/")
                iterable_curr = image_paths[1:]  # 获取连续的两帧，计算光流也是如此
                iterable_pre = image_paths[:len(image_paths) - 1]
                image_pairs = list(zip(iterable_pre, iterable_curr))

                for image_pair in image_pairs:
                    filename_dict = dict()
                    filename_dict["prevImg"] = image_pair[0]
                    filename_dict["currImg"] = image_pair[1]
                    filename_base = os.path.relpath(filename_dict["prevImg"], dirpath + dirs)  # 获取相对路径
                    filename_base = os.path.splitext(filename_base)[0]  # 分离文件名与扩展名

                    if "gt_flow" in basepaths:
                        filename_dict["gt_flow"] = basepaths["gt_flow"] + dirs + "/" + filename_base + ".flo"
                    if "estimate" in basepaths:
                        filename_dict["estflow"] = basepaths["estimate"] + dirs + "/" + filename_base + ".flo"
                    if "masks" in basepaths:
                        filename_dict["mask"] = basepaths["masks"] + dirs + "/" + filename_base + ".png"

                    filename_dict["dir"] = dirs  # 连续多帧图像所在的文件夹
                    filename_dict["filename"] = filename_base  # 当前两帧所对应光流文件的名称
                    filename_dict["basepath"] = basepaths["basepath"]
                    filename_dict["estimatepath"] = basepaths["estimate"] + dirs + "/"
                    self.filenames_dict.append(filename_dict)


def create_filename_list(basepath):
    """
    Create a list of dictionaries containing file-paths for the optical flow dataset
    :param basepath: basepath: a dictionary containing sub path.
    :return: filenames_dict
    filename_dict[0]:
        preImg: 'D:/PythonProject/MPI-Sintel/MPI-Sintel/training/clean/alley_1/frame_0001.png'
        currImg: 'D:/PythonProject/MPI-Sintel/MPI-Sintel/training/clean/alley_1/frame_0002.png'
        gt_flow: 'D:/PythonProject/MPI-Sintel/MPI-Sintel/training/flow/alley_1/frame_0001.flo'
        estflow: 'D:/PythonProject/MPI-Sintel/MPI-Sintel/estimate/ACPM/alley_1/frame_0001.flo'
        mask: 'D:/PythonProject/MPI-Sintel/MPI-Sintel/training/occlusions/alley_1/frame_0001.png'
        dir: 'alley_1'
        filename: 'frame_0001'
        basepath: 'D:/PythonProject/MPI-Sintel/MPI-Sintel/training/'
        estimatepath 'D:/PythonProject/MPI-Sintel/MPI-Sintel/estimate/ACPM/alley_1/'
    """
    fileparser = MyParser()
    fileparser.parsefilenames(basepath)
    return fileparser.filenames_dict
