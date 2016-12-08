#!/usr/bin/python
# -*- coding: UTF-8 -*-

import exifread

try:
	import osgeo.ogr as ogr
except:
	import ogr

try:
	import osgeo.osr as osr
except:
	import osr

def tieneGPS(img):
	'''
	Funcion que utiliza la librería exifread para saber si la foto tiene datos GPS
	'''
	imagen = open(img, 'rb')
	losTags = exifread.process_file(imagen)
	
	if losTags.has_key('GPS GPSLongitude'):
		return True
	
def borraLista(lista):
	del lista[:]

def crearShape(elid, tags, arch, lat, lng, featureDefn, capa):
	'''
	Función para crear el Shapefile
	Usa: OGR
	Parametros: (los tags, el archivo, latitud, longitud, el driver)
	'''
		
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
