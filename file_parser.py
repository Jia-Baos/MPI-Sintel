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


# passded
class MyParser(BaseParser):
    """
    Derived class
    """
    def __init__(self):
        BaseParser.__init__(self)

    def parsefilenames(self, basepaths):
        """
        Traverse the base path to get list of image and flow
        :param basepaths: basepaths
        :return: file list
        """
        self.filenames_dict = []
        for dirpath, dirnames, filenames in os.walk(basepaths["images"]):
            for dirs in dirnames:
                image_paths = glob.glob(r"{}/*.png".format(dirpath + dirs))
                image_paths = sorted(image_paths)  # assume filenames are sortable
                for index, value in enumerate(image_paths):
                    image_paths[index] = value.replace("\\", "/")

                iterable_curr = image_paths[1:]
                iterable_pre = image_paths[:len(image_paths) - 1]
                image_pairs = list(zip(iterable_pre, iterable_curr))
                for image_pair in image_pairs:
                    filename_dict = dict()
                    filename_dict["prevImg"] = image_pair[0]
                    filename_dict["currImg"] = image_pair[1]
                    filename_base = os.path.relpath(filename_dict["prevImg"], dirpath + dirs)  # 计算相对路径
                    filename_base = os.path.splitext(filename_base)[0]  # 分离文件名与扩展名

                    if "gt_flow" in basepaths:
                        filename_dict["gt_flow"] = basepaths["gt_flow"] + dirs + "/" + filename_base + ".flo"
                    if "masks" in basepaths:
                        filename_dict["mask"] = basepaths["masks"] + dirs + "/" + filename_base + ".png"
                    if "estimate" in basepaths:
                        filename_dict["estflow"] = basepaths["estimate"] + dirs + "/" + filename_base + ".flo"

                    filename_dict["dir"] = dirs
                    filename_dict["filename"] = filename_base
                    filename_dict["basepath"] = basepaths["basepath"]
                    filename_dict["estimatepath"] = basepaths["estimate"] + dirs + "/"
                    self.filenames_dict.append(filename_dict)


# passded
def create_filename_list(basepath):
    """
        brief Create a list of dictionaries containing file-paths for the optical flow dataset

        # Arguments
            basepath: a dictionary containing sub path.
    """
    fileparser = MyParser()
    fileparser.parsefilenames(basepath)
    return fileparser.filenames_dict
