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

import sys
import getopt

mainfolderprefix = "tmp"
conf_file = "pack.conf"
old_version_zips_dir = "old_version_zips"
dist_dir = "dist"
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
        zip folders and files under foldername.
    '''
    empty_dirs=[]
    save_cwd = os.getcwd()
    try:
        zip=zipfile.ZipFile(filename,'w',zipfile.ZIP_DEFLATED)
        #chdir for no foldername
        os.chdir(foldername)
        for root,dirs,files in os.walk("."):
            empty_dirs.extend([dir for dir in dirs if os.listdir(join(root,dir))==[]])
            for filename in files:
                #print "compressing",join(root,filename).encode("gbk")
                zip.write(join(root,filename).encode("gbk"))
        for dir in empty_dirs:
            zif=zipfile.ZipInfo(join(root, dir).encode("gbk"+"/"))
            zip.writestr(zif,"")
        zip.close()
    finally:
        os.chdir(save_cwd)
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
def move_file(srcfile, file, folder):
    if not os.path.exists(srcfile):
        return False
    if not os.path.exists(folder):
        os.makedirs(folder)
    dest_full_path = os.path.join(folder, file)
    # if dest file exist. delete
    if os.path.exists(dest_full_path):
        os.remove(dest_full_path)
    # move file
    os.rename(srcfile, dest_full_path)
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
def gen_module(module,config_file,version, encoding, http_prefix, https_prefix, olddic):
    '''
        parse xml and deal with every item
        return the file number copied
    '''
    copyFileNum = 0;
    mainFolder = module + mainfolderprefix
    if not os.path.exists(mainFolder):
        os.makedirs(mainFolder)
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
            #print node_value
            if platform.platform()=="Windows":
                file_path = node_value.replace("/","\\")
            else:
                file_path = node_value
            md5 = md5_file(file_path)
            print "file md5:" + md5
            http_value = http_prefix+str(node_value)
            #if same md5.
            if olddic and olddic[http_value] == md5:
                print "olddic[" + http_value +"]:" + olddic[http_value]
                #no need copy
                copy_result = True;
            else:
                #copy file
                copy_result = deal_item_copy(file_path, dest_filename, os.path.join(mainFolder,dest_folder))
                if copy_result:
                    copyFileNum = copyFileNum + 1
            if not copy_result:
                print "copy:" + file_path + " "+ str(copy_result)
            #create element http
            url_node = meta_conf.createElement("url")
            deal_item_metaitem(url_node,getmime(node_value),encoding,http_value,dest_folder + "/" + dest_filename,md5)
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
    return copyFileNum
def increaseversion(v, major):
    '''
        version add 1
    '''
    splits = v.split(".")
    majorversion = int(splits[0])
    minorversion = int(splits[1])
    if major:
        majorversion = majorversion + 1
        minorversion = 0
    else:
        minorversion = minorversion + 1
    return str(majorversion) + "." + str(minorversion)
def parse_metaxml(filename):
    '''
    parse metadata.xml and return (value md5) dics
    '''
    metaxml = minidom.parse(filename)
    result ={}
    for node in metaxml.getElementsByTagName("url"): 
        md5 = node.getAttribute("md5")
        value = node.getAttribute("value")
        if "" == md5:
            print value + " no md5"
        else:
            result[value]=md5
    return result
def get_old_version_metadata(module_name, unzip_dir):
    target_zip = ""
    target_metaxml = ""
    for root,dirs,files in os.walk(old_version_zips_dir):
        for filename in files:
            if module_name in filename:
                target_zip = join(root,filename).encode("gbk")
                break
    if "" == target_zip:
        pass
    else:
        z = zipfile.ZipFile(target_zip, mode='r')
        if not os.path.exists(unzip_dir):
            os.makedirs(unzip_dir)
        target_metaxml = os.path.join(unzip_dir, "metadata.xml")
        if os.path.exists(target_metaxml):
            os.remove(target_metaxml)
        for name in z.namelist():
            if "metadata.xml" == name:
                outfile = open(target_metaxml, 'wb')
                outfile.write(z.read(name))
                outfile.close()
                break
    return target_metaxml
def deal_module(module_name, module_name_conf, version, encoding, http_prefix, https_prefix):
    '''
        compare with old version (if exsits) and gen module file then zip it.
    '''
    #old zip file unzip dir
    unzip_dir = os.path.join(old_version_zips_dir, module_name + "_old")
    #output folder to work
    tmp_dir = module_name + mainfolderprefix
    try:
        diff = get_old_version_metadata(module_name, unzip_dir)
        print "module_name:" + diff
        if "" == diff:
            filesuffix = "_All.zip"
        else:
            filesuffix = "_Patch.zip"
        if "" == diff:
            olddic = None
        else:
            olddic = parse_metaxml(diff)
        #output zip file
        result_zip_file = module_name + "_" + version + filesuffix

        copy_num = gen_module(module_name, module_name_conf, version, encoding, http_prefix, https_prefix, olddic)
        #only copy files, we zip it
        if copy_num > 0:
            zipfolder(tmp_dir, result_zip_file)
            move_file(result_zip_file, result_zip_file, dist_dir)
    finally:
        cleanTmp(tmp_dir)
        cleanTmp(unzip_dir)
def cleanTmp(tmpDir):
    if os.path.exists(tmpDir):
        __import__('shutil').rmtree(tmpDir)
def main(argv=sys.argv):
    #read command line args
    shortargs = 'm'
    longargs = []
    opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)
    major = False
    diff = ""
    for opt, val in opts:
        if opt == "-m":
            major = True
            continue
        '''
        if opt == "--diff":
            diff = val
            continue
        '''
    #read config file
    cf = ConfigParser.ConfigParser()
    cf.read(conf_file)
    versionorg = cf.get("version", "last_version_name")
    encoding = cf.get("constant", "encoding")
    http_prefix = cf.get("constant", "http_prefix")
    https_prefix = cf.get("constant", "https_prefix")
    # app_cart = cf.get("conf", "app_cart")
    # app_item = cf.get("conf", "app_item")
    # app_nav = cf.get("conf", "app_nav")
    # app_trade = cf.get("conf", "app_trade")
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
    #get new version name
    version = increaseversion(versionorg, major)
    success = True
    try:
        modules = ["app_cart", "app_item", "app_nav","app_trade"]
        for module_name in modules:
            deal_module(module_name, cf.get("conf", module_name), version, encoding, http_prefix, https_prefix)
    except:
        success = False
        print sys.exc_info()
    if success:
       cf.set("version", "last_version_name", version)
       cf.write(open(conf_file, "w"))
if __name__=="__main__":
    main()    
