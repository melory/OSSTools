#!/usr/bin/env python
# -*- coding: utf-8 -*-
## ossbrowser
## Author: melory
## Email:imsrch@melory.me
## License: GPL Version 2


from oss_api import *
from oss_util import *

HOST="storage.aliyun.com"
#ACCESS_ID and SECRET_ACCESS_KEY should not be empty, please input correct one.
   
def login(access_id, secret_access_key): 
    '''login'''
    oss = OssAPI(HOST, access_id, secret_access_key)
    res = oss.get_service()
    if (res.status / 100) == 2:
        return oss
    else:
        return None
 
   
def get_bucket_list(oss):
    '''get all buckets' info, return a list'''
    res = oss.get_service()
    if (res.status / 100) == 2:
        body = res.read()
        h = GetServiceXml(body)
        return h.list()
    else:
        return []
    
def put_object(oss, filename, bucket_name, object_name, content_type="text/HTML", headers={}):
    '''put object into bucket, the content of object is read from file'''
    res = oss.put_object_from_file(bucket_name, object_name, filename, content_type, headers)
    if (res.status / 100) == 2:
        return True
    else:
        return False

def put_object_from_string(oss, bucket, object, input_content, content_type='application/octet-stream', headers = {}):
    '''Put object into bucket, the content of object is from input_content'''
    res = oss.put_object_from_string(bucket, object, input_content, content_type, headers)
    if (res.status / 100) == 2:
        return True
    else:
        return False
    
def get_object_to_file(oss, bucket_name, object_name, filename, headers={}):
    '''Get object and write the content of object into a file'''
    res = oss.get_object_to_file(bucket_name, object_name, filename, headers)
    if (res.status / 100) == 2:
        return True
    else:
        return False
    
def head_object(oss, object_name, bucket_name, headers={}):
    '''To get the meta message of object without the content'''
    res = oss.head_object(bucket_name, object_name, headers)
    if (res.status / 100) == 2:
         header_map = convert_header2map(res.getheaders())
         #content_len = safe_get_element("content-length", header_map)
         #etag = safe_get_element("etag", header_map).upper()
         return header_map
    else:
        return None
        
def get_bucket_acl(oss, bucket_name):
    '''Get Access Control Level of bucket'''
    res = oss.get_bucket_acl(bucket_name)
    if (res.status / 100) == 2:
        body = res.read()
        h = GetBucketAclXml(body)
        return h
    else:
        return None

def get_bucket_objects(oss, bucket_name, prefix = "", marker = "", \
                       delimiter = "/", maxkeys = "100", headers = {}):
    '''List object that in bucket'''
    res = oss.get_bucket(bucket_name, prefix, marker, delimiter, maxkeys, headers)
    if (res.status / 100) == 2:
        body = res.read()
        h = GetBucketXml(body)
        #(file_list, common_list) = h.list()
        return h
    else:
        return None
    
def upload_large_file(oss, bucket_name, object_name, filename, thread_num = 10, max_part_num = 1000):
    '''
    Upload large file, the content is read from filename. 
    The large file is splitted into many parts. It will 
    put the many parts into bucket and then merge all 
    the parts into one object.
    ''' 
    res = oss.upload_large_file(bucket_name, object_name, filename, thread_num, max_part_num)    
    if (res.status / 100) == 2:
        return True
    else:
        return False
    
def delete_object(oss, bucket_name, object_name, headers = {}):
    '''delete object'''
    res = oss.delete_object(bucket_name, object_name, headers)
    if (res.status / 100) == 2:
        return True
    else:
        return False

    
def delete_bucket(oss, bucket_name):
    '''
    delete bucket, note that there must be 
    no objects in this bucket, else it will 
    failure to delete the bucket'''
    res = oss.delete_bucket(bucket_name)
    if (res.status / 100) == 2:
        return True
    else:
        return False
    
def delete_bucket_objects(oss, bucket_name):
    '''delete the bucket and all objects in it'''
    res = get_bucket_objects(oss, bucket_name)
    if res:
        (file_list, common_list) = res.list()
    else:
        return True
    for objinfo in file_list:
        res = delete_object(oss, bucket_name, objinfo[0])
        if not res:
            return False
    res = delete_bucket(oss, bucket_name)
    if not res:
        return False
    return True

def put_bucket(oss, bucket_name, acl, headers):
    '''Create bucket'''
    res = oss.put_bucket(bucket_name, acl=acl, headers = {})
    if (res.status / 100) == 2:
        return True
    else:
        return False
        
    
def get_object_in_bucket(oss, bucket_name):
    obj = GetAllObjects()
    res = obj.get_object_in_bucket(oss, bucket_name)
    if res:
        return res[0]
    else:
        return []