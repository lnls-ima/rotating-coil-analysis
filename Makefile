# Makefile for Rotating Coil Analysis GUI

all:
	pyuic4 interface.ui -o interface.py
	pyuic4 table_dialog.ui -o table_dialog.py
	pyrcc4 -py3 resources.qrc -o resources_rc.py

clean:
	-rm -rf interface.py resource_file_rc.py table_dialog.py
