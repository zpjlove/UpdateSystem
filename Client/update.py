# -*- coding: utf-8 -*-
# @Time    : 2019/5/12
# @Author  : zhangpengjie
# @File    : AutoUpdate.py
# @Software: PyCharm
# @Function: 实现客户端自动更新（客户端）
import os
import sys
import time
import getopt
import requests
import shutil
import zipfile
import tkinter
from tkinter import messagebox, ttk
from contextlib import closing
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


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

    def getModules(self):
        dict_element = {}
        objects = self.root.getchildren()
        for key, value in enumerate(objects):
            dict_element[value.tag] = value.attrib.get("Version")
        del dict_element["ServerInfo"]
        return dict_element

    def addModule(self, module):
        self.root.append(module)
        # self.save_change()

    def deleteModule(self, module_name):
        module = self.root.find(module_name)
        if module is not None:
            self.root.remove(module)
            # self.save_change()

    def getAttribute(self, module_name):
        moduleVersion = self.root.find(module_name)
        if moduleVersion is None:
            return None
        return moduleVersion.get("Version")

    def updateAttribute(self, module_name, version):
        if type(version) is int:
            version = str(version)
        moduleVersion = self.root.find(module_name)
        moduleVersion.set("Version", version)
        # self.save_change()

    def get_node_value(self, path):
        """
        查找某个路径匹配的第一个节点
        tree: xml树
        path: 节点路径
        """
        node = self.tree.find(path)
        if node == None:
            return None
        return node.text


# 手动更新时，检查更新
def CheckUpdate(server_ip, server_port, module_name, order):
    update_flag = tkinter.messagebox.askokcancel('客户端自动升级检测', '检测到客户端更新，是否立即开始更新？')
    print(update_flag)
    print(server_ip, server_port, module_name, order)
    if update_flag == True:
        AutoUpdate(server_ip, server_port, module_name, order)
    else:
        root.destroy()
        return


# 主要函数
def AutoUpdate(server_ip, server_port, module_name, order):
    time_start = time.perf_counter()
    try:
        download_url = "http://{0}:{1}/{2}".format(server_ip, server_port, "VersionInfo.xml")
        local_path = os.path.join(sys.path[0], "VersionInfoTemp.xml")
        print("download_url: " + download_url)
        if not download_file_by_http(download_url, local_path):
            raise Exception()
    except Exception as e:
        # tkinter.messagebox.showerror("更新无法继续", "获取最新版本列表文件出现异常！")
        print("Update error: Can't get the latest VersionInfo xml!")
        # root.destroy()
        return False
    root.update()
    root.deiconify()
    # 比较文件变化
    add_dict, delete_list = analyze_update_info(local_xml_path, update_xml_path, module_name)
    if add_dict == {} and delete_list == []:
        os.remove(update_xml_path)
        # tkinter.messagebox.showinfo("更新无法继续", "当前客户端已经是最新版本！")
        print("No file changed!")
        return False
    # 下载需要更新的文件
    download_progress(add_dict)
    # 文件覆盖到主目录
    prompt_info11.set("正在解压...")
    prompt_info13.set("总体进度：99.9%")
    prompt_info21.set("")
    root.update()
    source_dir = os.path.join(sys.path[0], "TempFolder")
    dest_dir = os.path.dirname(sys.path[0])
    # dest_dir = os.path.join(sys.path[0], "test_main")
    override_dir(source_dir, dest_dir)
    # 删除要删除的文件
    for file in delete_list:
        delete_dir(os.path.join(dest_dir, file))
    # 更新xml文件
    if module_name == "all_module":
        os.remove(local_xml_path)
        os.rename(update_xml_path, local_xml_path)
    else:
        update_xml(local_xml_path, update_xml_path, module_name)
    # 客户端更新结束
    time_end = time.perf_counter()
    print("更新耗时：%ds" % (time_end - time_start))
    prompt_info11.set("更新完毕。")
    prompt_info13.set("总体进度：100.0%")
    root.update()
    # tkinter.messagebox.showinfo("更新完成", "更新完毕，耗时：%ds" % (time_end - time_start))
    return True


