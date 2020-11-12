# -*- coding: utf-8 -*-

import re
import bs4
import urllib.request  
from bs4 import BeautifulSoup 
import urllib.parse
import sys
import time
import socket
import os


#先建立一个存储爬虫结果的文件
#进入工作目录
os.chdir('D:\\NULL')

#设置超时时间
socket.setdefaulttimeout(5)

#防止反爬虫，构造合理的HTTP请求头
header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"}

#首先获取代理IP列表
url = 'http://www.nimadaili.com/http/1/'
print('url = ' + url)

try:
    request = urllib.request.Request(url, headers = header)
    response = urllib.request.urlopen(request).read()
    soup = BeautifulSoup(response, "lxml")
    #print(soup.prettify())
    #print(soup.tbody.find('tr').find('td').get_text())
    proxy_list = []
    for tr in soup.tbody.find_all('tr'):
        ip = tr.find('td').get_text()
        proxy_list.append(ip)
        
    print('proxy_list : %s' % proxy_list)
except Exception as e:
    print("Get proxy failed, %s" % str(e))
    sys.exit()

#打开结果文档，错误结果文档，要查询的前缀文档
resultfile = open(r"result.txt", 'w')
errorfile = open(r'error.txt', 'w')
prefixfile = open(r"prefix.txt")

while True:
    #按行读取文档，获取前缀
    prefix = prefixfile.readline().strip('\n')
    
    #如果读取完了就退出
    if not prefix:
        print("Finished")
        break

    #按照号段 130+0000 到 130+9999的范围进行循环查询
    print ('prefix = ' + prefix)
    haoduan_start = prefix + '0000'
    haoduan_end = prefix + '9999'

    #代理IP的索引
    proxy_index = 0
    proxy_index_max = len(proxy_list) - 1

    #对130前缀内所有7位号段进行查询
    for haoduan in range(int(haoduan_start), int(haoduan_end)):
        #失败计数器
        fail_count = 0
        
        while True:
            try:
                #组装ip138网站的号段查询URL
                url = 'http://www.ip138.com/mobile.asp?mobile=' + str(haoduan) + '&action=mobile'
                #print('url = ' + url)
                
                #根据失败计数更换代理IP，没有失败则不换代理IP
                if fail_count != 0:                    
                    if proxy_index >= proxy_index_max:
                        proxy_index = 0
                    else:
                        proxy_index += 1
                    proxy_addr = proxy_list[proxy_index]
                    print('proxy_addr = ' + proxy_addr)
                    proxy = urllib.request.ProxyHandler({'http': proxy_addr})
                    opener = urllib.request.build_opener(proxy, urllib.request.HTTPHandler)
                    urllib.request.install_opener(opener)

                #获取查询结果
                request = urllib.request.Request(url, headers = header)
                response = urllib.request.urlopen(request).read()
                #print('response = ' + str(response))            
                
                #用来代替正则式取源码中相应标签中的内容
                soup = BeautifulSoup(response, "lxml")  
                res = soup.find('tr', bgcolor="#EFF1F3")

                #获取省份，城市
                res1 = res.next_sibling.next_sibling.find('td', class_="tdc2").get_text()
                res1 = res1.strip()
                if len(res1) == 0:
                    province=''
                    city=''
                else:
                    res1 = res.next_sibling.next_sibling.find('td', class_="tdc2").get_text()
                    province = res1.split()[0]
                    if len(res1.split()) == 1:
                        city = res1.split()[0] + '市'
                    else :
                        city = res1.split()[1]

                #获取号段类型，区号，邮编
                type1 = res.next_sibling.next_sibling.next_sibling.next_sibling.find('td', class_="tdc2").get_text()
                areacode = res.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.find('td', class_="tdc2").get_text()
                postcode = res.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.find('td', class_="tdc2").get_text()
                if postcode:
                    postcode = postcode.split()[0]

                #写入结果文件，打印
                resultfile.write("{},{},{},{},{},{}\n".format(haoduan, province, city, type1, areacode, postcode))
                print("search result:","{},{},{},{},{},{}".format(haoduan, province, city, type1, areacode, postcode))

                #成功，则跳出本次循环
                break
            except Exception as e:
                print("Failed! Please wait! %s" % str(e))
                fail_count += 1
                print('fail_count = %d' % fail_count)
                #失败计数小于代理IP的数量，则继续换代理IP尝试，否则写错误文件，并结束循环，退出程序
                if fail_count < proxy_index_max:
                    continue
                else:
                    errorfile.write("{}\n".format(haoduan))
                    break

        #失败计数小于代理IP的数量，则获取下一个号段，否则结束循环，退出程序
        if fail_count < proxy_index_max:
            continue
        else:
            break

    #失败计数小于代理IP的数量，则获取下一个前缀，否则结束循环，退出程序
    if fail_count < proxy_index_max:
        continue
    else:
        break

#程序结束，关闭文件
prefixfile.close()
errorfile.close()
resultfile.close()
