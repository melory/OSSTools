#!/usr/bin/env python
# -*- coding: utf-8 -*-
## ossbrowser
## Author: HuangMeilong
## Email:imsrch@gmail.com
## License: GPL Version 2



from ossvue_utils import *
from oss_ui import *
from wx.lib.wordwrap import wordwrap
import wx
import sys
import re
import webbrowser

#---------------------------------------------------------------------------

preferred_encoding = "UTF-8"


def unicodise(string, encoding = None, errors = "replace"):
    """
    Convert 'string' to Unicode or raise an exception.
    """
    global preferred_encoding
    
    if not encoding:
        encoding = preferred_encoding

    if type(string) == unicode:
        return string
    try:
        return string.decode(encoding, errors)
    except UnicodeDecodeError:
        raise UnicodeDecodeError("Conversion to unicode failed: %r" % string)

##authentication info
HOST="storage.aliyun.com"
ACCESS_ID = "ACSExkTj45MMzTMu"
SECRET_ACCESS_KEY = "k8H0n6BCKi"
#oss = login(ACCESS_ID, SECRET_ACCESS_KEY)
#ACCESS_ID = ""
#SECRET_ACCESS_KEY = ""
oss = None

##  
app = wx.PySimpleApp(0)
log = open('log.txt', 'a+')
wx.InitAllImageHandlers()

column_names = [u'文件名', u'最后修改时间', u'ETag', u'文件大小', u'OwnerID', u'OwnerDispalyName', u'类型']
bucket_names = []
rcd = []
rcds = []
all_data = {}
new_bucket_name = u""
new_bucket_acl = u""
acl_choices = [u" =====私有读写权限=====",u" =====公共读私有写=====",u" =====公共读写权限====="]
acl_options = [u"私有读写权限",u"公共读私有写",u"公共读写权限"]
acl_values = ['private', 'public-read', 'public-read-write']
selected_bucket = u""
edit_bucket_acl_option = u""
search_types = [u"包含字符串：", u"前缀为：", u"后缀为：", u"正则表达式："]
search_type = u""

login_frame = wx.Frame(parent=None, title=u"登录Aliyun OSS", 
                       pos=(550, 250), size=(300, 180), 
                       style=wx.DEFAULT_FRAME_STYLE
                       )

def KeyIDEvtText(event):
    global ACCESS_ID
    ACCESS_ID = event.GetString()
    ACCESS_ID = unicodise(ACCESS_ID)

def KeySecretEvtText(event):
    global SECRET_ACCESS_KEY
    SECRET_ACCESS_KEY = event.GetString()
    SECRET_ACCESS_KEY = unicodise(SECRET_ACCESS_KEY)