# 分析两个xml文件
def analyze_update_info(local_xml, update_xml, module_name):
    '''
    分析本地xml文件和最新xml文件获得增加的文件和要删除的文件
    :param local_xml: 本地xml文件路径
    :param update_xml: 下载的最新xml文件路径
    :return: download_info: {filename1: fizesize1, filename2: fizesize2}, delete_list: [filname1, filname2]
    '''
    print("Analyze the xml files and check the version number ...")
    old_xml = VersionInfoXml(local_xml)
    new_xml = VersionInfoXml(update_xml)
    module_names = []
    if module_name == "all_module":
        module_names = new_xml.getModules()
    else:
        module_names.append(module_name)
    download_info_total = {}
    delete_list_total = []
    for module_name in module_names:
        print(new_xml.getAttribute(module_name))
        print(old_xml.getAttribute(module_name))
        if old_xml.getAttribute(module_name) is None:
            ET.SubElement(old_xml.root, module_name).set("Version", "0")
        if new_xml.getAttribute(module_name) <= old_xml.getAttribute(module_name):
            continue
        old_xml_objects = old_xml.getObjects(module_name)
        new_xml_objects = new_xml.getObjects(module_name)
        old_xml_objects_dict = {file_info["FileRelativePath"]: file_info for file_info in old_xml_objects}
        new_xml_objects_dict = {file_info["FileRelativePath"]: file_info for file_info in new_xml_objects}
        old_data_list = set(old_xml_objects_dict.keys())
        new_data_list = set(new_xml_objects_dict.keys())
        add_list = list(new_data_list.difference(old_data_list))
        delete_list = list(old_data_list.difference(new_data_list))
        common_list = list(old_data_list.intersection(new_data_list))

        download_info = {file_name: new_xml_objects_dict[file_name]["FileSize"] for file_name in add_list}
        # 根据每个文件的版本号，确定是否需要更新
        for file_name in common_list:
            if int(new_xml_objects_dict[file_name]["Version"]) > int(old_xml_objects_dict[file_name]["Version"]):
                download_info.update({file_name: new_xml_objects_dict[file_name]["FileSize"]})

        download_info_total.update(download_info)
        delete_list_total.extend(delete_list)
    # return download_info, delete_list
    return download_info_total, delete_list_total


