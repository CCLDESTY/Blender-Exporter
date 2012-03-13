INSTALLATION INSTRUCTIONS

1. Ubuntu / Linux

First change your current directory to ~/.blender/2.62/scripts/addons

Possibly the subdirectories scripts/addons doesn't exist. In this case create them. Check
out the following directory from git and copy it to the new created one:

https://github.com/xml3d/Blender-Exporter/tree/master/org.xml3d.exporter.blender/src/2.62+/io_scene_xml3d

In the end the following directory should exist:

/home/<username>/.blender/<blenderversion>/scripts/addons/io_scene_xml3d
	|- export_xml3d.py
	|- __init__.py
	|- xml3d.py

Finally restart blender or press F8 to reload the scripts.

Change to the "User Preferences" view in blender and click on the "Addons" tab.
Type "xml3d" in the box in the top left corner and press Enter. In the right corner the
following should appear:

	Import-Export: XML3D (.xhtml)
	Description:	Export XML3D
	Location:		File > Export > XML3D (.xhtml)
	Author:			Nicolas Göddel
	Version:		12.2
	Internet:		

There is a checkbox on the right side that you have to activate. Afterwards the exporter plugin
is ready to use.