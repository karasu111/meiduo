from fdfs_client.client import Fdfs_client

#创建FastDFS客户端实例,并指定他的配置文件


fdfs_client = Fdfs_client('./client.conf')

ret = fdfs_client.upload_appender_by_filename('/home/python/Desktop/111.png')
print(ret)
"""getting connection
<fdfs_client.connection.Connection object at 0x7f4bd6ac1e48>
<fdfs_client.fdfs_protol.Tracker_header object at 0x7f4bd6ac1e10>
{'Group name': 'group1', 'Remote file_id': 'group1/M00/00/00/wKiSgl0sRiGEDsrVAAAAAMTlGPs976.png', 'Status': 'Upload successed.', 'Local file name': '/home/python/Desktop/111.png', 'Uploaded size': '466.00KB', 'Storage IP': '192.168.146.130'}
"""