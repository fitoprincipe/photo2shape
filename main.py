#!/usr/bin/python
# -*- coding: UTF-8 -*-

# en esta version intento hacer un solo shapefile con todas las fotos
# el formato KML lo dejo como esta, pero habria que darle una vuelta de rosca para que quede bien

import sys, exifread, os

try:
	import osgeo.ogr as ogr
except:
	import ogr

try:
	import osgeo.osr as osr
except:
	import osr
	
from PyQt4 import QtGui, QtCore

# diccionarios
longitudes = {}
theDict = {}
DriverExt = {'ESRI Shapefile':'.shp', 'KML':'.kml', 'GeoJSON':'.geojson'}
errList = []

class Window(QtGui.QMainWindow):
	
    # ---- FUNCION DE INCIO --------------------------------------------
    def __init__(self):
		# hereda los métodos de los 'padres' de QMainWindow
        super(Window, self).__init__()
                
		# fija parametros del Main Window
        self.setWindowTitle("PHOTO2SHAPE /XYLENIA FORESTAL /www.xylenia.com")
        #self.setGeometry(50,50,500,300)
        self.setFixedSize(500,300)
        
        # fija el estilo de la ventana
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Plastique"))
        
        # crea la barra del menu
        el_menu = self.menuBar()
        
        # agrega a la barra del menu el item "Archivo"
        menu_salir = el_menu.addMenu("Archivo")
        
        # crea el submenu "Salir" para el nuevo menu y le asigna una funcion
        salir = QtGui.QAction("&Salir", self)
        salir.setShortcut("Ctrl+Q")
        salir.triggered.connect(self.funcionSalir)
        salir.setStatusTip("Salir")
        
        # crea el submenu "Abrir" para abrir un archivo
        abrir = QtGui.QAction("&Abrir", self)
        abrir.setShortcut("Ctrl+A")
        abrir.triggered.connect(self.funcionAbrir)
        abrir.setStatusTip("Abrir")
        
        # activa el status bar
        self.theStatusBar = self.statusBar()
        
        # le agrega al nuevo elemento el submenu "Abrir" con su accion
        menu_salir.addAction(abrir)
                
        # le agrega al nuevo elemento el submenu "Salir" con su accion
        menu_salir.addAction(salir)
        
        # metodo para forzar a la aplicacion a usar la barra del menu segun Qt (y no la nativa del OS)
        el_menu.setNativeMenuBar(False)
        
        # llamo a la funcion "boton" que agrega un boton
        self.botones()

	# ---- FUNCION PARA AGREGAR BOTONES AL MAIN WINDOW -----------------

    def botones(self):
		
		# BOTON
        btn = QtGui.QPushButton("procesar", self)
        btn.resize(80,40)
        btn.move(210,200)
        btn.clicked.connect(self.procesar)
        
        # LABELS
        self.estiloVentana = QtGui.QLabel("Elija un formato", self)
        self.estiloVentana.move(20,130)
        self.estiloVentana.resize(200,20)
        
        self.Arch = QtGui.QLabel("ningun archivo seleccionado", self)
        self.Arch.move(20,30)
        self.Arch.resize(500,50)
        self.Arch.setMargin(2)
        
        self.ArchSave = QtGui.QLabel("Nombre del nuevo archivo:", self)
        self.ArchSave.move(20,95)
        self.ArchSave.resize(200,25)
        self.ArchSave.setMargin(2)
        
        # DROPDOWN        
        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.addItem('ESRI Shapefile')
        self.comboBox.addItem('KML')
        self.comboBox.addItem('GeoJSON')
        self.comboBox.move(150,130)
        self.comboBox.resize(135,25)
        
        # TEXT INPUT
        self.nombreArch = QtGui.QLineEdit(self)
        #self.nombrearch.setLineWidth(200)
        self.nombreArch.move(250,95)
        self.nombreArch.resize(200,25)
        
        # centra el MainWindow
        self.centerOnScreen()
                		
		# muestra los botones        
        self.show()
        
        
	# ---- FUNCION PARA CENTRAR EL MAINWINDOW --------------------------
    def centerOnScreen (self):
        '''centerOnScreen() Centers the window on the screen.'''
        resolution = QtGui.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

    
    # ------- FUNCIONES DE ACCION --------------------------------------
    
    # funcion para abrir el archivo mediante un file picker
    # obtiene una lista -theFilesList- con los archivos seleccionados
    def funcionAbrir(self):
		
		# Dialog para abrir varios archivos
		self.theFile = QtGui.QFileDialog.getOpenFileNames(self, "Abrir archivo", os.getcwd(), "Images (*.png *.jpg)")
				
		# lista de archivos
		self.theFilesList = []
		
		# lista de errores
		self.theErrorList = []
		
		if self.theFile:
			n = 0
			m = 0
			
			# para cada foto
			# agrega cada foto a la lista de fotos
			# TODO: comprobar los datos GPS, si ninguna tiene, directamente no crea el archivo
			for a in self.theFile:
				m += 1
				gps = self.tieneGPS(a)
				if gps:
					# aumento n para contar los archivos
					n += 1
					self.theFilesList.append(a)
			
			if m == 0:
				self.Arch.setText("se procesaran "+str(n)+" archivos")
			else:
				self.Arch.setText("se procesaran "+str(n)+" archivos\n"+str(m)+" archivos no tienen datos GPS")				
			
    def tieneGPS(self, img):
		
        imagen = open(img, 'rb')
        losTags = exifread.process_file(imagen)
        
        if losTags.has_key('GPS GPSLongitude'):
			return True
			
	# ------- FUNCION PARA EL BOTON ------------------------------------
	# funcion: procesar el archivo
	# extrae los datos del GPS del exif
	# automaticamente ejecuta la funcion -creaShape- con los datos obtenidos
    
    def procesar(self):
		
		theText = self.nombreArch.text()
		
		if theText.size() == 0:
			#self.Arch.setText("el nombre del archivo debe contener al menos un caracter")
			self.theStatusBar.showMessage("el nombre del archivo debe contener al menos un caracter")
			return
		elif len(self.theFilesList) == 0:
			#self.Arch.setText("no hay archivos para procesar...")
			self.theStatusBar.showMessage("no hay archivos para procesar...")
		else:
			err = 0
			
			# obtiene el Driver seleccionado
			theDvrI = self.comboBox.currentIndex()
			theDvr = self.comboBox.itemText(theDvrI)
			
			# CREO EL SHAPEFILE
			
			# obtiene el Driver
			driver = ogr.GetDriverByName(str(theDvr))
		
			# obtiene la extension de archivo para ese driver mediante el diccionario creado al ppio
			theExt = DriverExt[str(theDvr)]
			 
			# obtengo el directorio (path) en el que estan las fotos
			ultimo = str(self.theFilesList[0])
			dirname = os.path.dirname(ultimo)
			#print dirname
			#print str(self.theFilesList[0])-ultimo
			
			# crea el nuevo FileName (FN)
			#FN = str(arch)+theExt
			listaCarpeta = str(self.theFilesList[0]).split("/")
			#print listaCarpeta[len(listaCarpeta)-1]
			
			#theDirName = os.path.basename(str(self.theFilesList[0]))
			#FN = str(self.theFilesList[0])+theExt

			print str(dirname)
			print str(theText)
			FN = str(dirname)+"/"+str(theText)+theExt
			
			# crea el DataSource
			if os.path.exists(FN):
				errList.append(FN)
			else:		
				theShp = driver.CreateDataSource(FN)
			
				# crea el SRS
				# -- TODO-- aca se podria detectar el SRS a partir del exif
				theSR = osr.SpatialReference()
				theSR.ImportFromEPSG(4326)
	
				# crea el Layer a partir del DataSource
				# es un layer de puntos (wkbPoint)
				if theShp is None:
					#print 'No se puede crear el archivo'
					sys.exit(1)
				capa = theShp.CreateLayer(os.path.basename(FN), theSR, ogr.wkbPoint)
			
				# CREACION DE CAMPOS (COLUMNAS)
					
				# crea el campo ID y lo agrega al Layer
				fieldDefn = ogr.FieldDefn("ID", ogr.OFTInteger)
				capa.CreateField(fieldDefn)
				
				# crea el campo del path
				fldPath = ogr.FieldDefn("Path", ogr.OFTString)
				capa.CreateField(fldPath)
				
				# crea los campos para las coordenadas
				fldLat = ogr.FieldDefn("Lat", ogr.OFTReal)
				capa.CreateField(fldLat)
				
				fldLng = ogr.FieldDefn("Lng", ogr.OFTReal)
				capa.CreateField(fldLng)
			
				# TIPO DE LAYER ?? NO SE BIEN COMO FUNCIONA
			
				# obtiene el tipo de Layer
				featureDefn = capa.GetLayerDefn()
			
			# itera sobre las fotos para crear un punto por foto
			
			elid = 0
			for b in self.theFilesList:
				# aumenta el id
				elid += 1
				
				# abro la imagen y la proceso para agregar los tags al combobox
				imagen = open(b, 'rb')
				losTags = exifread.process_file(imagen)
		
				if losTags.has_key('GPS GPSLongitude'):
					
					longitud = losTags['GPS GPSLongitude']
					latitud = losTags['GPS GPSLatitude']
					longR = losTags['GPS GPSLongitudeRef']
					latR = losTags['GPS GPSLatitudeRef']
					
					listaLong = (str(longitud)).split(",")
					listaLat = (str(latitud)).split(",")
					
					LongG = listaLong[0].replace("[","")
					LongM = listaLong[1]
					LongS = listaLong[2].replace("]","")
					LongSS = LongS.split("/")
					LongS1 = (float(LongSS[0]))/(float(LongSS[1]))
					
					LatG = listaLat[0].replace("[","")
					LatM = listaLat[1]
					LatS = listaLat[2].replace("]","")
					LatSS = LatS.split("/")
					LatS1 = (float(LatSS[0]))/(float(LatSS[1]))
					
					if latR == "N":
						Lat = (float(LatG))+((float(LatM))/60)+((float(LatS1))/3600)
					else:
						Lat = ((float(LatG))+((float(LatM))/60)+((float(LatS1))/3600))*(-1)
					
					if longR == "E": 	
						Lng = (float(LongG))+((float(LongM))/60)+((float(LongS1))/3600)
					else:
						Lng = ((float(LongG))+((float(LongM))/60)+((float(LongS1))/3600))*(-1)
						
	
					# ejecuta la funcion para crear el shape, le pasa (el archivo en formato string, Latitud, Longitud, el driver)
					crearShape(elid, losTags, b, Lat, Lng, featureDefn, capa)
				
				else:
					#self.theErrorList.append(str(b))
					err = err + 1
	
			theShp.Destroy()
			
			if (err > 0) and (len(errList) == 0):
				self.Arch.setText(str(err)+" archivos no fueron procesados porque no tienen datos GPS")
			elif (err == 0) and (len(errList) > 0):
				self.Arch.setText(str(len(errList))+" archivos ya se encontraban procesados")
			elif (err > 0) and (len(errList) > 0):
				self.Arch.setText(str(err)+" archivos no fueron procesados porque no tienen datos GPS\n"+str(len(errList))+" archivos ya se encontraban procesados")
			else:
				self.Arch.setText("proceso completado con exito!")
				
			borraLista()
			print(str(len(errList)))
	
	# --- FUNCION PARA SALIR DEL PROGRAMA ------------------------------
			
    def funcionSalir(self):
        # creo las opciones
        opcion = QtGui.QMessageBox.question(self, 
											"Saliendo del programa", 
											"realmente quiere salir del programa?", 
											QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        
        # condicional que indica que hacer si elige si o no
        if opcion == QtGui.QMessageBox.Yes:
			#P = prueba()
			#P.imprime("saliendo")
			sys.exit()
        else:
			pass

# ---------- FUNCION PARA CORRER PROGRAMA ------------------------------

def correrPrograma():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    
# ---------- FUNCION PARA BORRAR LISTAS --------------------------------
def borraLista():
	del errList[:]

# --------- FUNCION QUE MUESTRA UN MENSAJE -----------------------------
def mensaje():
	print("el archivo ya fue procesado")

# -------- FUNCION PARA CREAR LOS SHAPES -------------------------------
# recibe (los tags, el archivo, latitud, longitud, el driver)


def crearShape(elid, tags, arch, lat, lng, featureDefn, capa):
		
		# --TODO-- ACA PUEDO ELEGIR SI VOY A CREAR UN ARCH POR FOTO O UNO PARA TODAS LAS FOTOS

		# crea un feature a partir de la definicion de la capa
		feature = ogr.Feature(featureDefn)
						
		# escribe sobre los campos
		feature.SetField("ID", elid)
		feature.SetField("Path", str(arch))
		#print(lat)
		#print(lng)
		feature.SetField("Lat", float(lat))
		feature.SetField("Lng", float(lng))
		#print(feature.GetFieldAsString(2))
		#print(feature.GetFieldAsString(3))
			
		# crea un punto
		pto = ogr.Geometry(ogr.wkbPoint)
		pto.AddPoint(lng, lat)
			
		# agrega al pto
		feature.SetGeometry(pto)
		
		# agrega los nuevos features a la capa
		capa.CreateFeature(feature)

		# DESTRUYE!
		pto.Destroy()
		feature.Destroy()
		#theShp.Destroy()

# llama a la funcion que hace correr el programa
if __name__ == "__main__":
	correrPrograma()
