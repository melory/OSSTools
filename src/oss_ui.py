#!/usr/bin/env python
# -*- coding: utf-8 -*-
## ossbrowser
## Author: melory
## Email:imsrch@melory.me
## License: GPL Version 2


import wx
import time
from ossvue_utils import *
import locale

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


class OSSFrame(wx.Frame):
    def __init__(self, parent, size, pos, 
                 style, title, log
                 #new_bucket_frame, edit_bucket_acl_frame
                 ):
        wx.Frame.__init__(self, parent=parent, size=size, 
                          pos=pos, style=style, title=title)
        self.log = log
        self.icon = wx.Icon("..\\res\\icon.png", wx.BITMAP_TYPE_PNG)
        self.SetIcon(self.icon) 
        #self.new_bucket_frame = new_bucket_frame
        #self.edit_bucket_acl_frame = edit_bucket_acl_frame
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def OnClose(self, event):
        if self.log.closed:
            self.log = open('log.txt', 'a+')
        self.log.write((u'[' + unicodise(time.asctime()) + u']  Logged out.  [OK]\n').encode('utf-8'))
        self.log.flush()
        self.log.close()
        #self.new_bucket_frame.Destroy()
        #self.edit_bucket_acl_frame.Destroy()
        self.DestroyChildren()
        self.Destroy()

class OSSStatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)
        self.SetFieldsCount(2)
        self.SetStatusWidths([-3, -1])
        self.timer = wx.PyTimer(self.notify)
        self.timer.Start(1000)
        self.notify()
    
    def notify(self):
        t = time.localtime(time.time())
        st = time.strftime("%d-%b-%Y   %I:%M:%S", t)
        self.SetStatusText(st, 1)

class OSSSearchCtrl(wx.SearchCtrl):
    maxSearches = 5
    
    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.doSearch = doSearch
        self.searches = []

    def OnTextEntered(self, evt):
        text = self.GetValue()
        text = unicodise(text)
        if self.doSearch(text):
            self.searches.append(text)
            if len(self.searches) > self.maxSearches:
                del self.searches[0]
            self.SetMenu(self.MakeMenu())            
        self.SetValue(u"")

    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        text = unicodise(text)
        self.doSearch(text)
        
    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, u"Recent Searches")
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            menu.Append(1+idx, txt)
        return menu

