# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


bl_info = {
    "name"          : "XML3D (.xhtml)",
    "author"        : "Nicolas Göddel",
    "version"       : (12, 2),
    "blender"       : (2, 5, 6),
    "api"           : 36103,
    "location"      : "File > Export > XML3D (.xhtml) ",
    "description"   : "Export XML3D",
    "warning"       : "",
    "wiki_url"      : "",
    "tracker_url"   : "",
    "category"      : "Import-Export"}

if "bpy" in locals() :
    import imp
    if "export_xml3d" in locals() :
        imp.reload(export_xml3d)
    if "xml3d" in locals() :
        imp.reload(xml3d)
else:
    import bpy
    import bpy.utils

from bpy.props import StringProperty, BoolProperty, FloatProperty

from bpy_extras.io_utils import (ExportHelper, path_reference_mode)

class XML3DExporter(bpy.types.Operator, ExportHelper) :
    '''Save XML3D'''
    bl_idname = "export_scene.xhtml"
    bl_label = "Export XML3D"
    bl_options = {'PRESET'}
    
    filename_ext = ".xhtml"
    filter_glob     = StringProperty(
                            default       = "*.xhtml",
                            options       = {'HIDDEN'})
    exportCameras   = BoolProperty(
                            name          = "Export Cameras",
                            description   = "Export cameras as views or a default view if there is no camera available. Also deselected cameras will be exported",
                            default       = False)
    onlySelected    = BoolProperty(
                            name          = "Only Selected",
                            description   = "Export only the selected objects",
                            default       = True)
    applyModifiers  = BoolProperty(
                            name          = "Apply Modifiers",
                            description   = "Create each object with modifiers applied",
                            default       = True)
    annotatePhysics = BoolProperty(
                            name          = "Annotate Physics",
                            description   = "Annotate Physics where possible",
                            default       = False)
    writeHTMLHeader = BoolProperty(
                            name          = "Write HTML header",
                            description   = "Write HTML header",
                            default       = False)
    ignoreLamps     = BoolProperty(
                            name          = "Ignore Lamps",
                            description   = "Ignore Lamps",
                            default       = False) 
    useRaytracing   = BoolProperty(
                            name          = "Use Raytracing",
                            description   = "Use Raytracing for the xml3d node",
                            default       = True)
    convertParenting = BoolProperty(
                            name          = "Convert parent transformations",
                            description   = "Convert parent transformation to the object",
                            default       = False)
    
    pathMode = path_reference_mode

    check_extension = True

    def execute(self, context) :
        if not self.filepath :
            raise Exception("Filepath not set")
        
        from . import export_xml3d
        exporter = export_xml3d.XML3DExporterHelper(self.filepath, self.onlySelected, self.exportCameras, self.applyModifiers, self.pathMode, self.annotatePhysics, self.writeHTMLHeader, self.ignoreLamps, self.useRaytracing, self.convertParenting)
        exporter.write()

        return {'FINISHED'}

    def invoke(self, context, event) :
        if not self.filepath :
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".xhtml")
        self.pathMode = 'RELATIVE'
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_export(self, context) :
    self.layout.operator(XML3DExporter.bl_idname, text="XML3D (.xhtml)")


def register() :
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister() :
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