def OnLoginOK(event):
    global oss
    global log
    global login_frame
    global oss_frame
    global log_listctrl
    global operation_listctrl
    oss = login(ACCESS_ID, SECRET_ACCESS_KEY)
    oss_frame.Enable()
    if oss:
        if log.closed:
            log = open('log.txt', 'a+')   
        log.write((u'[' + unicodise(time.asctime()) + u']  ACCESS_ID: ' + ACCESS_ID + u' Logged in.  [OK]\n').encode('utf-8'))
        log.flush()
        login_frame.Close()
        refresh_pages()
        ## update the operation_listctrl
        operation_listctrl.InsertColumn(0, u'最近操作')
        operation_listctrl.SetColumnWidth(0, 800)
        operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  ACCESS_ID: ' + ACCESS_ID + u' Logged in.  [OK]\n'])
        ## set all log
        if not log.closed:
            log.close()
            log = open('log.txt', 'r')
            result_count = 0
            log_listctrl.ClearAll()
            log_listctrl.InsertColumn(0, u'历史日志')
            log_listctrl.SetColumnWidth(0, 800)
            for eachline in log:
                log_listctrl.InsertStringItem(result_count, unicodise(eachline))
                result_count += 1
            log.close()
        
        
    else:
        dlg = wx.MessageDialog(login_frame, u'验证失败，请重新输入或者检查网络连接状况.',
                               u'提示信息',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()        
        if log.closed:
            log = open('log.txt', 'a+')
        log.write((u'[' + unicodise(time.asctime()) + u']  ACCESS_ID: ' + ACCESS_ID + u' Logged in.  [Failure]\n').encode('utf-8'))
        log.flush()

def OnLoginCalcel(event):
    global login_frame
    global log
    login_frame.Close()
    log.close()
    sys.exit()
    
def OnCloseLogin(event):
    global login_frame
    global log
    login_frame.DestroyChildren()
    login_frame.Destroy()
    if not oss:
        log.close()
        sys.exit()

def go_login():
    global login_frame
    if not login_frame:
        login_frame = wx.Frame(parent=None, title=u"登录Aliyun OSS", 
                               pos=(550, 250), size=(300, 180), 
                               style=wx.DEFAULT_FRAME_STYLE
                               )
    login_panel = wx.Panel(login_frame, -1)
    l1 = wx.StaticText(login_panel, -1, u"Key ID:")
    t1 = wx.TextCtrl(login_panel, -1, u"", size=(180, -1))
    wx.CallAfter(t1.SetInsertionPoint, 0)
    login_panel.Bind(wx.EVT_TEXT, KeyIDEvtText, t1)
    l2 = wx.StaticText(login_panel, -1, u"Key Secret:")
    t2 = wx.TextCtrl(login_panel, -1, u"", size=(180, -1), style = wx.TE_PASSWORD)
    login_panel.Bind(wx.EVT_CHOICE, KeySecretEvtText, t2)
    new_bucket_ok_btn = wx.Button(login_panel, -1, label=u"登录", size=(90,30))
    new_bucket_cancel_btn = wx.Button(login_panel, -1, label=u"取消", size=(90,30))
    login_panel.Bind(wx.EVT_BUTTON, OnLoginOK, new_bucket_ok_btn)
    login_panel.Bind(wx.EVT_BUTTON, OnLoginCalcel, new_bucket_cancel_btn)
    
    new_bucket_sizer1 = wx.FlexGridSizer(cols=3, hgap=2, vgap=2)
    new_bucket_sizer1.AddMany([ l1, t1, (0,0),
                               l2, t2, (0,0)
                               ])
    new_bucket_sizer2 = wx.FlexGridSizer(cols=3, hgap=30, vgap=0)
    new_bucket_sizer2.AddMany([(0,0), new_bucket_ok_btn, new_bucket_cancel_btn
                               ])
    border = wx.BoxSizer(wx.VERTICAL)
    border.Add(new_bucket_sizer1, 2, wx.ALL, 15)
    border.Add(new_bucket_sizer2, 1, wx.ALL, 5)
    login_panel.SetSizer(border)
    login_panel.SetAutoLayout(True)
    login_frame.Bind(wx.EVT_CLOSE, OnCloseLogin)
    login_frame.Show()



#new_bucket_frame = wx.Frame(parent=None, title="新建Bucket", 
#                                pos=(550, 250), size=(300, 180), 
#                                style=wx.DEFAULT_FRAME_STYLE
#                                )
#edit_bucket_acl_frame = wx.Frame(parent=None, title="设置ACL", 
#                                 pos=(550, 250), size=(240, 180), 
#                                 style=wx.DEFAULT_FRAME_STYLE
#                                 )

 
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
##main frame with MenuBar ToolBar and StatusBar

#oss_frame = wx.Frame(parent = None, size=(1000, 600), style=wx.DEFAULT_FRAME_STYLE)
oss_frame = OSSFrame(parent=None, size=(1024, 680), pos=(140, 20),
                     style=wx.DEFAULT_FRAME_STYLE, 
                     title=u"OSS Browser 1.2.1", log = log 
                     )

new_bucket_frame = wx.Frame(parent=oss_frame, title=u"新建Bucket", 
                                pos=(550, 250), size=(300, 180), 
                                style=wx.DEFAULT_FRAME_STYLE
                                )
edit_bucket_acl_frame = wx.Frame(parent=oss_frame, title=u"设置ACL", 
                                 pos=(550, 250), size=(240, 180), 
                                 style=wx.DEFAULT_FRAME_STYLE
                                 )

oss_panel = wx.Panel(oss_frame, -1, style=wx.WANTS_CHARS)
#---------------------------------------------------------------------------
#oss_notebook
oss_notebook = wx.Notebook(oss_panel, style=wx.BK_DEFAULT)

oss_notebook.SetPageSize((600, 100))
oss_notebook.SetSize((610, 110))


task_panel = wx.Panel(oss_notebook, -1)
task_list = wx.ListCtrl(task_panel, size=(100,100), style=wx.LC_REPORT)
task_list.InsertColumn(0, 'Name')
task_list.InsertColumn(1, 'Status')
#employees = [('Earl Boffo', 'Software'), ('Mildred Plotka', 'Software'), ('Sugar Kane', 'QA')]
employees = [('', '')]
for i in employees:
    index = task_list.InsertStringItem(sys.maxint, i[0])
    task_list.SetStringItem(index, 1, i[1])
#task_list.Append(["ying", "ying"])
mainSizer = wx.BoxSizer(wx.VERTICAL)
mainSizer.Add(task_list, 0, wx.EXPAND|wx.ALL, 5)
task_panel.SetSizer(mainSizer)
task_panel.Show()
oss_notebook.AddPage(task_panel, u"任务")

operation_panel = wx.Panel(oss_notebook, -1)
operation_listctrl = wx.ListCtrl(operation_panel, -1, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
operation_sizer = wx.BoxSizer(wx.VERTICAL)
operation_sizer.Add(operation_listctrl,  1, wx.EXPAND|wx.ALL)
operation_panel.SetSizer(operation_sizer)
operation_panel.Show()
oss_notebook.AddPage(operation_panel, u"最近操作")

log_panel = wx.Panel(oss_notebook, -1)
log_listctrl = wx.ListCtrl(log_panel, -1, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
log_sizer = wx.BoxSizer(wx.VERTICAL)
log_sizer.Add(log_listctrl,  1, wx.EXPAND|wx.ALL)
log_panel.SetSizer(log_sizer)
log_panel.Show()
oss_notebook.AddPage(log_panel, u"历史日志")

properties_panel = wx.Panel(oss_notebook, -1)
oss_notebook.AddPage(properties_panel, u"文件属性")

search_panel = wx.Panel(oss_notebook, -1, style=wx.WANTS_CHARS)
search_result_listcrl = wx.ListCtrl(search_panel, -1, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
search_sizer = wx.BoxSizer(wx.VERTICAL)
search_sizer.Add(search_result_listcrl, 1, wx.EXPAND|wx.ALL)
search_panel.SetSizer(search_sizer)
search_panel.Show()
oss_notebook.AddPage(search_panel, u"搜索结果")


#oss_notebook end


#---------------------------------------------------------------------------
#ListBOOK
oss_listbook = wx.Listbook(oss_panel, wx.ID_ANY, style=
                           wx.BK_DEFAULT
                           #wx.BK_TOP
                           #wx.BK_BOTTOM
                           #wx.BK_LEFT
                           #wx.BK_RIGHT
                           )

il = wx.ImageList(48, 48)
for i in range(len(bucket_names)):
    il.Add(wx.Bitmap("..\\res\\bucket.png"))
oss_listbook.AssignImageList(il)

def OnUseNative(self, event):
    wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", not event.IsChecked())
    wx.GetApp().GetTopWindow().LoadDemo("ListCtrl_virtual")

def OnPageChanged(self, event):
    old = event.GetOldSelection()
    new = event.GetSelection()
    sel = self.GetSelection()
    event.Skip()
        
def OnBucketClicked(event):
    global selected_bucket
    choose = event.GetSelection()
    selected_bucket = bucket_names[choose]
    


pages = []
file_list = []
common_list = []
for bucket in bucket_names:
    res = get_bucket_objects(oss, bucket, prefix = '')
    if res:
        (file_list, common_list) = res.list()
        file_list = file_list
        common_list = common_list
    else:
        file_list = []
        common_list = []
    rcds = []
    rcd = []
    if len(common_list):
        for folder_item in common_list:
            rcd = [unicodise(folder_item)]
            for i in range(len(column_names) - 1):
                rcd.append(u'')
            if len(rcd):rcds.append(rcd) 
    for file_item in file_list:
        file_item_t = list(file_item)
        time_parts = file_item_t[1].split("T")
        file_item_t[1] = time_parts[0] + " " + time_parts[1][0:8]
        if float(file_item_t[3]) < 1024:
            file_size = float(file_item_t[3])
            size_unit = " Byte(s)"
        elif float(file_item_t[3]) < 1024 * 1204:
            file_size = float(file_item_t[3]) / 1024
            size_unit = " KB"
        elif float(file_item_t[3]) < 1024 * 1204 * 1024:
            file_size = float(file_item_t[3]) / 1024 / 1024
            size_unit = " MB"
        else:
            file_size = float(file_item_t[3]) / 1024 / 1024 / 1024
            size_unit = " GB"
        file_item_t[3] = str(file_size) + size_unit
        rcds.append(file_item_t)
 
            
    #----------------------------------------------------------------------------
    #object_list_panel
    object_list_panel = wx.Panel(oss_listbook, -1, style=wx.WANTS_CHARS)
    object_list_sizer = wx.BoxSizer(wx.VERTICAL)  
    
    if wx.Platform == "__WXMAC__" and hasattr(wx.GetApp().GetTopWindow(), "LoadDemo"):
        useNative = wx.CheckBox(object_list_panel, -1, "Use native listctrl")
        useNative.SetValue( 
            not wx.SystemOptions.GetOptionInt("mac.listctrl.always_use_generic") )
        object_list_panel.Bind(wx.EVT_CHECKBOX, OnUseNative, useNative)
        object_list_sizer.Add(useNative, 0, wx.ALL | wx.ALIGN_RIGHT, 4)
    
    #----------------------------------------------------------------------------
    #object_list
    #add_obj_btn = wx.Button(object_list_panel, label="上传文件")
    object_list = OssFileListCtrl(object_list_panel, -1, 
                                  style=wx.LC_REPORT|wx.BORDER_SUNKEN,
                                  records = rcds, column_names=column_names, 
                                  oss=oss, bucket_name = bucket, log=log, 
                                  operation_list = operation_listctrl
                                  )
    #object_list end
    #----------------------------------------------------------------------------
    
    object_list_sizer.Add(object_list, 1, wx.EXPAND) 
    #object_list_sizer.Add(add_obj_btn, 0, wx.ALL|wx.CENTER)
    object_list_panel.SetSizer(object_list_sizer)
    object_list_panel.SetAutoLayout(True)
    #object_list_panel
    #----------------------------------------------------------------------------
    
    pages.append((object_list_panel, bucket))

imID = 0
if len(pages):
    for page, label in pages:
        oss_listbook.AddPage(page, label, imageId=imID)
        imID += 1
else:
    blank_panel = wx.Panel(oss_listbook, -1)
    blank_panel.SetBackgroundColour('white')
    oss_listbook.AddPage(blank_panel, '', imageId=imID)
    if oss:
        wx.StaticText(blank_panel, -1, 
                      u'\n\n\n\n\n\n\n\n\n\n\n\n                                                        目前该账户中没有任何文件，可以点击[新建Bucket]按钮来新建Bucket!', wx.Point(10, 10))
    else:
        wx.StaticText(blank_panel, -1, 
                      u'\n\n\n\n\n\n\n\n\n\n\n\n                                                                         您还没有登录，请先登录：[账户]->[登录]', wx.Point(10, 10))

oss_listbook.Bind(wx.EVT_LISTBOOK_PAGE_CHANGED, OnBucketClicked)

 
#ListBook end


## refresh_pages
def refresh_pages():
    global oss
    global bucket_names
    global column_names
    global all_data
    
    if not oss:
        dlg = wx.MessageDialog(new_bucket_frame, u'请先登录!',
                    u'提示信息',
                    wx.OK | wx.ICON_INFORMATION
                    #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                    )
        dlg.ShowModal()
        dlg.Destroy()
    
    else:
        bucket_names = []
        bucket_list = []
        if oss:
            bucket_list = get_bucket_list(oss)
        for buc in bucket_list:
            bucket_names.append(buc[0])
    
        all_data = {}
        for buc_name in bucket_names:
            all_data[buc_name] = get_object_in_bucket(oss, buc_name)
        
        oss_listbook.DeleteAllPages()
        il = wx.ImageList(48, 48)
        for i in range(len(bucket_names)):
            il.Add(wx.Bitmap("..\\res\\bucket.png"))
        oss_listbook.AssignImageList(il)
        pages = []
        file_list = []
        common_list = []
        for bucket in bucket_names:
            res = get_bucket_objects(oss, bucket, prefix = '')
            if res:
                (file_list, common_list) = res.list()
                file_list = file_list
                common_list = common_list
            else:
                file_list = []
                common_list = []
            rcds = []
            rcd = []
            if len(common_list):
                for folder_item in common_list:
                    rcd = [unicodise(folder_item)]
                    for i in range(len(column_names) - 1):
                        rcd.append('')
                    if len(rcd):rcds.append(rcd) 
            for file_item in file_list:
                file_item_t = list(file_item)
                time_parts = file_item_t[1].split("T")
                file_item_t[1] = time_parts[0] + " " + time_parts[1][0:8]
                if float(file_item_t[3]) < 1024:
                    file_size = float(file_item_t[3])
                    size_unit = " Byte(s)"
                elif float(file_item_t[3]) < 1024 * 1204:
                    file_size = float(file_item_t[3]) / 1024
                    size_unit = " KB"
                elif float(file_item_t[3]) < 1024 * 1204 * 1024:
                    file_size = float(file_item_t[3]) / 1024 / 1024
                    size_unit = " MB"
                else:
                    file_size = float(file_item_t[3]) / 1024 / 1024 / 1024
                    size_unit = " GB"
                file_item_t[3] = unicodise(str(file_size) + size_unit)
                rcds.append(file_item_t)
         
                    
            #----------------------------------------------------------------------------
            #object_list_panel
            object_list_panel = wx.Panel(oss_listbook, -1, style=wx.WANTS_CHARS)
            object_list_sizer = wx.BoxSizer(wx.VERTICAL)  
            
            if wx.Platform == "__WXMAC__" and hasattr(wx.GetApp().GetTopWindow(), "LoadDemo"):
                useNative = wx.CheckBox(object_list_panel, -1, "Use native listctrl")
                useNative.SetValue( 
                    not wx.SystemOptions.GetOptionInt("mac.listctrl.always_use_generic") )
                object_list_panel.Bind(wx.EVT_CHECKBOX, OnUseNative, useNative)
                object_list_sizer.Add(useNative, 0, wx.ALL | wx.ALIGN_RIGHT, 4)
            
            #----------------------------------------------------------------------------
            #object_list
            #add_obj_btn = wx.Button(object_list_panel, label="上传文件")
            object_list = OssFileListCtrl(object_list_panel, -1, 
                                          style=wx.LC_REPORT|wx.BORDER_SUNKEN,
                                          records = rcds, column_names=column_names, 
                                          oss=oss, bucket_name = bucket, log=log, 
                                          operation_list = operation_listctrl
                                          )
            #object_list end
            #----------------------------------------------------------------------------
            
            object_list_sizer.Add(object_list, 1, wx.EXPAND) 
            #object_list_sizer.Add(add_obj_btn, 0, wx.ALL|wx.CENTER)
            object_list_panel.SetSizer(object_list_sizer)
            object_list_panel.SetAutoLayout(True)
            #object_list_panel
            #----------------------------------------------------------------------------
            
            pages.append((object_list_panel, bucket))
        
        imID = 0
        if len(pages):
            for page, label in pages:
                oss_listbook.AddPage(page, label, imageId=imID)
                imID += 1
        else:
            blank_panel = wx.Panel(oss_listbook, -1)
            blank_panel.SetBackgroundColour('white')
            oss_listbook.AddPage(blank_panel, '', imageId=imID)
            if oss:
                wx.StaticText(blank_panel, -1, 
                              u'\n\n\n\n\n\n\n\n\n\n\n\n                                                        目前该账户中没有任何文件，可以点击[新建Bucket]按钮来新建Bucket!', wx.Point(10, 10))
            else:
                wx.StaticText(blank_panel, -1, 
                              u'\n\n\n\n\n\n\n\n\n\n\n\n                                                                        您还没有登录，请先登录：[账户]->[登录]', wx.Point(10, 10))
        
        oss_listbook.Bind(wx.EVT_LISTBOOK_PAGE_CHANGED, OnBucketClicked) 
## fresh_pages end

#---------------------------------------------------------------------------
#sizer for oss_listbook and oss_notebook
hbox = wx.BoxSizer()
hbox.Add(oss_listbook, proportion = 1, flag = wx.ALL| wx.EXPAND, border = 5)
hbox2 = wx.BoxSizer()
hbox2.Add(oss_notebook, proportion = 1, flag = wx.ALL| wx.EXPAND, border = 5)
vbox = wx.BoxSizer(wx.VERTICAL)
vbox.Add(hbox, proportion = 2, flag = wx.EXPAND, border = 5)
vbox.Add(hbox2, proportion = 1, flag = wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border = 5)
oss_panel.SetSizer(vbox)

#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

#set StatusBar
oss_frame.SetStatusBar(OSSStatusBar(oss_frame))
#StatusBar end

#---------------------------------------------------------------------------
#set ToolBar
oss_toolbar = oss_frame.CreateToolBar(wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT)

tsize = (24, 24)
new_bucket_bmp =  wx.Bitmap("..\\res\\new.png")
delete_bmp = wx.Bitmap("..\\res\\delete.png")
download_bmp = wx.Bitmap("..\\res\\download.png")
refresh_bmp = wx.Bitmap("..\\res\\refresh.png")
lock_bmp = wx.Bitmap("..\\res\\lock.png")
link_bmp = wx.Bitmap("..\\res\\link.png")
oss_toolbar.SetToolBitmapSize(tsize)



def OnToolRClick():
    pass

def OnClickNewBucket(event):
    global new_bucket_frame
    global new_bucket_name
    global new_bucket_acl
    new_bucket_name = ""
    new_bucket_acl = ""
    if not new_bucket_frame:
        new_bucket_frame = wx.Frame(parent=oss_frame, title=u"新建Bucket", 
                                    pos=(550, 250), size=(300, 180), 
                                    style=wx.DEFAULT_FRAME_STYLE
                                    )
    new_bucket_panel = wx.Panel(new_bucket_frame, -1)
    l1 = wx.StaticText(new_bucket_panel, -1, u"Bucket名:")
    t1 = wx.TextCtrl(new_bucket_panel, -1, u"3-32字符,只包含小写字母和数字", size=(180, -1))
    wx.CallAfter(t1.SetInsertionPoint, 0)
    new_bucket_panel.Bind(wx.EVT_TEXT, BucNameEvtText, t1)
    l2 = wx.StaticText(new_bucket_panel, -1, u"读写权限:")
    acl_choice = wx.Choice(new_bucket_panel, -1, size=(180, -1), 
                           choices=acl_choices)
    new_bucket_panel.Bind(wx.EVT_CHOICE, BucACLEvtText, acl_choice)
    new_bucket_ok_btn = wx.Button(new_bucket_panel, -1, label=u"确定", size=(90,30))
    new_bucket_cancel_btn = wx.Button(new_bucket_panel, -1, label=u"取消", size=(90,30))
    new_bucket_panel.Bind(wx.EVT_BUTTON, OnNewButtonOK, new_bucket_ok_btn)
    new_bucket_panel.Bind(wx.EVT_BUTTON, OnNewButtonCalcel, new_bucket_cancel_btn)


    new_bucket_sizer1 = wx.FlexGridSizer(cols=3, hgap=2, vgap=2)
    new_bucket_sizer1.AddMany([ l1, t1, (0,0),
                    l2, acl_choice, (0,0)
                    ])
    new_bucket_sizer2 = wx.FlexGridSizer(cols=3, hgap=30, vgap=0)
    new_bucket_sizer2.AddMany([(0,0), new_bucket_ok_btn, new_bucket_cancel_btn
                    ])
    border = wx.BoxSizer(wx.VERTICAL)
    border.Add(new_bucket_sizer1, 2, wx.ALL, 15)
    border.Add(new_bucket_sizer2, 1, wx.ALL, 5)
    new_bucket_panel.SetSizer(border)
    new_bucket_panel.SetAutoLayout(True)
    new_bucket_frame.Show()
    
def BucNameEvtText(event):
    global new_bucket_name
    new_bucket_name = event.GetString()
    new_bucket_name = unicodise(new_bucket_name)

def BucACLEvtText(event):
    global new_bucket_acl
    new_bucket_acl = event.GetString()
    new_bucket_acl = unicodise(new_bucket_acl)

def OnNewButtonOK(event):
    global new_bucket_name
    global log
    global operation_listctrl
    if len(new_bucket_name)<3 or len(new_bucket_name)>32:
        dlg = wx.MessageDialog(new_bucket_frame, u'Bucket名称长度为3-32个字符!',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
        dlg.ShowModal()
        dlg.Destroy()
        if log.closed:
            log = open('log.txt', 'a+')
        log.write((u'[' + unicodise(time.asctime()) + u']  创建Bucket失败，错误提示：Bucket名称长度错误。  [Failure]\n').encode('utf-8'))
        log.flush()
        ## update operation_listctrl
        operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  创建Bucket失败，错误提示：Bucket名称长度错误。  [Failure]\n'])
    elif not re.search('^([0-9]|[a-z])+$', new_bucket_name):
        dlg = wx.MessageDialog(new_bucket_frame, u'Bucket名称不合法：只能包括小写字母和数字!',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
        dlg.ShowModal()
        dlg.Destroy()
        if log.closed:
            log = open('log.txt', 'a+')
        log.write((u'[' + unicodise(time.asctime()) + u']  创建Bucket失败，错误提示：Bucket名称不合法。  [Failure]\n').encode('utf-8'))
        log.flush()
        ## update operation_listctrl
        operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  创建Bucket失败，错误提示：Bucket名称不合法。  [Failure]\n'])
    else:
        if oss:
            if new_bucket_acl == acl_choices[1]:
                new_buc_res = put_bucket(oss, new_bucket_name, acl_values[1], headers={})
            elif new_bucket_acl == acl_choices[2]:
                new_buc_res = put_bucket(oss, new_bucket_name, acl_values[2], headers={})
            else:
                new_buc_res = put_bucket(oss, new_bucket_name, acl_values[0], headers={})
            if new_buc_res:
                dlg = wx.MessageDialog(new_bucket_frame, u'Bucket创建成功!',
                            u'提示信息',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
                dlg.ShowModal()
                dlg.Destroy()
                if log.closed:
                    log = open('log.txt', 'a+')
                log.write((u'[' + unicodise(time.asctime()) + u']  创建Bucket [' + new_bucket_name + '] 成功。  [OK]\n').encode('utf-8'))
                log.flush()
                new_bucket_frame.Close()
                ## update operation_listctrl
                operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  创建Bucket[ ' + new_bucket_name + '] 成功。  [OK]\n'])
                
                refresh_pages()
            else:
                dlg = wx.MessageDialog(new_bucket_frame, u'Bucket创建失败!可能Bucket重名，建议更改Bucket名称重试。或者BUcket数目已经达到10个。',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
                dlg.ShowModal()
                dlg.Destroy()
                if log.closed:
                    log = open('log.txt', 'a+')
                log.write((u'[' + unicodise(time.asctime()) + u']  创建Bucket[ ' + new_bucket_name + u'] 失败。  [Failure]\n').encode('utf-8'))
                log.flush()
                new_bucket_frame.Close()
                ## update operation_listctrl
                operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  创建Bucket[ ' + new_bucket_name + u'] 失败。  [Failure]\n'])
        else:
            dlg = wx.MessageDialog(new_bucket_frame, u'OSS用户验证信息错误!请检查网络状态.',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
            dlg.ShowModal()
            dlg.Destroy()
            if log.closed:
                log = open('log.txt', 'a+')
            log.write((u'[' + unicodise(time.asctime()) + u']  创建Bucket失败，错误提示：OSS验证信息失败。  [Failure]\n').encode('utf-8'))
            log.flush()
            new_bucket_frame.Close()
            ## update operation_listctrl
            operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  创建Bucket失败，错误提示：OSS验证信息失败。  [Failure]\n'])

def OnNewButtonCalcel(event):
    global new_bucket_frame
    new_bucket_frame.Close()



def OnClickDeleteBucket(event):
    global selected_bucket
    global log
    global operation_listctrl
    if not selected_bucket:
        dlg = wx.MessageDialog(oss_frame, u'请选中一个Bucket!',
                               u'提示信息',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    else:
        dlg = wx.MessageDialog(oss_frame, u'确认删除Bucket [ '+selected_bucket+' ]?',
                               u'提示信息',
                               wx.YES_NO
                               #wx.OK | wx.ICON_INFORMATION 
                               # | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == 5103:
            delete_bucket_res = delete_bucket(oss, selected_bucket)
            if delete_bucket_res:
                dlg = wx.MessageDialog(oss_frame, u'成功删除Bucket['+selected_bucket+']!',
                                       u'提示信息',
                                       wx.OK | wx.ICON_INFORMATION
                                       #wx.YES_NO 
                                       # | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                       )
                dlg.ShowModal()
                dlg.Destroy()
                if log.closed:
                    log = open('log.txt', 'a+')
                log.write((u'[' + unicodise(time.asctime()) + u']  删除Bucket['+selected_bucket+u']成功!  [OK]\n').encode('utf-8'))
                log.flush()
                ## update operation_listctrl
                operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  删除Bucket['+selected_bucket+u']成功!  [OK]\n'])
                refresh_pages()
            else:
                dlg = wx.MessageDialog(oss_frame, u'删除Bucket[' + unicodise(selected_bucket) + u']失败! 请确定该Bucket中没有文件和文件夹.',
                                       u'错误提示',
                                       wx.OK | wx.ICON_INFORMATION
                                       #wx.YES_NO 
                                       # | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                       )
                dlg.ShowModal()
                dlg.Destroy()
                if log.closed:
                    log = open('log.txt', 'a+')
                log.write((u'[' + unicodise(time.asctime()) + u']  删除Bucket['+selected_bucket+u']失败,错误提示:请确定该Bucket中没有文件和文件夹。  [Failure]\n').encode('utf-8'))
                log.flush()
                ## update operation_listctrl
                operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  删除Bucket['+selected_bucket+u']失败,错误提示:请确定该Bucket中没有文件和文件夹。  [Failure]\n'])
    selected_bucket = ""

def OnClickEditACL(event):
    global selected_bucket
    global edit_bucket_acl_frame
    if not selected_bucket:
        dlg = wx.MessageDialog(oss_frame, u'请选中一个Bucket!',
                               u'提示信息',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    else:
        cur_acl = get_bucket_acl(oss, selected_bucket).grant
        for i in range(len(acl_options)):
            if acl_values[i] == cur_acl:
                cur_option = acl_options[i]       
        if not edit_bucket_acl_frame:
            edit_bucket_acl_frame = wx.Frame(parent=oss_frame, title=u"设置ACL", 
                                             pos=(550, 250), size=(240, 180), 
                                             style=wx.DEFAULT_FRAME_STYLE
                                             )
        edit_bucket_acl_panel = wx.Panel(edit_bucket_acl_frame, -1)
        l1 = wx.StaticText(edit_bucket_acl_panel, -1, u"    当前访问权限:")
        t1 = wx.StaticText(edit_bucket_acl_panel, -1, cur_option)
        #edit_bucket_acl_panel.Bind(wx.EVT_TEXT, BucNameEvtText, t1)
        l2 = wx.StaticText(edit_bucket_acl_panel, -1, u"    设置访问权限:")
        acl_choice = wx.Choice(edit_bucket_acl_panel, -1, size=(80, -1), 
                                choices=acl_options)
        edit_bucket_acl_panel.Bind(wx.EVT_CHOICE, EditedBucACLEvtText, acl_choice)
        edit_bucket_acl_ok_btn = wx.Button(edit_bucket_acl_panel, -1, label=u"确定", size=(80,28))
        edit_bucket_acl_cancel_btn = wx.Button(edit_bucket_acl_panel, -1, label=u"取消", size=(80,28))
        edit_bucket_acl_panel.Bind(wx.EVT_BUTTON, OnEditAclOK, edit_bucket_acl_ok_btn)
        edit_bucket_acl_panel.Bind(wx.EVT_BUTTON, OnEditAclCancel, edit_bucket_acl_cancel_btn)

        new_bucket_sizer1 = wx.FlexGridSizer(cols=3, hgap=30, vgap=10)
        new_bucket_sizer1.AddMany([ l1, t1, (0,0),
                                    l2, acl_choice, (0,0)
                                    ])
        new_bucket_sizer2 = wx.FlexGridSizer(cols=3, hgap=20, vgap=0)
        new_bucket_sizer2.AddMany([(0,0), edit_bucket_acl_ok_btn, edit_bucket_acl_cancel_btn
                                    ])
        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(new_bucket_sizer1, 1.9, wx.ALL, 5)
        border.Add(new_bucket_sizer2, 1, wx.ALL, 5)
        edit_bucket_acl_panel.SetSizer(border)
        edit_bucket_acl_panel.SetAutoLayout(True)
        edit_bucket_acl_frame.Show()

def EditedBucACLEvtText(event):
    global edit_bucket_acl_option
    edit_bucket_acl_option = event.GetString()
    edit_bucket_acl_option = unicodise(edit_bucket_acl_option)
    
def OnEditAclOK(event):
    global selected_bucket
    global edit_bucket_acl_option
    global edit_bucket_acl_frame
    global operation_listctrl
    global log
    if not edit_bucket_acl_option:
        dlg = wx.MessageDialog(oss_frame, u'请选中一个ACL值!',
                               u'提示信息',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    else:
        if oss:
            if edit_bucket_acl_option == acl_options[1]:
                new_buc_res = put_bucket(oss, selected_bucket, acl_values[1], headers={})
            elif edit_bucket_acl_option == acl_options[2]:
                new_buc_res = put_bucket(oss, selected_bucket, acl_values[2], headers={})
            else:
                new_buc_res = put_bucket(oss, selected_bucket, acl_values[0], headers={})
            if new_buc_res:
                dlg = wx.MessageDialog(edit_bucket_acl_frame, u'Bucket [ '+ unicodise(selected_bucket) +u' ] ACL值修改成功!',
                            u'提示信息',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
                dlg.ShowModal()
                dlg.Destroy()
                if log.closed:
                    log = open('log.txt', 'a+')
                log.write((u'[' + unicodise(time.asctime()) + u']  修改Bucket [ ' + unicodise(selected_bucket) + u' ] ACL值成功。  [OK]\n').encode('utf-8'))
                log.flush()
                edit_bucket_acl_frame.Close()
                ## update operation_listctrl
                operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  修改Bucket [ ' + unicodise(selected_bucket) + u' ] ACL值成功。  [OK]\n'])
            else:
                dlg = wx.MessageDialog(edit_bucket_acl_frame, u'Bucket [ '+ unicodise(selected_bucket) +u' ] ACL值修改失败!',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
                dlg.ShowModal()
                dlg.Destroy()
                if log.closed:
                    log = open('log.txt', 'a+')
                log.write((u'[' + unicodise(time.asctime()) + u']  修改Bucket [ ' + unicodise(selected_bucket) + u' ] ACL值失败。  [Failure]\n').encode('utf-8'))
                log.flush()
                edit_bucket_acl_frame.Close()
                ## update operation_listctrl
                operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  修改Bucket [ ' + unicodise(selected_bucket) + u' ] ACL值失败。  [Failure]\n'])
        else:
            dlg = wx.MessageDialog(edit_bucket_acl_frame, u'OSS用户验证信息错误!',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
            dlg.ShowModal()
            dlg.Destroy()
            if log.closed:
                log = open('log.txt', 'a+')
            log.write((u'[' + unicodise(time.asctime()) + u']  修改Bucket [ ' + unicodise(selected_bucket) + u' ] ACL值失败，错误提示：OSS验证信息失败。  [Failure]\n').encode('utf-8'))
            log.flush()
            edit_bucket_acl_frame.Close()
            ## update operation_listctrl
            operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  修改Bucket [ ' + unicodise(selected_bucket) + u' ] ACL值失败，错误提示：OSS验证信息失败。  [Failure]\n'])
    
def OnEditAclCancel(event):
    global edit_bucket_acl_frame
    edit_bucket_acl_frame.Close()
def OnClickRefresh(event):
    refresh_pages()


def OnSearchType(event):
    global search_type
    search_type = event.GetString()
    search_type = unicodise(search_type)

def DoSearch(text):
    global search_type
    global bucket_names
    global all_data
    global search_result_listcrl
    global oss_notebook
    search_result = {}
    if search_type == search_types[1]:
        pat = None
        pass
    elif search_type == search_types[2]:
        pat = None
        pass
    elif search_type == search_types[3]:
        pat = None
        pass
    else:
        text = unicodise(text)
        pat = re.compile(text, re.UNICODE)
    for bucket in bucket_names:
        search_result[bucket] = []
        for file_name in all_data[bucket]:
            file_name = unicodise(file_name)
            srch_res = pat.search(file_name)
            if srch_res:
                search_result[bucket].append(file_name)

    result_count = 0
    search_result_listcrl.ClearAll()
    search_result_listcrl.InsertColumn(0, u'搜索结果')
    search_result_listcrl.SetColumnWidth(0, 800)
    for bucket in bucket_names:
        for file_name in search_result[bucket]:
            search_result_listcrl.InsertStringItem(result_count, unicodise(bucket) + u": " + unicodise(file_name))
            result_count += 1
    oss_notebook.ChangeSelection(4)  

    

oss_toolbar.AddLabelTool(10, u"NewBucket", new_bucket_bmp, shortHelp=u"新建Bucket", longHelp=u"新建一个Buckt。")
oss_toolbar.Bind(wx.EVT_TOOL, OnClickNewBucket, id=10)
oss_toolbar.AddSeparator()

oss_toolbar.AddLabelTool(20, u"Delete", delete_bmp, shortHelp=u"删除Bucket", longHelp=u"选中Bucket点击按钮以删除Bucket.")
oss_toolbar.Bind(wx.EVT_TOOL, OnClickDeleteBucket, id=20)
oss_toolbar.AddSeparator()

oss_toolbar.AddLabelTool(30, u"ACL", lock_bmp, shortHelp=u"访问权限设置", longHelp=u"设置Bucket访问权限")
oss_toolbar.Bind(wx.EVT_TOOL, OnClickEditACL, id=30)
oss_toolbar.AddSeparator()


#oss_toolbar.AddLabelTool(40, "link", link_bmp, shortHelp=u"外链管理", longHelp=u"Bucket外链设置")
#oss_toolbar.Bind(wx.EVT_TOOL, OnClickRefresh, id=40)
#oss_toolbar.AddSeparator()

oss_toolbar.AddLabelTool(50, u"Refresh", refresh_bmp, shortHelp=u"刷新", longHelp=u"刷新数据")
oss_toolbar.Bind(wx.EVT_TOOL, OnClickRefresh, id=50)
oss_toolbar.AddSeparator()


        
oss_toolbar.AddSeparator()
oss_toolbar.AddSeparator()
oss_toolbar.AddSeparator()

oss_toolbar.AddControl(
    wx.ComboBox(
        oss_toolbar, 90, u"选择搜索方式", choices=search_types,
        size=(120,-1), style=wx.CB_DROPDOWN
        ))
oss_toolbar.Bind(wx.EVT_COMBOBOX, OnSearchType, id=90)
        
search = OSSSearchCtrl(oss_toolbar, size=(300,-1), doSearch=DoSearch)
oss_toolbar.AddControl(search)
oss_toolbar.Realize()
#ToolBar end        

#---------------------------------------------------------------------------
      
#MenuBar
oss_menubar = wx.MenuBar()
menu1 = wx.Menu()
menu1.Append(101, u"&登录", u"登录账户")
menu1.AppendSeparator()
menu1.Append(102, u"&退出", u"退出并关闭窗口")
# Add menu to the menu bar
oss_menubar.Append(menu1, u"&账户")

menu2 = wx.Menu()
menu2.Append(201, u"&新建Bucket", u"新建Bucket")
menu2.Append(202, u"&删除Bucket", u"删除Bucket")
menu2.Append(203, u"&修改ACL", u"修改Bucket ACL")
menu2.AppendSeparator()
menu2.Append(204, u"&下载Bucket", u"下载Bucket所有文件到本地")
# a submenu in the 2nd menu
#submenu = wx.Menu()
#submenu.Append(2051,"...")
#submenu.Append(2052,"...")
#submenu.Append(2053,"...")
#menu2.AppendMenu(205, "...", submenu)
# Append 2nd menu
oss_menubar.Append(menu2, u"&Bucket")

#menu3 = wx.Menu()
#menu3.Append(301, u"&下载文件", u"下载文件到本地")
#menu3.Append(302, u"&上传文件", u"上传文件到当前路径")
#menu3.Append(303, u"&删除文件", u"删除文件")
#menu3.AppendSeparator()
#menu3.Append(304, u"&新建文件夹", u"在当前路径新建文件夹")
#oss_menubar.Append(menu3, u"&文件")

menu4 = wx.Menu()
menu4.Append(401, u"&下载所有文件", u"下载所有文件到本地")
submenu = wx.Menu()
submenu.Append(4021,u"从OSS同步到Mysql数据库")
submenu.Append(4022,u"从OSS同步到MongoDB数据库")
submenu.Append(4023,u"从OSS同步到HBase数据库")
menu4.AppendMenu(402, u"同步到数据库", submenu)
menu4.AppendSeparator()
menu4.Append(403, u"&统计分析", u"OSS使用情况分析")
menu4.AppendSeparator()
menu4.Append(404, u"&导出日志文件", u"将log文件到处到本地，并且清除之前的日志文件")
oss_menubar.Append(menu4, u"&工具")

menu5 = wx.Menu()
menu5.Append(501, u"&在线帮助", u"在线帮助")
menu5.Append(502, u"&联系我们", u"联系我们")
menu5.Append(503, u"&检查更新", u"检查更新")
menu5.AppendSeparator()
menu5.Append(504, u"&关于", u"关于OSS Browser 1.2.1")
oss_menubar.Append(menu5, u"&帮助")

oss_frame.SetMenuBar(oss_menubar)      


def OnMenuBar(event):
    pass

def OnClickLogin(event):
    global oss_frame
    go_login()
    oss_frame.Disable()

def OnClickExit(event):
    global oss_frame
    global log
    oss_frame.DestroyChildren()
    oss_frame.Destroy()
    if log.closed:
        log = open('log.txt', 'a+')   
    log.write((u'[' + unicodise(time.asctime()) + u']  Logged out.  [OK]\n').encode('utf-8'))
    log.flush()
    sys.exit()

def OnDownloadBucket(event):
    global bucket_names
    global oss_frame
    global all_data
    global oss
    global log
    global selected_bucket
    global operation_listctrl
    if not selected_bucket:
        dlg = wx.MessageDialog(oss_frame, u'请选中一个Bucket!',
                               u'提示信息',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    else:
        dlg = wx.DirDialog(oss_frame, u"Choose a directory:",
                  style=wx.DD_DEFAULT_STYLE
                   #| wx.DD_DIR_MUST_EXIST
                    #| wx.DD_CHANGE_DIR
                   )
        if dlg.ShowModal() == wx.ID_OK:
            store_path = dlg.GetPath()
            store_path = unicodise(store_path)
            if not os.path.exists(store_path + '\\' + unicodise(selected_bucket) + '\\'):
                os.makedirs(store_path + '\\' + selected_bucket + '\\')
            for obj in all_data[selected_bucket]:
                obj = unicodise(obj)
                if obj[-1] == '/':
                    temp = obj.split('/')
                    obj = '\\'.join(temp)
                    if not os.path.exists(store_path + '\\' + unicodise(selected_bucket) + '\\' + obj):
                        os.makedirs(store_path + '\\' + unicodise(selected_bucket) + '\\' + obj)
            for obj1 in all_data[selected_bucket]:
                obj1 = unicodise(obj1)
                if obj1[-1] != '/':
                    res = get_object_to_file(oss, selected_bucket, obj1, store_path + u'/' + unicodise(selected_bucket)  + u'/' + obj1, headers={})
                    if res:
                        if log.closed:
                            log = open('log.txt', 'a+') 
                        log.write((u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(selected_bucket) + u'\\' + obj1) + u'成功。  [OK]\n').encode('utf-8'))
                        ## update operation_listctrl
                        operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(selected_bucket) + u'\\' + obj1) + u'成功。  [OK]\n'])
                    else:
                        if log.closed:
                            log = open('log.txt', 'a+') 
                        log.write((u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(selected_bucket) + u'\\' + obj1) + u'失败。  [Failure]\n').encode('utf-8'))
                        ## update operation_listctrl
                        operation_listctrl.Append([u'[' + time.asctime() + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(selected_bucket) + u'\\' + obj1) + u'失败。  [Failure]\n'])
   
def OnDownloadAll(event):
    global bucket_names
    global oss_frame
    global all_data
    global oss
    global log
    global operation_listctrl
    if not oss:
        dlg = wx.MessageDialog(oss_frame, u'请先登录!',
                               u'提示信息',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
    else:
        dlg = wx.DirDialog(oss_frame, u"Choose a directory:",
                  style=wx.DD_DEFAULT_STYLE
                   #| wx.DD_DIR_MUST_EXIST
                    #| wx.DD_CHANGE_DIR
                   )
        if dlg.ShowModal() == wx.ID_OK:
            store_path = dlg.GetPath()
            store_path = unicodise(store_path)
            for bucket in bucket_names:
                if not os.path.exists(store_path + '\\' + unicodise(bucket) + '\\'):
                    os.makedirs(store_path + '\\' + unicodise(bucket) + '\\')
                for obj in all_data[bucket]:
                    obj = unicodise(obj)
                    if obj[-1] == '/':
                        temp = obj.split('/')
                        obj = '\\'.join(temp)
                        if not os.path.exists(store_path + '\\' + unicodise(bucket) + '\\' + obj):
                            os.makedirs(store_path + '\\' + unicodise(bucket) + '\\' + obj)
            for bucket1 in bucket_names:
                for obj1 in all_data[bucket1]:
                    obj1 = unicodise(obj1)
                    if obj1[-1] != '/':
                        res = get_object_to_file(oss, bucket1, obj1, store_path + u'/' + unicodise(bucket1)  + u'/' + obj1, headers={})
                        if res:
                            if log.closed:
                                log = open('log.txt', 'a+') 
                            log.write((u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(bucket1) + u'\\' + obj1) + u'成功。  [OK]\n').encode('utf-8'))
                            ## update operation_listctrl
                            operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(bucket1) + u'\\' + obj1) + u'成功。  [OK]\n'])
                        else:
                            if log.closed:
                                log = open('log.txt', 'a+') 
                            log.write((u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(bucket1) + u'\\' + obj1) + u'失败。  [Failure]\n').encode('utf-8'))
                            ## update operation_listctrl
                            operation_listctrl.Append([u'[' + unicodise(time.asctime()) + u']  下载文件:' + obj1 + u'到' + (store_path + u'\\' + unicodise(bucket1) + u'\\' + obj1) + u'失败。  [Failure]\n'])
                            
        dlg.Destroy()


def OnAbout(event):
        info = wx.AboutDialogInfo()
        info.Name = u"OSSBrowser"
        info.Version = u"1.2.1"
        info.Copyright = u"Copyright(C) 2012 OSSTools Software. All Rights Reserved"
        info.Licence = u" GNU Public License v2"
        info.Icon = wx.Icon("..\\res\\about_icon1.png", wx.BITMAP_TYPE_PNG)
        info.Description = wordwrap(
            u"    OSSBrowser is a freeware client for Aliyun OSS Service. "+ \
            u"Aliyun OSS providers a simple web services interface that "+ \
            u"can be used to store an retrieve any amount of data, at any "+ \
            u"time, from anywhere on the web",
            500, wx.ClientDC(oss_frame))
        info.WebSite = ("http://www.aliyun.com/", "About Aliyun.com")
        info.Developers = [ u" Meilong Huang [imsrch@melory.me]"]
        wx.AboutBox(info)

def OnContactUs(event):
    webbrowser.open("imsrch.tk/about")

def OnOnlineHelp(event):
    webbrowser.open("www.aliyun.com")

# Menu Bar Events
oss_frame.Bind(wx.EVT_MENU, OnClickLogin, id=101)
oss_frame.Bind(wx.EVT_MENU, OnClickExit, id=102)
oss_frame.Bind(wx.EVT_MENU, OnDownloadAll, id=401)
oss_frame.Bind(wx.EVT_MENU, OnClickNewBucket, id=201)
oss_frame.Bind(wx.EVT_MENU, OnClickDeleteBucket, id=202)
oss_frame.Bind(wx.EVT_MENU, OnClickEditACL, id=203)
oss_frame.Bind(wx.EVT_MENU, OnDownloadBucket, id=204)
oss_frame.Bind(wx.EVT_MENU, OnAbout, id=504)
oss_frame.Bind(wx.EVT_MENU, OnOnlineHelp, id=501)
oss_frame.Bind(wx.EVT_MENU, OnContactUs, id=502)

#oss_frame.Bind(wx.EVT_TOOL, OnMenuBar, id=11)

#MenuBar end

oss_frame.Show()
app.MainLoop()