class OssFileListCtrl(wx.ListCtrl):
    def __init__(self, parent, id, style, records, column_names, oss, bucket_name, log, operation_list):
        wx.ListCtrl.__init__(self, parent=parent, id=id, style=style)
        self.records = records
        self.column_names = column_names
        self.oss = oss
        self.bucket_name = bucket_name
        ## log 
        self.log = log
        ## operation_listctrl in oss_notebook
        self.operation_list = operation_list
        self.cur_paths = []
        

        row = len(self.records)
        column = len(column_names)
        il = wx.ImageList(16, 16, True)
        for i in range(row):
            if self.records[i][0][-1] == '/':
                il_max = il.Add(wx.Bitmap("..\\res\\folder.png", wx.BITMAP_TYPE_PNG))
            else:
                il_max = il.Add(wx.Bitmap("..\\res\\file.png", wx.BITMAP_TYPE_PNG))
        self.AssignImageList(il, wx.IMAGE_LIST_SMALL)
        for i in range(column):
            self.InsertColumn(i, unicodise(column_names[i]))
            self.SetColumnWidth(i, 100)
        self.SetColumnWidth(0, 120)
        self.SetColumnWidth(1, 130)
        self.SetColumnWidth(2, 240)
        self.SetColumnWidth(3, 115)
        
        for i in range(row):
            self.InsertImageStringItem(i, unicodise(self.records[i][0]), i)
            for j in range(column-1):
                self.SetStringItem(i, j+1, unicodise(self.records[i][j+1]))
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRClicked)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnContextMenu)

    def refresh(self):
        self.ClearAll()
        cur_prefix = ''.join(self.cur_paths)
        res = get_bucket_objects(self.oss, self.bucket_name, prefix = cur_prefix)
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
                for i in range(len(self.column_names) - 1):
                    rcd.append(u'')
                if len(rcd):rcds.append(rcd)
        for file_item in file_list:
            file_item_t = list(file_item)
            time_parts = file_item_t[1].split("T")
            file_item_t[1] = time_parts[0] +" " + time_parts[1][0:8]
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
            
            if file_item_t[0] == cur_prefix:
                for i in range(len(self.column_names) - 1):
                    file_item_t[i + 1] = u''
                rcds.insert(0, file_item_t)
            else:
                rcds.append(file_item_t)

        
        for i in range(len(rcds)):
            if rcds[i][0] == cur_prefix:
                rcds[i][0] = "../"
            else:
                rcds[i][0] = rcds[i][0][len(cur_prefix):len(rcds[i][0])]
             
        row = len(rcds)
        column = len(self.column_names)
        il = wx.ImageList(16, 16, True)
        for i in range(row):
            if rcds[i][0][-1] == '/':
                il_max = il.Add(wx.Bitmap("..\\res\\folder.png", wx.BITMAP_TYPE_PNG))
            else:
                il_max = il.Add(wx.Bitmap("..\\res\\file.png", wx.BITMAP_TYPE_PNG))
        self.AssignImageList(il, wx.IMAGE_LIST_SMALL)
        for i in range(column):
            self.InsertColumn(i, unicodise(self.column_names[i]))
            self.SetColumnWidth(i, 100)
        self.SetColumnWidth(0, 120)
        self.SetColumnWidth(1, 130)
        self.SetColumnWidth(2, 240)
        self.SetColumnWidth(3, 115)
    
        for i in range(row):
            self.InsertImageStringItem(i, unicodise(rcds[i][0]), i)
            for j in range(column-1):
                self.SetStringItem(i, j+1, unicodise(rcds[i][j+1]))    
   
    
    def go_parent_dir(self):
        self.cur_paths.pop()
        self.refresh()
  
    
    
    def go_into_dir(self):
        self.cur_paths.append(unicodise(self.itemtext))
        self.refresh()
    
    
    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        self.itemtext = unicodise(self.GetItemText(self.currentItem))
        if self.itemtext == "../":
            self.go_parent_dir()
        elif self.itemtext[-1] == '/':
            self.go_into_dir()                 
        else:
            self.OnPopupDownloadFile(None)
    

    def OnItemSelected(self, event):
        pass
        

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return unicodise(item.GetText())

    def OnItemDeselected(self, evt):
        pass


    def OnContextMenu(self, event):
        self.currentItem = event.m_itemIndex
        self.itemtext = self.GetItemText(self.currentItem)
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
        if self.itemtext[-1] == '/' and self.itemtext != '../':
            self.Bind(wx.EVT_MENU, self.OnPopupOpenFolder, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupDownloadFolder, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupDeleteFolder, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnPopupUploadToFolder, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnPopupPropertyFolder, id=self.popupID5)
            # make a menu
            menu = wx.Menu()
            menu.Append(self.popupID1, u"打开文件夹")
            menu.Append(self.popupID2, u"下载文件夹")
            menu.Append(self.popupID3, u"删除文件夹")
            menu.Append(self.popupID4, u"上传文件到文件夹")
            menu.AppendSeparator()
            menu.Append(self.popupID5, u"文件夹属性")
            self.PopupMenu(menu)
            menu.Destroy()

        elif self.itemtext != '../':
            self.Bind(wx.EVT_MENU, self.OnPopupDownloadFile, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupDeleteFile, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupPropertyFile, id=self.popupID3)

            # make a menu
            menu = wx.Menu()
            menu.Append(self.popupID1, u"下载文件")
            menu.Append(self.popupID2, u"删除文件")
            menu.AppendSeparator()
            menu.Append(self.popupID3, u"文件属性")
            self.PopupMenu(menu)
            menu.Destroy()
        

    def OnPopupOpenFolder(self, event):
        self.go_into_dir()

        
    def OnPopupDownloadFolder(self, event):
        pass

    def OnPopupDeleteFolder(self, event):
        cur_prefix = ''.join(self.cur_paths)
        dlg = wx.MessageDialog(self, u'确定删除文件夹：'+unicodise(''.join(self.cur_paths))+unicodise(self.itemtext)+u'及其中所有文件?',
                               u'提示信息',
                               wx.YES_NO
                               )
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == 5103:
            res = get_bucket_objects(self.oss, self.bucket_name, 
                                     prefix = unicodise(cur_prefix)+unicodise(self.itemtext), 
                                    delimiter="/")
            if res:
                (file_list, common_list) = res.list()
                for file_info in file_list:
                    res1 = delete_object(self.oss, self.bucket_name, file_info[0])
                self.refresh()
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  删除文件夹:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'成功。  [OK]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  删除文件夹:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'成功。  [OK]\n'])
            else:
                dlg = wx.MessageDialog(self, u'确定删除文件夹：'+unicodise(''.join(self.cur_paths))+unicodise(self.itemtext)+u'失败，请检查网络状况。',
                               u'错误提示',
                               wx.OK | wx.ICON_INFORMATION
                               )
                result = dlg.ShowModal()
                dlg.Destroy()
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  删除文件夹:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'失败。  [OK]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  删除文件夹:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'失败。  [OK]\n'])
        else:
            pass
        


    def OnPopupPropertyFolder(self, event):
        pass
        
    def OnPopupUploadToFolder(self, event):
        pass

    def OnPopupOpenFile(self, event):
        pass
        
    def OnPopupDownloadFile(self, event):
        wildcard = "Python source (*.py)|*.py|"     \
            "Compiled Python (*.pyc)|*.pyc|" \
            "JPEG files (*.jpg)|*.jpg|"    \
            "AVI file (*.avi)|*.avi|"        \
            "TXT file (*.txt)|*.txt|"        \
            "All files (*.*)|*.*"
           
        dlg = wx.FileDialog(self, message=u"文件另存为 ...", defaultDir=os.getcwd(), 
                            defaultFile="", wildcard=wildcard, style=wx.SAVE
                            )
        dlg.SetFilterIndex(2)


        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            headers = {}
            res = get_object_to_file(self.oss, self.bucket_name, unicodise(''.join(self.cur_paths))+unicodise(self.itemtext), path, headers)
            if res:
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  下载文件:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'成功。  [OK]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  下载文件:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'成功。  [OK]\n'])
            else:
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  下载文件:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'失败。  [Failure]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  下载文件:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'失败。  [Failure]\n'])
        dlg.Destroy()

        
    def OnPopupDeleteFile(self, event):
        dlg = wx.MessageDialog(self, u'确定删除文件：'+unicodise(self.itemtext)+u'?',
                               u'提示信息',
                               wx.YES_NO
                               )
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == 5103:
            res = delete_object(self.oss, self.bucket_name, unicodise(''.join(self.cur_paths))+unicodise(self.itemtext), headers = {})
            if res:
                self.DeleteItem(self.currentItem)
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  删除文件:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'成功。  [OK]\n').encode('utf-8'))
                self.log.flush()
                self.refresh()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  删除文件:' + unicodise(''.join(self.cur_paths))+unicodise(self.itemtext) + u'成功。  [OK]\n'])
            else:
                dlg = wx.MessageDialog(self, u'删除文件：'+unicodise(''.join(self.cur_paths))+unicodise(self.itemtext)+u'失败！',
                                       u'提示信息',
                                       wx.OK | wx.ICON_INFORMATION
                                       )
                dlg.ShowModal()
                dlg.Destroy()
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  删除文件:' + unicodise(self.itemtext) + u'失败。  [Failure]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  删除文件:' + unicodise(self.itemtext) + u'失败。  [Failure]\n'])

        
        

    def OnPopupPropertyFile(self, event):
        pass
        
    def OnColRClicked(self, event):
        if not hasattr(self, "popupID11"):
            self.popupID11 = wx.NewId()
            self.popupID12 = wx.NewId()
            self.popupID13 = wx.NewId()

        self.Bind(wx.EVT_MENU, self.OnUploadObject, id=self.popupID11)
        self.Bind(wx.EVT_MENU, self.OnMakeDir, id=self.popupID12)
        self.Bind(wx.EVT_MENU, self.OnGoParent, id=self.popupID13)

        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupID11, u"上传文件到该路径")
        menu.Append(self.popupID12, u"在该路径创建文件夹")
        if self.cur_paths:
            menu.AppendSeparator()
            menu.Append(self.popupID13, u"返回上一层目录")
        self.PopupMenu(menu)
        menu.Destroy()
        
        
    def OnUploadObject(self, event):
        wildcard = "Python source (*.py)|*.py|"     \
            "Compiled Python (*.pyc)|*.pyc|" \
            "JPEG files (*.jpg)|*.jpg|"    \
            "AVI file (*.avi)|*.avi|"        \
            "TXT file (*.txt)|*.txt|"        \
            "All files (*.*)|*.*"
        dlg = wx.FileDialog(self, message=u"选择文件", defaultDir=os.getcwd(), 
                            defaultFile="", wildcard=wildcard, 
                            style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                            )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = unicodise(path)
            p_list = path.split('\\')
            res = put_object(self.oss, path, self.bucket_name, unicodise(''.join(self.cur_paths))+unicodise(p_list[-1]), headers={})
            if res:
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  上传文件:' + path + u'成功。  [OK]\n').encode('utf-8'))
                self.log.flush()
                self.refresh()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  上传文件:' + path + u'成功。  [OK]\n'])
            else:
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  上传文件:' + path + u'失败。  [Failure]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  上传文件:' + path + u'失败。  [Failure]\n'])
        dlg.Destroy()
        

    def OnMakeDir(self, event):
        dlg = wx.TextEntryDialog(self, 
                                 u'“文件夹”命名规范:\n    \
                                 » 1. 只能包含字母，数字，中文，下划线（_）和短横线（-）,小数点（.）\n    \
                                 » 2. 只能以字母、数字或者中文开头\n    \
                                 » 3. 文件夹的长度限制在1-254之间\n    \
                                 » 4. Object总长度必须在1-1023之间',
                u'创建文件夹', u'请输入文件夹名称')
        if dlg.ShowModal() == wx.ID_OK:
            folder_name = unicodise(dlg.GetValue())
            cur_prefix = unicodise(''.join(self.cur_paths))
            mkdir_res = put_object_from_string(self.oss, self.bucket_name, cur_prefix+folder_name+'/', cur_prefix+folder_name+'/')
            if mkdir_res:
                dlg = wx.MessageDialog(self, u'文件夹创建成功!',
                            u'提示信息',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
                dlg.ShowModal()
                dlg.Destroy()
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  创建文件夹:' + folder_name + u'成功。  [OK]\n').encode('utf-8'))
                self.log.flush()
                self.refresh()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  创建文件夹:' + folder_name + u'成功。  [OK]\n'])
            else:
                dlg = wx.MessageDialog(self, u'文件夹创建失败!请检查网络状况.',
                            u'错误提示',
                            wx.OK | wx.ICON_INFORMATION
                            #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                            )
                dlg.ShowModal()
                dlg.Destroy()
                if self.log.closed:
                    self.log = open('log.txt', 'a+')
                self.log.write((u'[' + unicodise(time.asctime()) + u']  创建文件夹:' + folder_name + u'失败。  [Failure]\n').encode('utf-8'))
                self.log.flush()
                self.operation_list.Append([u'[' + unicodise(time.asctime()) + u']  创建文件夹:' + folder_name + u'失败。  [Failure]\n'])
        dlg.Destroy()
    
    def OnGoParent(self, event):
        self.go_parent_dir()
    
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()
        