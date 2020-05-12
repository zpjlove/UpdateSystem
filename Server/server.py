# -*- coding: utf-8 -*-
# @Time    : 2019/5/12
# @Author  : zhangpengjie
# @File    : AutoCheckVersion.py
# @Software: PyCharm
# @Function: 实现客户端自动更新（服务端）
import os
import sys
import time
import configparser
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from pprint import pprint


# 处理xml的类
class VersionInfoXml:
    def __init__(self, xml_path, server_info=None, module_list=None):
        self.xml_path = xml_path
        if server_info is not None:
            if module_list is None:
                module_list = ["ClientVersion"]
            self.create_new_xml(server_info, module_list)
        self.tree = ET.parse(self.xml_path)
        self.root = self.tree.getroot()

    def create_new_xml(self, server_info, module_info):
        root = ET.Element("versionInfo")
        ServerInfo = ET.SubElement(root, "ServerInfo")
        ET.SubElement(ServerInfo, "ServerIp").text = server_info[0]
        ET.SubElement(ServerInfo, "ServerPort").text = server_info[1]
        ET.SubElement(ServerInfo, "XmlLocalPath").text = server_info[2]
        for each_module in module_info:
            ET.SubElement(root, each_module).set("Version", "0")
        self.save_change(root)
        print("I created a new temp xml!")

    def save_change(self, root=None):
        if root is None:
            root = self.root
        rough_bytes = ET.tostring(root, "utf-8")
        rough_string = str(rough_bytes, encoding="utf-8").replace("\n", "").replace("\t", "").replace("    ", "")
        content = minidom.parseString(rough_string)
        with open(self.xml_path, 'w+') as fs:
            content.writexml(fs, indent="", addindent="\t", newl="\n", encoding="utf-8")
        return True

    def changeServerInfo(self, name, value):
        if type(value) is int:
            value = str(value)
        Xpath = "ServerInfo/%s" % name
        element = self.root.find(Xpath)
        if element is not None:
            element.text = value
            # self.save_change()
        else:
            print("I can't find \"ServerInfo/%s\" in xml!" % name)

    def addObject(self, module_name, file_path, file_size, last_update_time, version):
        moduleVersion = self.root.find(module_name)
        object = ET.SubElement(moduleVersion, "object")
        ET.SubElement(object, "FileRelativePath").text = str(file_path)
        ET.SubElement(object, "FileSize").text = str(file_size)
        ET.SubElement(object, "LastUpdateTime").text = str(last_update_time)
        ET.SubElement(object, "Version").text = str(version)
        # self.save_change()

    def deleteObject(self, module_name, file_name):
        Xpath = "%s/object" % module_name
        objects = self.root.findall(Xpath)
        moudleVersion = self.root.find(module_name)
        for element in objects:
            if element.find('FileRelativePath').text == file_name:
                moudleVersion.remove(element)
                # self.save_change()
                print("Delete object: %s" % file_name)
                break
        else:
            print("I can't find \"%s\" in xml!" % file_name)

    def updateObject(self, module_name, file_name, version):
        if type(version) is int:
            version = str(version)
        Xpath = "%s/object" % module_name
        objects = self.root.findall(Xpath)
        for element in objects:
            if element.find('FileRelativePath').text == file_name:
                element.find('Version').text = version
                # self.save_change()
                # print("Update \"%s\" version: %s" % (file_name, version))
                break
        else:
            print("I can't find \"%s\" in xml!" % file_name)

    def updateAttribute(self, module_name, version):
        if type(version) is int:
            version = str(version)
        moduleVersion = self.root.find(module_name)
        moduleVersion.set("Version", version)
        # self.save_change()

    def getObjects(self, module_name):
        list_element = []
        Xpath = "%s/object" % module_name
        objects = self.root.findall(Xpath)
        for element in objects:
            dict_element = {}
            for key, value in enumerate(element):
                dict_element[value.tag] = value.text
            list_element.append(dict_element)
        return list_element

    def addModule(self, module):
        self.root.append(module)
        # self.save_change()

    def deleteModule(self, module_name):
        module = self.root.find(module_name)
        if module is not None:
            self.root.remove(module)
            # self.save_change()

    def getModules(self):
        dict_element = {}
        objects = list(self.root)
        for key, value in enumerate(objects):
            dict_element[value.tag] = value.attrib.get("Version")
        del dict_element["ServerInfo"]
        return dict_element

    def getAttribute(self, module_name):
        moduleVersion = self.root.find(module_name)
        return moduleVersion.get("Version")

    def get_node_value(self, path):
        '''查找某个路径匹配的第一个节点
           tree: xml树
           path: 节点路径'''
        node = self.tree.find(path)
        if node == None:
            return None
        return node.text