# 下载需要更新的文件
def download_progress(file_info_dict):
    if file_info_dict is None:
        return None
    try:
        # update_path = local_xml.get_node_value("ServerInfo/XmlLocalPath")
        file_total_count = len(file_info_dict)
        file_count = 0
        for each_file in file_info_dict.keys():
            file_count += 1
            download_url = "http://{0}:{1}/ClientFolder/{2}".format(server_ip, server_port, each_file)
            local_path = os.path.join(sys.path[0], "TempFolder", each_file.replace("/", "\\"))
            file_path = os.sep.join(local_path.split("\\")[:-1])
            file_name = each_file
            if len(file_name) > 26:
                file_name = "..." + file_name[-26:]
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            with closing(requests.get(download_url, stream=True)) as response:
                chunk_size = 1024 * 1024  # 单次请求最大值
                content_size = int(file_info_dict[each_file])  # int(response.headers['content-length'])  # 内容体总大小
                data_count = 0
                with open(local_path, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        data_count = data_count + len(data)
                        prompt_info11.set("下载文件：(%d/%d)" % (file_count, file_total_count))
                        prompt_info12.set("下载进度：{:.1%} ".format(data_count / content_size))
                        prompt_info21.set("%s" % file_name)
                        message_progress_bar1["value"] = int(data_count * 1000 / content_size)
                        root.update()
            prompt_info13.set("总体进度：{:.1%} ".format(file_count / file_total_count))
            message_progress_bar2["value"] = int(file_count * 1000 / file_total_count)
    except Exception as e:
        # root.destroy()
        print(e)
        print("更新已终止！")
    return True


# 拷贝文件到主目录，并清空临时文件夹
def override_dir(source_dir, dest_dir):
    for each_path in os.listdir(source_dir):
        source_path = os.path.join(source_dir, each_path)
        dest_path = os.path.join(dest_dir, each_path)
        if each_path == "ClientVersion":
            dest_path = os.path.dirname(dest_path)
        if zipfile.is_zipfile(source_path):
            unpack_module(source_path, dest_dir)
        else:
            copy_dir(source_path, dest_path)
    clear_dir(source_dir)


# 下载
def download_file_by_http(down_load_url, dest_file_path):
    r = requests.get(down_load_url, timeout=10, params=None)
    print(r.status_code)
    try:
        with open(dest_file_path, "wb") as code:
            code.write(r.content)
        if r.status_code == 200:
            ret = True
        else:
            ret = False
        r.close()
        return ret
    except:
        r.close()
        return False


# 解压
def unpack_module(zip_src, dst_dir):
    print("Unpacking module: %s..." % zip_src)
    res = zipfile.is_zipfile(zip_src)
    if res:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
        fz.close()


# 拷贝
def copy_dir(source_dir, dest_dir):
    print("Copying dir: %s..." % source_dir)
    if os.path.isfile(source_dir):
        shutil.copy(source_dir, dest_dir)
    else:
        try:
            shutil.copytree(source_dir, dest_dir)
        except FileExistsError:
            for each_path in os.listdir(source_dir):
                source_path = os.path.join(source_dir, each_path)
                dest_path = os.path.join(dest_dir, each_path)
                copy_dir(source_path, dest_path)


# 删除
def delete_dir(file_path):
    print("Deleting dir: %s..." % file_path)
    if not os.path.exists(file_path):
        return None
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        shutil.rmtree(file_path)
    return True


# 清空目录
def clear_dir(file_path):
    print("Clearing folder: %s..." % file_path)
    if not os.path.exists(file_path):
        return None
    for each_path in os.listdir(file_path):
        delete_dir(os.path.join(file_path, each_path))
    return True


# 更新xml文件
def update_xml(local_xml_path, update_xml_path, module_name):
    old_xml = VersionInfoXml(local_xml_path)
    new_xml = VersionInfoXml(update_xml_path)
    new_server_module = new_xml.root.find("ServerInfo")
    new_module = new_xml.root.find(module_name)
    old_xml.deleteModule("ServerInfo")
    old_xml.addModule(new_server_module)
    old_xml.deleteModule(module_name)
    old_xml.addModule(new_module)
    old_xml.save_change()
    os.remove(update_xml_path)


# 重启客户端
def restart_client():
    # if int(client_pid) != 0:
    #     cmdline = "taskkill /T /F /PID %d" % int(client_pid)
    #     os.system(cmdline)
    #     # print('%d is kill.' % int(client_pid))
    # cmdline = os.path.join(os.path.dirname(sys.path[0]), "startMqttClient.bat")
    # os.system(cmdline)
    print('Client restart.')


if __name__ == '__main__':
    # region 主窗口界面显示部分
    root = tkinter.Tk()
    # 窗体大小和默认居中
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    ww = sw / 4
    wh = sh / 6
    root.geometry("%dx%d+%d+%d" % (ww, wh, (sw - ww) / 2, (sh - wh) / 3))
    root.title('客户端自动升级')  # 标题
    root.resizable(False, False)  # 固定窗体

    # 使用Frame增加一层容器
    frame = tkinter.Frame(root)
    # region 使用Frame在frame内部增加一层容器，第一列
    frame1 = tkinter.Frame(frame)
    # “下载文件”第1列第1行
    prompt_info11 = tkinter.StringVar(value="下载文件：(0/0)")
    message_label11 = tkinter.Label(frame1, textvariable=prompt_info11)
    message_label11.pack(side=tkinter.TOP, anchor=tkinter.W, pady=5)
    # “下载进度”第1列第2行
    prompt_info12 = tkinter.StringVar(value="下载进度：  ")
    message_label12 = tkinter.Label(frame1, textvariable=prompt_info12)
    message_label12.pack(side=tkinter.TOP, anchor=tkinter.W, pady=5)
    # “总体进度”第1列第3行
    prompt_info13 = tkinter.StringVar(value="总体进度：  ")
    message_label13 = tkinter.Label(frame1, textvariable=prompt_info13)
    message_label13.pack(side=tkinter.TOP, anchor=tkinter.W, pady=5)
    frame1.pack(side=tkinter.LEFT, anchor=tkinter.W, padx=2)
    # endregion
    # region 使用Frame在frame内部增加一层容器，第二列
    frame2 = tkinter.Frame(frame)
    # 文件名字
    prompt_info21 = tkinter.StringVar(value="")
    message_label21 = tkinter.Label(frame2, textvariable=prompt_info21)
    message_label21.pack(side=tkinter.TOP, anchor=tkinter.W, pady=5)
    # “下载进度”进度条
    message_progress_bar1 = ttk.Progressbar(frame2, orient="horizontal", length=200, mode="determinate")
    message_progress_bar1.pack(side=tkinter.TOP, anchor=tkinter.W, pady=5)
    message_progress_bar1["maximum"] = 1000
    message_progress_bar1["value"] = 0
    # “总体进度”进度条
    message_progress_bar2 = ttk.Progressbar(frame2, orient="horizontal", length=200, mode="determinate")
    message_progress_bar2.pack(side=tkinter.TOP, anchor=tkinter.W, pady=5)
    message_progress_bar2["maximum"] = 1000
    message_progress_bar2["value"] = 0
    frame2.pack(side=tkinter.LEFT, anchor=tkinter.W, padx=2)
    # endregion
    frame.pack(expand=True)

    # 隐藏主窗口
    root.withdraw()
    root.update()
    # endregion

    # region 获取并处理命令行参数
    module_name = "ClientVersion"
    order = "update"
    client_pid = 0  # 旧客户端进程pid，更新主客户端时用于重启
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:p:o:")
    except getopt.GetoptError:
        print('test.py -c <module_name> -p<pid> -o<add,delete,update>')
        sys.exit(2)
    for opt, value in opts:
        if opt == "-c":
            module_name = value
            print(module_name)
        elif opt == "-p":
            client_pid = value
        elif opt == "-o":
            order = value
    # endregion

    # 启动窗口
    local_xml_path = os.path.join(sys.path[0], "VersionInfo.xml")
    update_xml_path = os.path.join(sys.path[0], "VersionInfoTemp.xml")
    local_xml = VersionInfoXml(local_xml_path)
    server_ip = local_xml.get_node_value("ServerInfo/ServerIp")
    server_port = local_xml.get_node_value("ServerInfo/ServerPort")
    del local_xml
    update_flag = AutoUpdate(server_ip, server_port, module_name, order)
    root.destroy()
    if update_flag and (module_name == "ClientVersion" or module_name == "all_module"):
        # print("restart")
        restart_client()
