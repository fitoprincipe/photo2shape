#!/usr/bin/python
# -*- coding: UTF-8 -*-

# en esta version intento hacer un solo shapefile con todas las fotos
# el formato KML lo dejo como esta, pero habria que darle una vuelta de rosca para que quede bien

import sys	
import ui
from QtGui import QApplication

def correrPrograma():
    app = QtGui.QApplication(sys.argv)
    GUI = ui.Window()
    sys.exit(app.exec_())

if __name__ == "__main__":
	correrPrograma()
