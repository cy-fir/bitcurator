#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# BitCurator
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# python3 bc_disk_access_v2.py bc_disk_access_v2 --listfiles
#
#################################################################### 
# The basic GUI is designed using PyQT4 Designer. 
# Base .ui file: disk_access_v7.py
# Code manually added to QTreeView and for the functionality of all widgets.
# From the DFXML file, the "filename" attribute is read using 
# fiwalk.fiwalk_using_sax() API. The list of file-paths is stored in 
# the dictionary fiDictList. 
# To store the Tree structure of the directory hierarchy, the QStandardItemModel
# class of the QtPy4's Model/View framework is used:
# http://pyqt.sourceforge.net/Docs/PyQt4/qstandarditemmodel.html#details
#################################################################### 

import os, fiwalk, sys
from PyQt4 import QtCore, QtGui
import subprocess
from subprocess import Popen,PIPE
import threading
import time
import re
from os.path import expanduser

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")

try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## app = QtGui.QApplication(sys.argv)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# init widgets

global g_model
global g_image
global g_dfxmlfile
global isGenDfxmlFile
global g_breakout
global g_parent0_item
global_fw = "null"
#global g_oldstdout
global g_img_oldstdout

class Ui_MainWindow(object):
    progressBar = "null"
    current_image = "null"
    global g_img_oldstdout
    g_img_oldstdout = sys.stdout

    global g_oldstdout
    g_oldstdout = sys.stdout
    sys.stdout = StringIO()

    def setupUi(self, MainWindow):
        # Save the current working directory
        self.cwd = os.getcwd()

        # Set the directory to user's home directory
        os.chdir(os.environ["HOME"])

        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(880, 642)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.DirectoryTree = QtGui.QTreeView(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.DirectoryTree.sizePolicy().hasHeightForWidth())
        self.DirectoryTree.setSizePolicy(sizePolicy)
        self.DirectoryTree.setSizeIncrement(QtCore.QSize(0, 0))
        self.DirectoryTree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        #.#
        self.DirectoryTree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.DirectoryTree.setObjectName(_fromUtf8("DirectoryTree"))
        self.gridLayout.addWidget(self.DirectoryTree, 0, 0, 2, 1)

        #.#
        self.model = QtGui.QStandardItemModel()
        self.DirectoryTree.setModel(self.model)
        self.DirectoryTree.setUniformRowHeights(True)
        global g_model
        g_model = self.model
        g_model.setHorizontalHeaderLabels(['File System: \n  Entries in bold are directories \n  Entries in red are unallocated/deleted files '])
        
        

        self.dockWidget_imginfo = QtGui.QDockWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dockWidget_imginfo.sizePolicy().hasHeightForWidth())
        self.dockWidget_imginfo.setSizePolicy(sizePolicy)
        self.dockWidget_imginfo.setObjectName(_fromUtf8("dockWidget_imginfo"))
        self.dockWidgetContents_imginfo = QtGui.QWidget()
        self.dockWidgetContents_imginfo.setObjectName(_fromUtf8("dockWidgetContents_imginfo"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.dockWidgetContents_imginfo)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.textEdit_imginfo = QtGui.QTextEdit(self.dockWidgetContents_imginfo)
        self.textEdit_imginfo.setObjectName(_fromUtf8("textEdit_imginfo"))
        self.textEdit_imginfo.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.verticalLayout_3.addWidget(self.textEdit_imginfo)
        self.dockWidget_imginfo.setWidget(self.dockWidgetContents_imginfo)
        self.gridLayout.addWidget(self.dockWidget_imginfo, 0, 1, 1, 1)

 
        # Save the state 
        self.byte_array_msg_window = MainWindow.saveState()

        self.dockWidget_msg = QtGui.QDockWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dockWidget_msg.sizePolicy().hasHeightForWidth())
        self.dockWidget_msg.setSizePolicy(sizePolicy)
        self.dockWidget_msg.setMinimumSize(QtCore.QSize(380, 146))
        self.dockWidget_msg.setObjectName(_fromUtf8("dockWidget_msg"))
        self.dockWidgetContents_msg = QtGui.QWidget()
        self.dockWidgetContents_msg.setObjectName(_fromUtf8("dockWidgetContents_msg"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.dockWidgetContents_msg)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.textEdit_msg = QtGui.QTextEdit(self.dockWidgetContents_msg)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textEdit_msg.sizePolicy().hasHeightForWidth())
        self.textEdit_msg.setSizePolicy(sizePolicy)
        self.textEdit_msg.setAutoFillBackground(True)
        self.textEdit_msg.setStyleSheet(_fromUtf8("background-color: rgb(200, 206, 200);\n"
"border-color: rgb(170, 0, 0);"))
        self.textEdit_msg.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.textEdit_msg.setObjectName(_fromUtf8("textEdit_msg"))
        self.verticalLayout_4.addWidget(self.textEdit_msg)

        #.#
        global g_textEdit_msg
        g_textEdit_msg = self.textEdit_msg

        #.#
        #self.progressBar = QtGui.QProgressBar(self.dockWidgetContents_msg)
        self.progressBar = ProgressBar()

        #.#
        global global_fw
        global_fw =  self.progressBar

        #.#
        global global_pb_da
        global_pb_da = self.progressBar
        

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout_4.addWidget(self.progressBar)
        self.dockWidget_msg.setWidget(self.dockWidgetContents_msg)
        self.gridLayout.addWidget(self.dockWidget_msg, 1, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 880, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName(_fromUtf8("menuEdit"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        self.menuRun = QtGui.QMenu(self.menubar)
        self.menuRun.setObjectName(_fromUtf8("menuRun"))
        #self.menuWindow = QtGui.QMenu(self.menubar)
        #self.menuWindow.setObjectName(_fromUtf8("menuWindow"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionSelect_All = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-select-all"))
        self.actionSelect_All.setIcon(icon)
        self.actionSelect_All.setObjectName(_fromUtf8("actionSelect_All"))
        self.actionDeSelect_All = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-clear"))
        self.actionDeSelect_All.setIcon(icon)
        self.actionDeSelect_All.setObjectName(_fromUtf8("actionDeSelect_All"))
        self.actionOpen_disk_image = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-open"))
        self.actionOpen_disk_image.setIcon(icon)
        self.actionOpen_disk_image.setIconVisibleInMenu(False)
        self.actionOpen_disk_image.setObjectName(_fromUtf8("actionOpen_disk_image"))
        self.actionClose_disk_image = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("list-remove"))
        self.actionClose_disk_image.setIcon(icon)
        self.actionClose_disk_image.setObjectName(_fromUtf8("actionClose_disk_image"))
        self.actionAbout_BitCurator_Disk_Access = QtGui.QAction(MainWindow)
        self.actionAbout_BitCurator_Disk_Access.setObjectName(_fromUtf8("actionAbout_BitCurator_Disk_Access"))
        self.actionExport_selected_files = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-send"))
        self.actionExport_selected_files.setIcon(icon)
        self.actionExport_selected_files.setObjectName(_fromUtf8("actionExport_selected_files"))
        self.actionCancel_export = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("process-stop"))
        self.actionCancel_export.setIcon(icon)
        self.actionCancel_export.setObjectName(_fromUtf8("actionCancel_export"))
        self.actionShow_Messages = QtGui.QAction(MainWindow)
        self.actionShow_Messages.setObjectName(_fromUtf8("actionShow_Messages"))
        self.actionShow_Image_Info = QtGui.QAction(MainWindow)
        self.actionShow_Image_Info.setObjectName(_fromUtf8("actionShow_Image_Info"))

        self.actionSelect_Deleted_Files = QtGui.QAction(MainWindow)
        self.actionSelect_Deleted_Files.setObjectName(_fromUtf8("actionSelect_Deleted_Files"))
        self.actionDeSelect_Deleted_Files = QtGui.QAction(MainWindow)
        self.actionDeSelect_Deleted_Files.setObjectName(_fromUtf8("actionDeSelect_Deleted_Files"))
        
        self.menuFile.addAction(self.actionOpen_disk_image)
        self.menuFile.addAction(self.actionClose_disk_image)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionSelect_All)
        self.menuEdit.addAction(self.actionDeSelect_All)

        self.menuEdit.addAction(self.actionSelect_Deleted_Files)
        self.menuEdit.addAction(self.actionDeSelect_Deleted_Files)
        

        self.menuHelp.addAction(self.actionAbout_BitCurator_Disk_Access)
        self.menuRun.addAction(self.actionExport_selected_files)
        self.menuRun.addAction(self.actionCancel_export)
        self.menuRun.addSeparator()
        #self.menuWindow.addAction(self.actionShow_Messages)
        #self.menuWindow.addAction(self.actionShow_Image_Info)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuRun.menuAction())
        #self.menubar.addAction(self.menuWindow.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.toolBar.addAction(self.actionOpen_disk_image)
        self.toolBar.addAction(self.actionClose_disk_image)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSelect_All)
        self.toolBar.addAction(self.actionDeSelect_All)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionExport_selected_files)
        self.toolBar.addAction(self.actionCancel_export)
        #self.toolBar.addAction(self.actionShow_Messages)
        #self.toolBar.addAction(self.actionShow_Image_Info)

        # menubar triggers
        self.actionExit.triggered.connect(self.exitMenu)
        self.actionSelect_All.triggered.connect(self.selectAllMenu)
        self.actionDeSelect_All.triggered.connect(self.deSelectAllMenu)
        self.actionSelect_Deleted_Files.triggered.connect(self.selectDeletedFilesMenu)
        self.actionDeSelect_Deleted_Files.triggered.connect(self.deSelectDeletedFilesMenu)

        self.actionOpen_disk_image.triggered.connect(self.openDiskImageMenu)
        self.actionClose_disk_image.triggered.connect(self.closeDiskImageMenu)
        self.actionExport_selected_files.triggered.connect(self.exportFilesMenu)
        self.actionCancel_export.triggered.connect(self.cancelExportMenu)
        self.actionShow_Messages.triggered.connect(self.showMsgsWindowMenu)
        self.actionShow_Image_Info.triggered.connect(self.showImginfoWindowMenu)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    

    def retranslateUi(self, MainWindow):
        ###MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Disk Image Access Interface", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.menuRun.setTitle(_translate("MainWindow", "Run", None))
        #self.menuWindow.setTitle(_translate("MainWindow", "Window", None))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar", None))
        self.dockWidget_msg.setWindowTitle(_translate("MainWindow", "Messages", None))
        self.dockWidget_imginfo.setWindowTitle(_translate("MainWindow", "Image Info", None))
        self.actionExit.setText(_translate("MainWindow", "Exit", None))
        self.actionSelect_All.setText(_translate("MainWindow", "Select All", None))
        self.actionDeSelect_All.setText(_translate("MainWindow", "DeSelect All", None))
        self.actionOpen_disk_image.setText(_translate("MainWindow", "Open disk image", None))
        self.actionOpen_disk_image.setToolTip(_translate("MainWindow", "Open disk image", None))
        self.actionClose_disk_image.setText(_translate("MainWindow", "Close disk image", None))
        self.actionAbout_BitCurator_Disk_Access.setText(_translate("MainWindow", "About BitCurator Disk Access", None))
        self.actionExport_selected_files.setText(_translate("MainWindow", "Export selected files", None))
        self.actionCancel_export.setText(_translate("MainWindow", "Cancel export", None))
        #self.actionShow_Messages.setText(_translate("MainWindow", "Show Messages", None))
        #self.actionShow_Image_Info.setText(_translate("MainWindow", "Show Image Info", None))
        self.actionSelect_Deleted_Files.setText(_translate("MainWindow", "Select Deleted Files", None))
        self.actionDeSelect_Deleted_Files.setText(_translate("MainWindow", "DeSelect Deleted Files", None))
        

    def getExportOutdir(self):
        # Since This directory should not exist, use getSaveFileName
        # to let the user create a new directory.
        export_dialog = QtGui.QFileDialog(caption="Find or create an output directory")
        export_dialog.setFileMode(QtGui.QFileDialog.Directory)
        export_dialog.setOption(QtGui.QFileDialog.ShowDirsOnly)
        result = export_dialog.exec_()
        if result:
            export_outdir = export_dialog.selectedFiles()[0]

            print(">> Output directory selected for file export ", export_outdir)
            global g_oldstdout
            g_textEdit_msg.append( sys.stdout.getvalue() )
            sys.stdout = g_oldstdout
            g_oldstdout = sys.stdout
            sys.stdout = StringIO()
            self.exportOutdirName = export_outdir

            # Save it in global var for use by the thread
            global g_export_outdir
            g_export_outdir = self.exportOutdirName

            if not os.path.exists(self.exportOutdirName):
                os.mkdir(self.exportOutdirName)

        else:
            print(">> Warning! No output directory selected! ")
        return self.exportOutdirName
    

    def exitMenu(self):
        QtCore.QCoreApplication.instance().quit()

    def openDiskImageMenu(self):
        global g_oldstdout
        g_oldstdout = sys.stdout
        sys.stdout = StringIO()
        
        # First delete any existing QTreeView model. Also clear the 
        # dictionary created for any previous image.
        global g_model
        if (g_model):
            g_model.clear()
            BcFileStructure.fiDictList = []

        image_file = QtGui.QFileDialog.getOpenFileName(caption="Select an image file")
        self.current_image = image_file
        print(">> Image file selected: ", image_file)

        # Check if the image exists. 
        if not os.path.exists(image_file):
            print(">> Error! Image {} does not exist: ".format(image_file))
            g_textEdit_msg.append( sys.stdout.getvalue() )
            sys.stdout = g_oldstdout
            return
        
        g_textEdit_msg.append( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

        self.imginfo_oldstdout = sys.stdout
        sys.stdout = StringIO()

        # If aff or ewf images, run the info commands
        mod_image_name = re.escape(image_file)
        if image_file.endswith(".E01") or image_file.endswith(".e01"):
            os.system('echo Image Name: ' + image_file + '>/tmp/tmpe01infofile')
            os.system('ewfinfo ' + mod_image_name + '>>/tmp/tmpe01infofile')
            with open("/tmp/tmpe01infofile", 'r') as tmpfile:
                print(tmpfile.read())

            tmpfile.close()
            os.system('rm /tmp/tmpe01infofile')

        elif image_file.endswith(".aff") or image_file.endswith(".AFF"):
            #os.system('echo Image Name: ' + image_file + '>/tmp/tmpe01infofile')
            os.system('affinfo ' + mod_image_name + '>/tmp/tmpe01infofile')
            with open("/tmp/tmpe01infofile", 'r') as tmpfile:
                print(tmpfile.read())

            tmpfile.close()
            os.system('rm /tmp/tmpe01infofile')
        else:
            print(">>> No image information found")

        self.textEdit_imginfo.append( sys.stdout.getvalue() )
        sys.stdout = self.imginfo_oldstdout

        self.imginfo_oldstdout = sys.stdout
        sys.stdout = StringIO()

        # Image is selected. First Generte the dfxml file using Fiwalk, 
        # in a hidden directory .bcfa, in the user's home directory
        dfxmlpath = expanduser("~") + '/.bcfa'
        if not os.path.exists(dfxmlpath):
            os.mkdir(dfxmlpath)

        image_name = os.path.basename(image_file)
        dfxmlfile = dfxmlpath + '/' + image_name + '_dfxml.xml'

        print(">> Generating DFXML file  ", dfxmlfile)
        self.textEdit_msg.append( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

        g_oldstdout = sys.stdout
        sys.stdout = StringIO()

        # First check if the file image exists
        if not os.path.exists(image_file):
            print(">> Error. Image {} does not exist".format(image_file))
            return
    
        if os.path.exists(dfxmlfile):
            os.system("rm " + dfxmlfile)

        cmd = ['fiwalk', '-z', '-g', '-X', dfxmlfile, image_file]
        ## print(" >>D: Generating XML File ", dfxmlfile)
        ## print(">>D: Invoking command for Fiwalk = ", cmd)
        self.textEdit_msg.append( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout
        g_oldstdout = sys.stdout
        sys.stdout = StringIO()

        thread1 = bcfaThread_fw(cmd, image_file, dfxmlfile)

        # Save the thread handle for later use in cancel task.
        global g_thread1_fw
        g_thread1_fw = thread1

        thread2 = guiThread("fiwalk")

        thread2.start()
        thread1.start()
        
    def closeDiskImageMenu(self):
        print(">> Closing image ", self.current_image)

        BcFileStructure.bcDeleteModel(self, self.current_image)
        self.current_image = "null"

        self.textEdit_msg.setText( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

        self.textEdit_imginfo.clear()
        return

    def selectAllMenu(self):
        BcFileStructure.bcOperateOnFiles(BcFileStructure, 1, None)
        
    def deSelectAllMenu(self):
        BcFileStructure.bcOperateOnFiles(BcFileStructure, 0, None)

    def selectDeletedFilesMenu(self):
        self.textEdit_msg.setText( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

        BcFileStructure.bcOperateOnFiles(BcFileStructure, 4, None)
        
    def deSelectDeletedFilesMenu(self):
        BcFileStructure.bcOperateOnFiles(BcFileStructure, 5, None)

    def cancelExportMenu(self):
        # if dfxml file was internally generated, remove it.
        global isGenDfxmlFile
        if isGenDfxmlFile == True:
            os.system('rm '+g_dfxmlfile)
        print(">> Disk Access operation is aborted ")

        # Set the breakout flag to True to stop the export operation.
        global g_breakout
        g_breakout = True

        # Set the active flag to False
        ProgressBar._active = False

        # Set the progressbar maximum to > minimum so the spinning will stop
        global global_pb_da
        global_pb_da.progressbar.setRange(0,1)

        x = Ui_MainWindow
        global g_textEdit_msg
        global g_oldstdout
        g_textEdit_msg.setText( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

        g_oldstdout = sys.stdout
        sys.stdout = StringIO()

        # Set the flag in the thread to signal thread termination
        global g_thread1_da
        g_thread1_da.join()

    def exportFilesMenu(self):
        os.chdir(os.environ["HOME"])
        outdir = self.getExportOutdir()

        ## print(">> D: Output Directory Selected: ", exportDir)
        
        # Invoke bcOperateOnfiles routine with check=2
        thread1 = daThread(2, outdir)

        # Save the thread handle for later use in cancel task.
        global g_thread1_da
        g_thread1_da = thread1
        
        thread2 = guiThread("export")

        thread1.start()
        thread2.start()

    '''
    def buttonClickedDump(self):
        BcFileStructure.bcOperateOnFiles(BcFileStructure, 3, None)
    '''
    def showMsgsWindowMenu(self):
        # FIXME: Under construction
        MainWindow.restoreState(self.byte_array_msg_window)
        ret = MainWindow.restoreDockWidget(self.dockWidget_msg)
        ## print("D: showMsgsWidnowMenu: ret: ", ret)
        return

    def showImginfoWindowMenu(self):
        # FIXME: Under construction
        MainWindow.restoreState(self.byte_array_msg_window)
        ret = MainWindow.restoreDockWidget(self, self.dockWidget_imginfo)
        ## print("D: showMsgsWidnowMenu: ret: ", ret)
        return

class BcFileStructure:

    acc_dict_array = ["filename", "partition", "inode", "name_type", "filesize", "alloc"]
    fiDictList = []
    parentlist = []
    file_item_of = dict()
    path_of = dict()

    x = Ui_MainWindow
    
    # bcOperateOnFiles()
    # Iterate through the leaves of the file structure and check/uncheck
    # all the files based on whether "check" is True or False.
    # This same routine is reused with the parameter "check" set to 2, 
    # to dump the contents of the "checked" files to the specified output 
    # directory. It is again used with check=3 to dump the contents of a
    # file to the textEdit window. Further it is extended to use check=4 and 5 
    # for selecting and deselecting respectively the deleted files. 
    def bcOperateOnFiles(self, check, exportDir):
        ## print(">>D: Length of fiDictList: ", len(self.fiDictList))
        global g_breakout
        g_breakout = False
        for i in range(0, len(self.fiDictList) - 1):
            path = self.fiDictList[i]['filename']
            inode = self.fiDictList[i]['inode']
            if self.fiDictList[i]['name_type'] == 'd':
                isdir = True
            else:
                isdir = False
            pathlist = path.split('/')
            pathlen = len(pathlist)
            ## print("D: Path LiSt: ", pathlist, len(pathlist))
            ## print("D: =================")
            last_elem = pathlist[pathlen-1]
            if last_elem == "." or last_elem == "..":
                # Ignore . and ..
                continue 

            deleted = False
            if self.fiDictList[i]['alloc'] == False:
                deleted = True

            if isdir == False:
                # First get the name of the current file
                current_fileordir = pathlist[pathlen-1]

                # Now using the dict of files, file_item_of, get the item 
                # for this file
                unique_path = path + '-' + str(inode)
                current_item = self.file_item_of[unique_path]
                if check == 1:
                    if (current_item.checkState() == 0):
                        ## print("D: Setting File to Checked_state ", current_fileordir) 
                        current_item.setCheckState(2)
                elif check == 0:
                    current_item.setCheckState(0)
                elif check == 2:
                    if g_breakout == True:
                        break
                    # If "check" is 2, we use this routine to dump the 
                    # contents of the specified file to the specified output
                    # file. 
                    # If this file is "checked", download its contents.
                    # item.checkState has 0 if not checked, 1 if partially
                    # checked and 2 if checked. 
                    # http://qt.developpez.com/doc/4.6/qt/#checkstate-enum

                    if current_item.checkState() == 2:
                        ## print(">> D: File %s is Checked" %current_fileordir)
                        if not os.path.exists(exportDir):
                            os.mkdir(exportDir)

                        pathlist = path.split('/')
                        oldDir = newDir = exportDir
                        
                        # Iterate through the path list and make the directories
                        # in the path, if they don't already exist.
                        for k in range(0, len(pathlist)-1):
                            newDir = oldDir + '/' + pathlist[k]
                            if not os.path.exists(newDir):
                                os.mkdir(newDir)
                            oldDir = newDir
                        outfile = newDir + '/'+current_fileordir
                        ## print(">> D: Writing to Outfile: ", outfile, path)
                        
                        filestr.bcCatFile(path, inode, g_image, g_dfxmlfile, True, outfile)
                    elif current_item.checkState() == 1:
                        print("Partially checked state: ",current_item.checkState()) 
                        print("File %s is NOT Checked" %current_fileordir)
                        # FIXME: Test the above debug print stmts
                        g_textEdit_msg.append( sys.stdout.getvalue() )
                        #sys.stdout = x.oldstdout
                        sys.stdout = g_oldstdout
                        g_oldstdout = sys.stdout
                        sys.stdout = StringIO()

                elif check == 3:
                    # Dump the first checked File in textEdit window
                    if current_item.checkState() == 2:
                        print(">> D: File %s is Checked" %current_fileordir)

                        #self.oldstdout = sys.stdout
                        g_oldstdout = sys.stdout
                        sys.stdout = StringIO()
                        
                        ## print("D: >> Dumping the contents of the file ", path)
                        ## FIXME: Not tested with inode yet.
                        filestr.bcCatFile(path, inode, g_image, g_dfxmlfile, False, None)
                         
                        g_textEdit_msg.setText( sys.stdout.getvalue() )
                        #sys.stdout = self.oldstdout
                        g_stdout = self.oldstdout
                        
                        # We list only the first checked file.
                        return
                    elif current_item.checkState() == 1:
                        print("Partially checked state: ",current_item.checkState()) 
                        print("File %s is NOT Checked" %current_fileordir)
                        g_textEdit_msg.setText( sys.stdout.getvalue() )
                        #sys.stdout = self.oldstdout
                        sys.stdout = g_oldstdout
                elif check == 4:
                    # If current_item is a deleted file, select it
                    if deleted == True:
                        if (current_item.checkState() == 0):
                            ## print("D: Setting File to Checked_state ", current_fileordir) 
                            current_item.setCheckState(2)
                elif check == 5:
                    # If current_item is a deleted file, DeSelect it
                    if deleted == True:
                        current_item.setCheckState(0)

    def bcHandleSpecialChars(self, filename):
        #filename = filename.replace("$", "\$")
        #filename = filename.replace(" ", "\ ")
        #filename = filename.replace("(", "\(")
        #filename = filename.replace(")", "\)")
        return re.escape(filename)
                    
    def bcGetFilenameFromPath(self, path):
        pathlist = path.split('/')
        pathlen = len(pathlist)

        filename = pathlist[pathlen-1]

        # Prepend special characters with backslash
        filename = self.bcHandleSpecialChars(filename)
        return filename
    
    # Routine to be invoked when a disk image is 'closed'
    # It clears the QTreeView model and the dictionary created from 
    # dfxml file of the image.
    def bcDeleteModel(self, image):
        global g_model
        g_model.clear()
        self.fiDictList = []
 
    # bcExtractFileStr()
    # This routine extracts the file structure given a disk image and the
    # corresponding dfxml file.
    def bcExtractFileStr(self, image, dfxmlfile, outdir):
        global g_textEdit_msg
        global g_oldstdout
        g_textEdit_msg.append( sys.stdout.getvalue() )
        g_oldstdout = sys.stdout
        sys.stdout = StringIO()
        
        # Extract the information from dfxml file to create the 
        # dictionary only if it is not done before.
        if len(self.fiDictList) == 0:
            self.bcProcessDfxmlFileUsingSax(dfxmlfile)
            ## print("D: Length of dictionary fiDictList: ", len(self.fiDictList))

        parent0 = image
        parent0_item = QtGui.QStandardItem('Disk Image: {}'.format(image))
        global g_parent0_item
        g_parent0_item = parent0_item

        current_fileordir = image
        parent_dir_item = parent0_item
        font = QtGui.QFont("Times",12,QtGui.QFont.Bold)
        parent_dir_item.setFont(font)

        global g_image
        global g_dfxmlfile
        g_image = re.escape(image)
        g_dfxmlfile = dfxmlfile

        # A dictionary item_of{} is maintained which contains each file/
        # directory and its corresponding " tree item" as its value.
        item_of = dict()
        item_of[image] = parent0_item

        global g_model
        g_model.setHorizontalHeaderLabels(['File System: \n  Entries in bold are directories \n  Entries in red are unallocated/deleted files '])
        g_model.appendRow(parent0_item)

        for i in range(0, len(self.fiDictList) - 1):
            path = self.fiDictList[i]['filename']
            inode = self.fiDictList[i]['inode']
            ## print("D: path, inode: ", path, inode)
            isdir = False
            if self.fiDictList[i]['name_type'] == 'd':
                isdir = True

            deleted = False
            if self.fiDictList[i]['alloc'] == False:
                deleted = True

            pathlist = path.split('/')
            pathlen = len(pathlist)
            ## print("D: Path LiSt: ", pathlist, len(pathlist))
            last_elem = pathlist[pathlen-1]
            if last_elem == "." or last_elem == "..":
                # Ignore . and ..
                continue 

            if isdir == True:
                ## print("D: It is  a Directory:  Pathlen: ", pathlen)
                if (pathlen < 2):
                    # If pathlen is < 2 it is a file/dir directly off the root.
                    parent_dir_item = parent0_item
                else:
                    parent_dir_item = item_of[pathlist[pathlen-2]]

                current_dir = pathlist[pathlen-1]
                current_item = QtGui.QStandardItem(current_dir)
                font = QtGui.QFont("Times",12,QtGui.QFont.Bold)
                current_item.setFont(font)

                # Add the directory item to the tree.
                parent_dir_item.appendRow(current_item)

                # DEBUG: Following 2 lines are added for debugging 
                ###g_textEdit_msg.append(sys.stdout.getvalue() )
                #sys.stdout = x.oldstdout
                ###sys.stdout = g_oldstdout

                # Save the item of this directory
                item_of[current_dir] = current_item
                
            else:
                # File: The file could be in any level - top level is the
                # child of parent0_item (disk img). The level is sensed by the
                # pathlen 
                current_fileordir = pathlist[pathlen-1]
                unique_current_file = current_fileordir + '-' + str(inode)
                current_item = QtGui.QStandardItem(unique_current_file)
                ## print("D: It is a file:  ", current_fileordir, current_item)
                ## print("D: pathlen: ", pathlen)

                # We want just the filename in the GUI - without the inode
                current_item.setText(current_fileordir)

                ##g_textEdit_msg.append( sys.stdout.getvalue() )
                ##sys.stdout = g_oldstdout

                current_item.setCheckable(True)
                current_item.setCheckState(0)

                if deleted == True:
                    current_item.setForeground(QtGui.QColor('red'))

                # save the "item" of each file
                unique_path = path + '-' + str(inode)
                self.file_item_of[unique_path] = current_item

                if pathlen > 1:
                    parent_dir_item = item_of[pathlist[pathlen-2]]
                else:
                    parent_dir_item = parent0_item
            
                # Add the directory item to the tree.
                parent_dir_item.appendRow(current_item)

            parent = parent_dir_item
            
    def bcCatFile(self, filename, inode, image, dfxmlfile, redirect_file, outfile):
        # Traverse the XML file, get the file_name, extract the inode number
        # of the file and run icat to extract the data.
        ## print(">>D: bcCatFile: Filename: ", filename)
        ## print(">>D: bcCatFile: image: ", image)
        ## print(">>D: bcCatFile: dfxmlfile: ", dfxmlfile)
        ## print(">>D: bcCatFile: outfile: ", outfile)
        x = Ui_MainWindow
        #x.oldstdout = sys.stdout
        #sys.stdout = StringIO()

        # First traverse through dfxmlfile to get the block containing 
        # "filename" to extract the inode. Do this just once.

        if len(self.fiDictList) == 0:
            self.bcProcessDfxmlFileUsingSax(dfxmlfile)
            ## print("D: Length of fiDictList ", len(self.fiDictList))

        # Dictionary is formed. Now traverse through the array and 
        # in each dictionary, get the inode and call iCat command.
        for i in range(0, len(self.fiDictList)-1):
            if (self.fiDictList[i]['filename'] == filename and self.fiDictList[i]['inode'] == inode):
                ## print("D: Extracting the contents of the file:inode ", \ 
                ##                  filename, self.fiDictList[i]['inode']) 
                # First get the offset of the 2nd partition using mmls cmd
                # ex: mmls -i aff ~/aaa/jo-favorites-usb-2009-12-11.aff

                if image.endswith(".E01") or image.endswith(".e01"):
                    imgtype = 'ewf'
                elif image.endswith(".aff") or image.endswith(".AFF"):
                    imgtype = 'aff'
                elif image.endswith(".iso") or image.endswith(".ISO"):
                    imgtype = 'iso'
                else:
                    imgtype = 'raw'

                # Extract the file-system type from dfxml file volume
                ftype = self.bc_get_ftype_from_sax(dfxmlfile) 
                
                # For fat12 file-system there is no partiton information.
                # So skip the step for extracting partition offset.
                part2_start = 0
                if self.ftype != 'fat12' and self.ftype != 'iso9660' and imgtype != 'iso':
                    mmls_cmd = "mmls -i " + imgtype +" "+image +" | grep \"02:\""

                    ## print("D: Executing mmls command: ", mmls_cmd) 
                    part2 = subprocess.check_output(mmls_cmd, shell=True)
                    ## print("D: Extracting partition-2: ", part2)

                    part2_list = part2.split()
                    part2_start = int(part2_list[2])
                

                ## print("D: Start offset of Partition-2: ", part2_start)
                ## icat_cmd ex: icat -o 1 ~/aaa/charlie-work-usb-2009-12-11.aff 130 
                # redirect_file is set to True if the contents need to be 
                # written to a file.
                if (redirect_file == True):
                    outfile = self.bcHandleSpecialChars(outfile)

                    icat_cmd = "icat -o "+str(part2_start)+ " "+ \
                                image + " " + \
                                self.fiDictList[i]['inode'] + ' > ' + outfile
                    f2 = Popen(icat_cmd, shell = True, stdout=PIPE, stderr=PIPE)
                    (data, err) = f2.communicate()

                else:
                    # Only printable files are dumped on the textEdit wondow.
                    # The rest are redirected to a file in /tmp
                    if (filename.endswith('txt') or filename.endswith('xml')):
                        icat_cmd = "icat -o "+str(part2_start)+ " "+ image + " " + self.fiDictList[i]['inode']
                        ## print(">> D: Executing iCAT command: ", icat_cmd)
                        f2 = os.popen(icat_cmd)
                        icat_out = f2.read()
                        print(">> Dumping Contents of the file :", filename)
                        print("\n")
                        print(icat_out)

                    else:
                        # Strip the path to extract just the name of the file.
                        justFilename = self.bcGetFilenameFromPath(filename)                
                        icat_cmd = "icat -o "+str(part2_start)+ " "+ \
                                image + " " + \
                                self.fiDictList[i]['inode'] + ' > /tmp/'+justFilename
                        f2 = os.popen(icat_cmd)

                        # Open the file in the pdf reader if it is a PDF file
                        # else copy it to a file in /tmp
                        if justFilename.endswith('pdf'):
                            print(">>> Opening the PDF file /tmp/",justFilename)  
                            os.system('evince /tmp/'+justFilename)
                        else:
                            print(">>> File copied to: ", '/tmp/'+justFilename)

                return
 
    # Callback function for SAX processing of the dfxml file.
    def cb(self, fi):
        self.fiDictList.append({self.acc_dict_array[0]:fi.filename(), \
                           self.acc_dict_array[1]:fi.partition(), \
                           self.acc_dict_array[2]:fi.inode(), \
                           self.acc_dict_array[3]:fi.name_type(), \
                           self.acc_dict_array[4]:fi.filesize(),\
                           self.acc_dict_array[5]:fi.allocated() })

        
    # The fiwalk utility fiwalk_using_sax is invoked with a callback
    # to process the dfxml file contents.
    def bcProcessDfxmlFileUsingSax(self, dfxmlfile):
        fiwalk.fiwalk_using_sax(xmlfile=open(dfxmlfile, 'rb'),callback=self.cb)

    def cbv_ftype(self, fv):
        self.ftype = fv.ftype_str()

    def bc_get_ftype_from_sax(self, dfxmlfile):
        fiwalk.fiwalk_vobj_using_sax(xmlfile=open(dfxmlfile, 'rb'),callback=self.cbv_ftype)
       
# Thread for running the fiwalk command
class bcfaThread_fw(threading.Thread):
    def __init__(self, cmd, image_file, dfxmlfile):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.image_file = image_file
        self.dfxmlfile = dfxmlfile
        super(bcfaThread_fw, self).__init__()
        self.stoprequest = threading.Event()
        self.process = None

    def stopped(self):
        return self.stoprequest.isSet()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(bcfaThread_fw, self).join(timeout)

    def run(self):
        g_oldstdout = sys.stdout
        sys.stdout = StringIO()
        p = self.process = Popen(self.cmd, stdout=PIPE, stderr=PIPE)
        (data, err) = p.communicate()
        if p.returncode:
            ProgressBar._active = False

            # We don't want to display this as an error as pressing the cancel
            # button could bring us here as well.
            ## print(">> D: ERROR!!! Fiwalk terminated with error: \n", err)
            print(">> Fiwalk terminated \n")

            global g_textEdit_msg
            g_textEdit_msg.append( sys.stdout.getvalue() )
            sys.stdout = g_oldstdout

            # Set the progressbar maximum to > minimum so the spinning will stop
            global global_fw
            global_fw.progressbar.setRange(0,1)

            g_oldstdout = sys.stdout
            sys.stdout = StringIO()
        else:
            # Set the progresbar active flag so the other thread can
            # get out of the while loop.
            ProgressBar._active = False
            #print("D: bcfaThread_fw: Progressbar Active Flag Set to: ", ProgressBar._active)

            print("\n>> Success!!! Fiwalk created DFXML file \n")

            # Set the progressbar maximum to > minimum so the spinning will stop
            global_fw.progressbar.setRange(0,1)

            # Generate the Directory Tree
            print(">> Generating directory tree ...")

            filestr = BcFileStructure()
            filestr.bcExtractFileStr(self.image_file, self.dfxmlfile, outdir=None)


# Thread which exports all the checked files 
class daThread(threading.Thread):
    def __init__(self, check, export_dir):
        self.check = check
        self.export_dir = export_dir
        super(daThread, self).__init__()
        self.stoprequest = threading.Event()

    def stopped(self):
        return self.stoprequest.isSet()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(daThread, self).join(timeout)

    def run(self):
        global g_oldstdout
        print(">> File export operation in progress...")
        global g_textEdit_msg
        g_textEdit_msg.append( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

        BcFileStructure.bcOperateOnFiles(BcFileStructure, self.check, self.export_dir)

        ProgressBar._active = False

        # Set the progressbar maximum to > minimum so the spinning will stop
        global global_pb_da
        global_pb_da.progressbar.setRange(0,1)

        g_oldstdout = sys.stdout
        sys.stdout = StringIO()
        print(">> Copied checked files to the directory: ", self.export_dir)
        g_textEdit_msg.append( sys.stdout.getvalue() )
        sys.stdout = g_oldstdout

    # A placeholder for any clean-up operation to be done upon pressing
    # the cancel button.
    def stop(self):
        pass
        ## print(">> D: Terminating the Thread for \"Export Files\"")

           

# This is the thread which spins in a loop till the other thread which
# does the work sets the flag once the task is completed.
class guiThread(threading.Thread):
    def __init__(self, cmd_type):
        threading.Thread.__init__(self)
        self.cmd_type = cmd_type

    def run(self):
        if self.cmd_type == "fiwalk":
            global global_fw
            progressbar = global_fw
        elif self.cmd_type == "export":
            global global_pb_da
            progressbar = global_pb_da

        progressbar.startLoop(self.cmd_type)

class ProgressBar( QtGui.QWidget):
    _active = False
    def __init__(self, parent=None):
        super(ProgressBar, self).__init__(parent)
        self.progressbar = QtGui.QProgressBar()
        main_layout = QtGui.QGridLayout()
        main_layout.addWidget(self.progressbar, 0, 1)
        self.setLayout(main_layout)
        self.setWindowTitle('Progress')

    def closeEvent(self):
        self._active = False

    def startLoop(self, cmd_type):
        self._active = True
        ProgressBar._active = True
        cntr = 0

        if cmd_type == "fiwalk":
            global global_fw
            global_fw.progressbar.setRange(0,0)
        elif cmd_type == "export":
            global global_pb_da
            global_pb_da.progressbar.setRange(0,0)

        while True:
            time.sleep(1.05)
            cntr = cntr + 1

            QtGui.qApp.processEvents()
            #print("D: ProgressBar._active = ", ProgressBar._active)
            if not ProgressBar._active:
                #print ("D: startLoop thread detected flag = ", ProgressBar._active)
                if cmd_type == "fiwalk":
                    global g_thread1_fw
                    if g_thread1_fw.stopped():
                        ## print("D: startLoop_bc: Thread Stopped ")
                        g_thread1_fw.stop()

                if cmd_type == "export":
                    #print ("D: startLoop thread detected flag = ", ProgressBar._active)
                    global g_thread1_da
                    if g_thread1_da.stopped():
                        ## print("D: startLoop_bc: Thread Stopped ")
                        g_thread1_da.stop()
                break

        ProgressBar._active = False
                    
            
if __name__=="__main__":
    import sys, time, re

    parser = ArgumentParser(prog='bc_disk_access.py', description='File Access')
    args = parser.parse_args()

    global isGenDfxmlFile
    isGenDfxmlFile = False

    filestr = BcFileStructure()

    '''
    # FIXME: Legacy code
    # The following call is just to test bcCatFile, giving a filename
    # from the dfxml file. In reality, it will be invoked from a click on 
    # a file in the web browser.
    if (args.cat == True):
        if args.filename == None or dfxmlfile == None:
            print(">> Filename or dfxml file not provided. Exiting")
            exit(0) 

        if not os.path.exists(dfxmlfile):
            print(">> File %s doesnot exist " %dfxmlfile) 
            exit(0)

        # FIXME: Inode is set to 0 temporarily.
        filestr.bcCatFile(args.filename, 0, args.image, dfxmlfile, False, None)
    '''

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # expand third container
    ## parent0_item = BcFileStructure.bcExtractFileStr.parent0
    ## index = model.indexFromItem(parent0)
    ## view.expand(index)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # select last row
    ## selmod = view.selectionModel()
    #index2 = model.indexFromItem(child3)
    ## index2 = model.indexFromItem(parent0)
    ## selmod.select(index2, QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Rows)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
