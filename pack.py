#!/usr/bin/env python
# -*- coding: cp936 -*-
from hashlib import md5

import os,zipfile
from os.path import join
from datetime import date
from time import time

import ConfigParser
import platform

from xml.dom import minidom
mainfolderprefix = "tmp"
def md5_file(name):
    m = md5()
    if not os.path.exists(name):
        return ""
    a_file = open(name, 'rb')
    m.update(a_file.read())
    a_file.close()
    return m.hexdigest()
'''
    zip a whole directory and its sub directories and files
'''
def zipfolder(foldername,filename):
    '''
        zip folder foldername and all its subfiles and folders into
        a zipfile named filename
    '''
    empty_dirs=[]
    zip=zipfile.ZipFile(filename,'w',zipfile.ZIP_DEFLATED)
    for root,dirs,files in os.walk(foldername):
        empty_dirs.extend([dir for dir in dirs if os.listdir(join(root,dir))==[]])
        for filename in files:
            print "compressing",join(root,filename).encode("gbk")
            zip.write(join(root,filename).encode("gbk"))
    for dir in empty_dirs:
        zif=zipfile.ZipInfo(join(root,dir).encode("gbk"+"/"))
        zip.writestr(zif,"")
    zip.close()
    print "Finish compressing"

'''
     copy file according item
'''
def deal_item_copy(srcfile, file, folder):
    if not os.path.exists(srcfile):
        return False
    if not os.path.exists(folder):
        os.makedirs(folder)
    dest_full_path = os.path.join(folder, file)
    # if dest file exist. delete
    if os.path.exists(dest_full_path):
        os.remove(dest_full_path)
    # copy file
    open(dest_full_path, "wb").write(open(srcfile, "rb").read()) 
    return True
def deal_item_metaitem(node, mime, encoding, value, uri, md5):
    node.setAttribute("mime", mime)
    node.setAttribute("encoding", encoding)
    node.setAttribute("value", value)
    node.setAttribute("uri", uri)
    if md5:
        node.setAttribute("md5", md5)
def getmime(value):
    if value.endswith("html"):
        return "text/html"
    elif value.endswith("css"):
        return "text/css"
    elif value.endswith("js"):
        return "text/javascript"
    elif value.endswith("gif"):
        return "image/gif"
    else:
        return "text/html"
def getfolder(value):
    if value.endswith("html"):
        return "html"
    elif value.endswith("css"):
        return "css"
    elif value.endswith("js"):
        return "js"
    elif value.endswith("gif"):
        return "resource"
    else:
        return "html"
def getfilename(value):
    splits = value.split("/")
    return splits[len(splits)-1]
def deal_module(module,config_file,version, encoding, http_prefix, https_prefix):
    '''
        parse xml and deal with every item
    '''
    mainFolder = module + mainfolderprefix
    model_config = minidom.parse(config_file)
    impl = minidom.getDOMImplementation()
    meta_conf=impl.createDocument(None, None, None)
    root = meta_conf.createElement("root")
    module_node = meta_conf.createElement('module')
    module_node.setAttribute('name', str(module))
    module_node.setAttribute('version', str(version))
    for node in model_config.getElementsByTagName("item"):     
        value_str = node.getAttribute("type")
        value_int = int(value_str)
        print value_str
        if 1 == value_int:
            #copy with value and uri
            node_value=node.getAttribute("value")
            node_url=node.getAttribute("uri")
            url_node = meta_conf.createElement("url")
            deal_item_metaitem(url_node,getmime(node_value),encoding,str(node_value),node_url,None)
            module_node.appendChild(url_node)
        elif 2 == value_int or 3 == value_int:
            #http
            node_value=node.getAttribute("value")
            dest_filename = getfilename(node_value);
            dest_folder = getfolder(node_value)
            print node_value
            if platform.platform()=="Windows":
                file_path = node_value.replace("/","\\")
            else:
                file_path = node_value
            #copy file
            print "copy:" + file_path + " "+ str(deal_item_copy(file_path, dest_filename, os.path.join(mainFolder,dest_folder)))
            #create element http
            url_node = meta_conf.createElement("url")
            md5 = md5_file(file_path)
            deal_item_metaitem(url_node,getmime(node_value),encoding,http_prefix+str(node_value),dest_folder + "/" + dest_filename,md5)
            module_node.appendChild(url_node)
            if (3 == value_int):
                #create element https
                url_node1 = meta_conf.createElement("url")
                deal_item_metaitem(url_node1,getmime(node_value),encoding,https_prefix+str(node_value),dest_folder + "/" + dest_filename, md5)
                module_node.appendChild(url_node1)
        else:
            print vaule_str
    root.appendChild(module_node)
    meta_conf.appendChild(root)
    f=file(os.path.join(mainFolder, "metadata.xml"),'w')
    meta_conf.writexml(f,'',' ','\n','utf-8')
    f.close()
if __name__=="__main__":
    print getfilename("static/c/fd/base/css/base/base.s.min.css")
    cf = ConfigParser.ConfigParser()
    cf.read("pack.conf")
    version = cf.get("version", "version_name")
    encoding = cf.get("constant", "encoding")
    http_prefix = cf.get("constant", "http_prefix")
    https_prefix = cf.get("constant", "https_prefix")
    app_cart = cf.get("conf", "app_cart")
    app_item = cf.get("conf", "app_item")
    app_nav = cf.get("conf", "app_nav")
    app_trade = cf.get("conf", "app_trade")
    '''
    print version
    print encoding
    print http_prefix
    print https_prefix
    print app_cart
    print app_item
    print app_nav
    print app_trade
    '''

    module_app_cart_name = "app_cart"
    deal_module(module_app_cart_name,app_cart,version,encoding,http_prefix,https_prefix)
    zipfolder(module_app_cart_name + mainfolderprefix, module_app_cart_name + "_" + version + "_All.zip")

    module_app_item_name = "app_item"
    deal_module(module_app_item_name,app_item,version,encoding,http_prefix,https_prefix)
    zipfolder(module_app_item_name + mainfolderprefix, module_app_item_name + "_" + version + "_All.zip")

    module_app_nav_name = "app_nav"
    deal_module(module_app_nav_name,app_nav,version,encoding,http_prefix,https_prefix)
    zipfolder(module_app_nav_name + mainfolderprefix, module_app_nav_name + "_" + version + "_All.zip")

    module_app_trade_name = "app_trade"
    deal_module(module_app_trade_name,app_trade,version,encoding,http_prefix,https_prefix)
    zipfolder(module_app_trade_name + mainfolderprefix, module_app_trade_name + "_" + version + "_All.zip")

