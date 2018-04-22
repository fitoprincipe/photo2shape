#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Simple software to create a vector file (shapefile, KML, geoJSON, etc)
from a collection of geotagged pictures
"""

import sys
import exifread
import os

try:
    import osgeo.ogr as ogr
except:
    import ogr

try:
    import osgeo.osr as osr
except:
    import osr

from PyQt4 import QtGui, QtCore

__version__ = '0.0.2'

DRIVER_EXTENSIONS = {'ESRI Shapefile': 'shp',
                     'KML': 'kml',
                     'GeoJSON': 'geojson'}
ERRORS = []

def erase_list():
    del ERRORS[:]

def check_gps_data(img):

    image = open(img, 'rb')
    the_tags = exifread.process_file(image)

    hasgps = 'GPS GPSLongitude' in the_tags.keys()

    return True if hasgps else False

class Window(QtGui.QMainWindow):
    """ Main Windows """

    def __init__(self, **kwargs):
        # inherit from QMainWindow
        super(Window, self).__init__(**kwargs)

        # set parameters for Main Window
        self.setWindowTitle(
            "photo2shape - github.com/fitoprincipe/photo2shape")
        # self.setGeometry(50,50,500,300)
        self.setFixedSize(500, 300)

        # set windows style
        QtGui.QApplication.setStyle(
            QtGui.QStyleFactory.create("Plastique"))

        # create menu bar
        menubar = self.menuBar()

        # Add 'File' to menubar
        filemenu = menubar.addMenu("File")

        # Open Action & shortcut
        open = QtGui.QAction("&Open", self)
        open.setShortcut("Ctrl+O")
        open.triggered.connect(self.open_filepicker)
        open.setStatusTip("Open")
        filemenu.addAction(open)

        # Exit Action & shortcut
        exit = QtGui.QAction("&Exit", self)
        exit.setShortcut("Ctrl+Q")
        exit.triggered.connect(self.exit_function)
        exit.setStatusTip("Exit")
        filemenu.addAction(exit)

        # StatusBar
        self.theStatusBar = self.statusBar()

        # force the application to use QT menu bar and NO OS menubar
        # useful for Linux users
        menubar.setNativeMenuBar(False)

        # Add Buttons
        self.add_buttons()

    def add_buttons(self):

        # Process button
        btn = QtGui.QPushButton("Process", self)
        btn.resize(80, 40)
        btn.move(210, 200)
        btn.clicked.connect(self.process)

        # Labels
        self.window_style = QtGui.QLabel("Choose a format", self)
        self.window_style.move(20, 130)
        self.window_style.resize(200, 20)

        self.file_label = QtGui.QLabel("no file selected", self)
        self.file_label.move(20, 30)
        self.file_label.resize(500, 50)
        self.file_label.setMargin(2)

        self.newfile_label = QtGui.QLabel("New filename:", self)
        self.newfile_label.move(20, 95)
        self.newfile_label.resize(200, 25)
        self.newfile_label.setMargin(2)

        # Dropdown
        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.addItem('ESRI Shapefile')
        self.comboBox.addItem('KML')
        self.comboBox.addItem('GeoJSON')
        self.comboBox.move(150, 130)
        self.comboBox.resize(135, 25)

        # TEXT INPUT
        self.filename_field = QtGui.QLineEdit(self)
        self.filename_field.move(250, 95)
        self.filename_field.resize(200, 25)

        # Center Mainwindow
        self.centerOnScreen()

        # Show buttons
        self.show()

    def centerOnScreen(self):
        """centerOnScreen() Centers the window on the screen."""
        resolution = QtGui.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

    # funcion para abrir el archivo mediante un file picker
    # obtiene una lista -theFilesList- con los archivos seleccionados
    def open_filepicker(self):
        """ Open files with File Picker

        :return: selected files
        """

        # Dialog to open files
        self.file_dialog = QtGui.QFileDialog.getOpenFileNames(self,
                                                          "Open files",
                                                          os.getcwd(), # TODO: save last opened folder to a text file
                                                          "Images (*.png "
                                                          "*.jpg)")

        # files list
        self.theFilesList = []

        # errors list
        self.theErrorList = []

        if self.file_dialog:
            n = 0
            m = 0

            # add files to list
            # TODO: check GPS data, if no file has it, do not create file
            for file in self.file_dialog:
                m += 1
                gps = check_gps_data(file)
                if gps:
                    n += 1
                    self.theFilesList.append(file)

            msg = "{} of {} files will be processed".format(n, m)
            self.file_label.setText(msg)

    def process(self):
        """ Extract GPS data using file's EXIF

        :return:
        """

        filename = self.filename_field.text()

        if filename.size() == 0:
            self.theStatusBar.showMessage(
            "filename must contain one character at least")
            return
        elif len(self.theFilesList) == 0:
            self.theStatusBar.showMessage("no files to process...")
            return
        else:
            err = 0

            theDvrI = self.comboBox.currentIndex()
            theDvr = self.comboBox.itemText(theDvrI)

            # SHAPEFILE CREATION

            # get driver
            driver = ogr.GetDriverByName(str(theDvr))

            # get extension
            theExt = DRIVER_EXTENSIONS[str(theDvr)]

            # get file's path
            last = str(self.theFilesList[0])
            dirname = os.path.dirname(last)
            # print dirname
            # print str(self.theFilesList[0])-last

            # create new FileName (filename)
            # listaCarpeta = str(self.theFilesList[0]).split("/")
            # print listaCarpeta[len(listaCarpeta)-1]

            # filename = str(dirname) + "/" + str(filename) + theExt
            filename = "{}.{}".format(os.path.join(str(dirname), str(filename)),
                                      theExt)

            # create DataSource
            if os.path.exists(filename):
                ERRORS.append(filename)
                self.theStatusBar.showMessage(
                    'file {} exists already, choose another name\
                     please'.format(filename))
                return
            else:
                theShp = driver.CreateDataSource(filename)

                # create SRS
                # TODO: detect SRS from EXIF
                theSR = osr.SpatialReference()
                theSR.ImportFromEPSG(4326)

                # create point Layer (wkbPoint) from DataSource
                if theShp is None:
                    sys.exit(1)
                layer = theShp.CreateLayer(os.path.basename(filename), theSR,
                                          ogr.wkbPoint)

                # COLUMNS CREATION

                # Create ID Field and add it to Layer
                fieldDefn = ogr.FieldDefn("ID", ogr.OFTInteger)
                layer.CreateField(fieldDefn)

                # create path field
                fldPath = ogr.FieldDefn("Path", ogr.OFTString)
                layer.CreateField(fldPath)

                # create coordinates field
                fldLat = ogr.FieldDefn("Lat", ogr.OFTReal)
                layer.CreateField(fldLat)

                fldLng = ogr.FieldDefn("Lng", ogr.OFTReal)
                layer.CreateField(fldLng)

                # get Layer type
                featureDefn = layer.GetLayerDefn()

            # create one point per file
            theid = 0
            for file in self.theFilesList:
                # augment id
                theid += 1

                # open file and process it to add the tags in the combobox
                image = open(file, 'rb')
                the_tags = exifread.process_file(image)

                if 'GPS GPSLongitude' in the_tags.keys():

                    lon = the_tags['GPS GPSLongitude']
                    lat = the_tags['GPS GPSLatitude']
                    lonR = the_tags['GPS GPSLongitudeRef']
                    latR = the_tags['GPS GPSLatitudeRef']

                    lon_list = (str(lon)).split(",")
                    lat_list = (str(lat)).split(",")

                    LongG = lon_list[0].replace("[", "")
                    LongM = lon_list[1]
                    LongS = lon_list[2].replace("]", "")
                    LongSS = LongS.split("/")
                    LongS1 = (float(LongSS[0])) / (float(LongSS[1]))

                    LatG = lat_list[0].replace("[", "")
                    LatM = lat_list[1]
                    LatS = lat_list[2].replace("]", "")
                    LatSS = LatS.split("/")
                    LatS1 = (float(LatSS[0])) / (float(LatSS[1]))

                    if latR == "N":
                        Lat = (float(LatG)) + ((float(LatM)) / 60) + (
                            (float(LatS1)) / 3600)
                    else:
                        Lat = ((float(LatG)) + ((float(LatM)) / 60) + (
                            (float(LatS1)) / 3600)) * (-1)

                    if lonR == "E":
                        Lng = (float(LongG)) + ((float(LongM)) / 60) + (
                            (float(LongS1)) / 3600)
                    else:
                        Lng = ((float(LongG)) + ((float(LongM)) / 60) + (
                            (float(LongS1)) / 3600)) * (-1)

                    # create shapefile
                    self.create_shapefile(theid, the_tags, file, Lat, Lng,
                                          featureDefn, layer)

                else:
                    # self.theErrorList.append(str(b))
                    err = err + 1

            theShp.Destroy()

            if (err > 0) and (len(ERRORS) == 0):
                self.file_label.setText(
                    "{} files were not processed because didn't have GPS\
                    data".format(err))
            elif (err == 0) and (len(ERRORS) > 0):
                self.file_label.setText(
                    "{} files were already processed".format(len(ERRORS)))
            elif (err > 0) and (len(ERRORS) > 0):
                self.file_label.setText(
                    "{} files were not processed because didn't have GPS\
                    data and {} files were already processed".format(err, len(ERRORS)))
            else:
                self.file_label.setText("process completed successfully")

            erase_list()
            print(str(len(ERRORS)))

    def exit_function(self):
        """ Exit function

        :return:
        """
        # Options
        options = QtGui.QMessageBox.question(self,
                                            "Quiting...",
                                            "do you really want to exit?",
                                            QtGui.QMessageBox.Yes |
                                            QtGui.QMessageBox.No)

        if options == QtGui.QMessageBox.Yes:
            sys.exit()
        else:
            pass

    def create_shapefile(self, theid, tags, file, lat, lng, featureDefn, layer):

        # Create Feature
        feature = ogr.Feature(featureDefn)

        # TODO: catch USEFUL data from tags and pass them to shapefile table

        # Set fields
        feature.SetField("ID", theid)
        feature.SetField("Path", str(file))
        feature.SetField("Lat", float(lat))
        feature.SetField("Lng", float(lng))

        # create the point
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lng, lat)

        # add point
        feature.SetGeometry(point)

        # add new feature to layer
        layer.CreateFeature(feature)

        # Destroy
        point.Destroy()
        feature.Destroy()

def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()