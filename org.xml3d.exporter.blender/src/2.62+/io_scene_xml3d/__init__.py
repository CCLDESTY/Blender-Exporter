# <pep8 compliant>


bl_info = {
    "name"          : "XML3D (.xml3d)",
    "author"        : "Nicolas Göddel",
    "version"       : (12, 2),
    "blender"       : (2, 5, 6),
    "api"           : 36103,
    "location"      : "File > Export > XML3D (.xml3d) ",
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

class XML3DExporter(bpy.types.Operator):
    '''Save XML3D'''
    bl_idname = ".xml3d"
    bl_label = "Export XML3D"

    filename        = StringProperty(
                            name          = "File Path",
                            description   = "Filepath used for exporting the XML3D file",
                            maxlen        = 1024,
                            subtype       = 'FILENAME')
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
    useRelativePath = BoolProperty(
                            name          = "Use relative path",
                            description   = "Use relative paths for the textures",
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
                            name             = "Ignore Lamps",
                            description   = "Ignore Lamps",
                            default       = False) 
    useRaytracing   = BoolProperty(
                            name             = "Use Raytracing",
                            description   = "Use Raytracing for the xml3d node",
                            default       = True)
    convertParenting = BoolProperty(
                            name          = "Convert parent transformations",
                            description   = "Convert parent transformation to the object",
                            default       = False)

    def execute(self, context):
        from . import export_xml3d
        exporter = export_xml3d.XML3DExporterHelper(self.filename, self.onlySelected, self.exportCameras, self.applyModifiers, self.useRelativePath, self.annotatePhysics, self.writeHTMLHeader, self.ignoreLamps, self.useRaytracing, self.convertParenting)
        exporter.write()

        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filename :
            self.filename = bpy.path.ensure_ext(bpy.data.filepath, ".xhtml")
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_export(self, context) :
    self.layout.operator(XML3DExporter.bl_idname, text="XML3D (.xml3d)")


def register() :
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister() :
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