def AutoCheckVersion(old_xml_path, new_xml_path):
    '''
    比较两个xml的objects节点，分析出增加，更改，和删除的文件列表，并在新xml里更新版本号
    :param old_xml: 旧xml的完整路径
    :param new_xml: 新xml的完整路径
    :return: len(add_list), len(delete_list), len(change_list),
    :return: add_list: [filname1, filname2], delete_list: [filname1, filname2] change_list: [filname1, filname2]
    '''
    print("Analyze the xml files and update the version number ...")
    old_xml = VersionInfoXml(old_xml_path)
    new_xml = VersionInfoXml(new_xml_path)
    # 先分析模块的增、删、改
    old_modules = list(old_xml.getModules().keys())
    new_modules = list(new_xml.getModules().keys())
    add_modules_list = list(set(new_modules).difference(set(old_modules)))
    for module_name in add_modules_list:
        ET.SubElement(old_xml.root, module_name).set("Version", 0)
    common_modules_list = [item for item in old_modules if item in new_modules]
    # 分析每个的模块中的每个文件的增、删、改
    total_add_list = []
    total_delete_list = []
    total_change_list = []
    common_modules_list.extend(add_modules_list)
    for module_name in common_modules_list:
        old_xml_objects = old_xml.getObjects(module_name)
        new_xml_objects = new_xml.getObjects(module_name)
        old_xml_objects_dict = {file_info["FileRelativePath"]: file_info for file_info in old_xml_objects}
        new_xml_objects_dict = {file_info["FileRelativePath"]: file_info for file_info in new_xml_objects}
        old_data_list = set(old_xml_objects_dict.keys())
        new_data_list = set(new_xml_objects_dict.keys())
        add_list = list(new_data_list.difference(old_data_list))
        delete_list = list(old_data_list.difference(new_data_list))
        common_list = list(old_data_list.intersection(new_data_list))
        change_list = []
        # 更新每个文件的版本号信息
        for file_name in common_list:
            new_version = int(old_xml_objects_dict[file_name]["Version"])
            update = TimeFormatComp(new_xml_objects_dict[file_name]["LastUpdateTime"],
                                    old_xml_objects_dict[file_name]["LastUpdateTime"])
            if update is True:
                change_list.append(file_name)
                new_version += 1
            new_xml.updateObject(module_name, file_name, new_version)
        # 更新模块版本信息
        new_module_version = int(old_xml.getAttribute(module_name))
        if len(add_list) or len(delete_list) or len(change_list):
            new_module_version = new_module_version + 1
        new_xml.updateAttribute(module_name, new_module_version)

        total_add_list.extend(add_list)
        total_delete_list.extend(delete_list)
        total_change_list.extend(change_list)

    # 保存到文件
    new_xml.save_change()
    print("Analysis update info done. Save the new xml ...")
    # 结果提示
    if len(total_add_list) or len(total_delete_list) or len(total_change_list):
        # 替换旧的xml文件
        os.remove(old_xml_path)
        os.rename(new_xml_path, old_xml_path)
        print("Done. add: %d, delete: %d, update: %d. The new client version: %s." % (
            len(total_add_list), len(total_delete_list), len(total_change_list), str(new_xml.getModules())))
    else:
        os.remove(new_xml_path)
        print("No file changed! The current client version: %s." % (str(new_xml.getModules())))
    return len(total_add_list), len(total_delete_list), len(total_change_list)


def CreateNewXmlFromFiles(client_dir):
    '''
    遍历文件夹所有文件，生成标准xml
    :param client_dir: 要遍历的文件夹路径
    :return: 生成的xml的完整路径
    '''
    print("Scan the folder and create the temp xml file ...")
    server_info = [UPDATE_HOST, UPDATE_PORT, "default"]
    module_list = os.listdir(client_dir)
    new_xml = VersionInfoXml("VersionInfoTemp.xml", server_info, module_list)
    for module_name in module_list:
        module_dir = os.path.join(client_dir, module_name)
        for (dirpath, dirnames, filenames) in os.walk(module_dir):
            for file in filenames:
                file_dir = os.path.join(dirpath, file)
                file_path = file_dir.replace(client_dir, "").strip("\\").replace("\\", "/")
                file_size = os.path.getsize(file_dir)
                last_update_time = TimeStampFormat(os.path.getmtime(file_dir))
                version = 1
                new_xml.addObject(module_name, file_path, file_size, last_update_time, version)
    new_xml.save_change()
    new_xml_path = os.path.join(sys.path[0], "VersionInfoTemp.xml")
    return new_xml_path


# 时间格式标准化
def TimeStampFormat(timestamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))


# 标准格式时间比较大小
def TimeFormatComp(timestamp1, timestamp2):
    timestamp1 = time.mktime(time.strptime(timestamp1, '%Y-%m-%d %H:%M:%S'))
    timestamp2 = time.mktime(time.strptime(timestamp2, '%Y-%m-%d %H:%M:%S'))
    if timestamp1 > timestamp2:
        return True
    else:
        return False


if __name__ == "__main__":
    current_dir = sys.path[0]
    client_path = os.path.join(current_dir, "ClientFolder")  # 发布文件的路径
    ini_path = os.path.join(current_dir, "cfg.ini")  # 用于配置使用的ip地址和端口号
    config_parser = configparser.ConfigParser()
    config_parser.read(ini_path)
    UPDATE_HOST = config_parser.get("server_info", 'host')
    UPDATE_PORT = config_parser.get("server_info", 'port')

    if not os.listdir(client_path):
        print("The file path 'ClientFolder' is empty!")
    else:
        update_xml_path = os.path.join(current_dir, "VersionInfo.xml")  # 当前文件信息的xml
        temp_xml_path = CreateNewXmlFromFiles(client_path)
        AutoCheckVersion(update_xml_path, temp_xml_path)
        py_path = os.path.join(sys.path[0], 'venv', 'Scripts', 'python.exe')
        cmdline = '%s -m http.server -b %s %s' % (py_path, UPDATE_HOST, UPDATE_PORT)
        os.system(cmdline)
