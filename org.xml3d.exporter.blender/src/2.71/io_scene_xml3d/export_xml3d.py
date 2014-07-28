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

__author__ = ["Nicolas Göddel"]
__version__ = '12.02'
__bpydoc__ = """\
"""

import bpy
import array
from . import xml3d
import sys
import time
import os
#from Blender import Mesh, Window, Mathutils, Material #@UnresolvedImport
import mathutils
import bpy_extras.io_utils

DEG2RAD = 0.017453292519943295
RAD2DEG = 57.295779513082323

class Vertex :
    index = None
    normal = None
    texcoord = None
    color = None
    
    def veckey3d(self, v) :
        if v == None :
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8), round(v[2], 8)))

    def veckey2d(self, v):
        if v == None:
            return None
        return mathutils.Vector((round(v[0], 8), round(v[1], 8)))

    def __init__(self, index, normal = None, texcoord = None, color = None):
        self.index = index
        self.normal = self.veckey3d(normal)
        self.texcoord = self.veckey2d(texcoord)
    
    def __str__( self ) :
        return "i: " + str(self.index) + ", n: " + str(self.normal) + ", t: " + str(self.texcoord)
 
    def __cmp__(self, other):
        "Currently not used as __eq__ has higher priority"
        #print("Compare")
        if self.index < other.index:
            return -1;
        if self.index > other.index:
            return 1;
        
        if self.normal != other.normal:
            if self.normal == None:
                return -1;
            if other.normal == None:
                return 1;
            return cmp(self.normal, other.normal)

        if self.texcoord != other.texcoord:
            if self.texcoord == None:
                return -1;
            if other.texcoord == None:
                return 1;
            return cmp(self.texcoord, other.texcoord)

        return 0;
 
    def __hash__( self ) :
        return self.index
                   
    def __eq__(self, other):
        return self.index == other.index and self.normal == other.normal and self.texcoord == other.texcoord

def appendUnique(mlist, value):
    if value in mlist :
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True  

class XML3DExporterHelper :
    
    noMaterialAppeared = False
    doc = None
    
    def __init__(self, filepath, onlySelected, exportCameras, applyModifiers,
                 pathMode, annotatePhysics, writeHTMLHeader, ignoreLamps,
                 useRaytracing, convertParenting) :
        self.filepath = filepath
        self.onlySelected = onlySelected
        self.exportCameras = exportCameras
        self.applyModifiers = applyModifiers
        self.pathMode = pathMode
        self.annotatePhysics = annotatePhysics
        self.writeHTMLHeader = writeHTMLHeader
        self.ignoreLamps = ignoreLamps
        self.useRaytracing = useRaytracing
        self.convertParenting = convertParenting
        self.withGUI = True
    
    def writeMeshObject(self, obj) :
        mesh = obj.data

        group = self.doc.createGroupElement(obj.name)
        group.setTransform("#t_" + obj.name)

        if self.annotatePhysics :
            group.setAttribute("physics-material", "#phy_" + obj.name)
        
        materialCount = len(mesh.materials)
        if materialCount == 0 :
            group.setShader("#noMat")
            meshElem = self.doc.createMeshElement(None, None, "triangles", "#mesh_" + mesh.name + "_noMat")
            group.appendChild(meshElem)
        else :
            for materialIndex, material in enumerate(mesh.materials) :
                materialName = "noMat%d" % (materialIndex)
                if material :
                    materialName = material.name
                
                subgroup = self.doc.createGroupElement(shader_ = "#" + materialName)
                group.appendChild(subgroup)
                meshElem = self.doc.createMeshElement(type_ = "triangles")
                meshElem.setSrc("#mesh_" + mesh.name + "_" + materialName)
                subgroup.appendChild(meshElem)
        
        return group
            
    def writeMeshData(self, parent, mesh, meshName = None) :
        if len(mesh.faces) == 0 :
            return
        
        if not meshName :
            meshName = mesh.name
        
        print("Writing mesh %s" % meshName)
        
        # Mesh indices
        singleMaterialName = ""
        materialCount = len(mesh.materials)
        if materialCount == 1 :
             singleMaterialName = "_" + mesh.materials[0].name
        elif materialCount == 0 :
            singleMaterialName = "_noMat"
            materialCount = 1
        
        # Speichert für jedes Material die entsprechenden Vertexindices
        indices = [[] for m in range(materialCount)] #@UnusedVariable
        # Speichert alle Vertices des Meshes in einer aufbereiteten Form
        vertices = []
        # Stellt sicher, dass keine Vertices doppelt aufgenommen werden
        vertex_dict = {}
       
        print("Faces: %i" % len(mesh.faces))
        
        uvTexture = mesh.uv_textures.active
        if uvTexture :
            print("Active UV Texture: " + uvTexture.name)
        
        #meshTextureFaceLayerData = None
        #if mesh.tessface_uv_textures.active :
        #    meshTextureFaceLayerData = mesh.tessface_uv_textures.active.data
        
        i = 0
        for faceIndex, face in enumerate(mesh.faces) :
            mv = None
            uvFace = None
            if uvTexture and uvTexture.data[faceIndex] :
                uvFaceData = uvTexture.data[faceIndex]
                uvFace = uvFaceData.uv1, uvFaceData.uv2, uvFaceData.uv3, uvFaceData.uv4
            
            newFaceVertices = []
            
            for i, vertexIndex in enumerate(face.vertices) :
                if face.use_smooth :
                    if uvFace :
                        mv = Vertex(vertexIndex, mesh.vertices[vertexIndex].normal, uvFace[i])
                    else :
                        mv = Vertex(vertexIndex, mesh.vertices[vertexIndex].normal, None)
                else :
                    if uvFace :
                        meshTexturePolyLayer = mesh.uv_textures.active
                        mv = Vertex(vertexIndex, face.normal, uvFace[i])
                    else:
                        mv = Vertex(vertexIndex, face.normal)
                
                index, added = appendUnique(vertex_dict, mv)
                newFaceVertices.append(index)
                #print("enumerate: %d -> %d (%d)" % (i, vertexIndex, index))
                if added :
                    vertices.append(mv)
            
            if len(newFaceVertices) == 3 :
                for vertexIndex in newFaceVertices :
                    indices[face.material_index].append(vertexIndex)
            elif len(newFaceVertices) == 4 :
                #print("4 vertices found")
                indices[face.material_index].append(newFaceVertices[0])
                indices[face.material_index].append(newFaceVertices[1])
                indices[face.material_index].append(newFaceVertices[2])
                indices[face.material_index].append(newFaceVertices[2])
                indices[face.material_index].append(newFaceVertices[3])
                indices[face.material_index].append(newFaceVertices[0])

        data = self.doc.createDataElement("mesh_" + meshName + singleMaterialName, None, None, None, None)    
        parent.appendChild(data)
        
        # Vertex positions
        value_list = []
        for v in vertices :
            value_list.append("%.6f %.6f %.6f" % tuple(mesh.vertices[v.index].co))
                
        valueElement = self.doc.createFloat3Element(None, "position")
        valueElement.setValue(' '.join(value_list))
        data.appendChild(valueElement)
        
        # Vertex normals
        value_list = []
        for v in vertices :
            value_list.append("%.6f %.6f %.6f" % tuple(v.normal))
     
        valueElement = self.doc.createFloat3Element(None, "normal")
        valueElement.setValue(' '.join(value_list))
        data.appendChild(valueElement)
        
        # Vertex texCoord
        if uvTexture :
            value_list = []
            for v in vertices :
                if v.texcoord :
                    value_list.append("%.6f %.6f" % tuple(v.texcoord))
                else :
                    value_list.append("0.0 0.0")
    
            valueElement = self. doc.createFloat2Element(None, "texcoord")
            valueElement.setValue(' '.join(value_list))
            data.appendChild(valueElement);
        
        # Single or no material: write all in one data block
        if materialCount <= 1 :
            valueElement = self.doc.createIntElement(None, "index")
            valueElement.setValue(' '.join(map(str, indices[0])))
            data.appendChild(valueElement)
        elif materialCount > 1 :
            for materialIndex, material in enumerate(mesh.materials) :
                if len(indices[materialIndex]) == 0:
                    continue
                
                if material :
                    materialName = material.name
                else :
                    materialName = "noMat%d" % (materialIndex)
                    self.noMaterialAppeared = True
                
                data = self.doc.createDataElement("mesh_" + meshName + "_" + materialName)    
                parent.appendChild(data)

                refdata = self.doc.createDataElement(src_ = "#mesh_" + meshName)
                data.appendChild(refdata)

                valueElement = self.doc.createIntElement(None, "index")
                valueElement.setValue(' '.join(map(str, indices[materialIndex])))
                data.appendChild(valueElement)
       
    def writeMainDef(self, parent) :
        defElement = self.doc.createDefsElement("mainDef")
        defElement.setIdAttribute( "id" )
        
        parent.appendChild(defElement)
        
        meshes, lights, unknownParents = {}, {}, {}
        
        old_objmode = None
        
        if self.onlySelected :
            objects = bpy.context.selected_objects
            print("Selected Objects: %i" % len(objects))
        else :
            objects = bpy.context.scene.objects
            print("Objects: %i" % len(objects))
            
        for obj in objects :
            
            if obj.users == 0 :
                continue
            
            if obj.mode != 'OBJECT' :
                old_objmode = obj.mode
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            
            objType = obj.type
            
            if objType == 'MESH' or objType == 'CURVE' :
                dataName = obj.data.name
                mesh = obj.to_mesh(self.scene, self.applyModifiers, 'RENDER')
                #print("%s found: %s" % (objType, dataName))
                meshes[dataName] = mesh
                self.writeTransform(defElement, obj)
            elif objType == 'LAMP' and (not self.ignoreLamps) :
                dataName = obj.data.name
                light = obj.data
                #print("LAMP found: " + dataName)
                lights[dataName] = light
                self.writeTransform(defElement, obj)
            else :
                continue
            
            unknownParents[obj.name] = None
            while not (obj.parent == None) :
                if not (obj.parent.name in unknownParents) :
                    unknownParents[obj.parent.name] = obj.parent
                obj = obj.parent
            
        if not self.convertParenting :
            for objName in unknownParents :
                if not (unknownParents[objName] == None) :
                    self.writeTransform(defElement, unknownParents[objName])
        
        for meshName in meshes :
            mesh = meshes[meshName]
            self.writeMeshData(defElement, mesh, meshName)
            del mesh
            #TODO
            if (self.annotatePhysics):
                self.writePhysicsMaterial(defElement, mesh);
        
        for lightName in lights :
            light = lights[lightName]
            self.writeLightShader(defElement, light)
            
        for material in bpy.data.materials :
            if material.users > 0 :
                self.writePhongShader(defElement, material)
        
        if self.noMaterialAppeared :
            self.writeDefaultShader(defElement)
        
        if old_objmode :
            bpy.ops.object.mode_set(mode=old_objmode, toggle=False)
    
    def writeTransform(self, parent, obj) :
        #try:
            matrix = None
            if self.convertParenting :
                matrix = obj.matrix_world
            else :
                matrix = obj.matrix_basis
            axis, angle = matrix.to_quaternion().to_axis_angle()
            location = matrix.to_translation()
            scale = matrix.to_scale()
            #print("%s: %.6f %.6f %.6f %.6f" % (obj.name, quat[1], quat[2], quat[3], quat[0]))

            transform = self.doc.createTransformElement("t_" + obj.name)
            transform.setTranslation("%.6f %.6f %.6f" % (location.x, location.y, location.z))
            transform.setScale("%.6f %.6f %.6f" % (scale.x, scale.y, scale.z))
            transform.setRotation("%.6f %.6f %.6f %.6f" % (axis.x, axis.y, axis.z, angle))

            parent.appendChild(transform)
        #except AttributeError:
            #print("Warning object has no name and got no transform")
        
    def writePhysicsMaterial(self, parent, mesh):
        
        mat = self.doc.createElement("physics:material")
        mat.setAttribute("id", "phy_" + mesh.name)
        parent.appendChild(mat)        
        
        # Set the actor type
        type = self.doc.createElement("string")
        type.setAttribute("name", "type")
        type.appendChild(self.doc.createTextNode("dynamic"))
        mat.appendChild(type)

        materials = mesh.materials
        if (len(materials) and materials[0] != None) :
            # Set the friction
            frictionElement = self.doc.createElement("float")
            frictionElement.setAttribute("name", "friction")
            frictionElement.appendChild(self.doc.createTextNode(str(materials[0].rbFriction)))
            mat.appendChild(frictionElement)
    
            # Set the restitution
            restitutionElement = self.doc.createElement("float")
            restitutionElement.setAttribute("name", "restitution")
            restitutionElement.appendChild(self.doc.createTextNode(str(materials[0].rbRestitution)))
            mat.appendChild(restitutionElement)

    def writeLightShader(self, parent, light):
        # TODO: Directional Light
        # Specification: http://www.xml3d.org/xml3d/specification/current/lightshader.html
        if (light.type == 'SPOT') : #TODO
            lightShaderElement = self.doc.createLightshaderElement("ls_" + light.name, "urn:xml3d:lightshader:spot")
            
            if light.use_square :
                print("WARNING: Square formed spot light not supported. Using circle form insted.")
            
            if light.use_halo :
                print("WARNING: Halo rendering of a spot light not supported. Ignoring.")
            
            valueElement = self.doc.createBoolElement(None, "beamWidth")
            valueElement.setValue("%f" % (light.spot_size * RAD2DEG * (1.0 - light.spot_blend)))
            lightShaderElement.appendChild(valueElement)
            
            valueElement = self.doc.createBoolElement(None, "cutOffAngle")
            valueElement.setValue("%f" % (light.spot_size * RAD2DEG * light.spot_blend))
            lightShaderElement.appendChild(valueElement)
            
            valueElement = self.doc.createFloat3Element(None, "direction")
            valueElement.setValue("0 0 -1")
            lightShaderElement.appendChild(valueElement)
            
        elif (light.type == 'SUN') : #TODO
            print("WARNING: SUN Lamp type not supported yet. Ignoring.")
            return
        elif (light.type == 'POINT') :                  
            lightShaderElement = self.doc.createLightshaderElement("ls_" + light.name, "urn:xml3d:lightshader:point")
            parent.appendChild(lightShaderElement)
        
        else :
            return
        
        parent.appendChild(lightShaderElement)
            
        valueElement = self.doc.createBoolElement(None, "castShadow")
        if light.shadow_method == 'RAY_SHADOW' :
            valueElement.setValue("true")
        else:
            valueElement.setValue("false")
        lightShaderElement.appendChild(valueElement)
        
        attens = [1.0, 0.0, 0.0]
        if light.falloff_type == 'CONSTANT' :
            attens = [1.0, 0.0, 0.0]
        elif light.falloff_type == 'INVERSE_LINEAR' :
            attens = [1.0, 1.0 / light.distance, 0.0]
        elif light.falloff_type == 'INVERSE_SQUARE' :
            attens = [1.0, 0.0, 1.0 / (light.distance * light.distance)]
        elif light.falloff_type == 'LINEAR_QUADRATIC_WEIGHTED' :
            attens = [1.0, light.linear_attenuation, light.quadratic_attenuation]
        else :
            print("WARNING: light falloff type not supported: " + light.falloff_type + ". Using CONSTANT instead.")
        
        valueElement = self.doc.createFloat3Element(None, "attenuation")
        valueElement.setValue("%f %f %f" % tuple(attens))
        lightShaderElement.appendChild(valueElement)
        
        valueElement = self.doc.createFloat3Element(None, "intensity")
        lightColor = light.color * light.energy
        valueElement.setValue("%f %f %f" % (lightColor[0], lightColor[1], lightColor[2]))
        lightShaderElement.appendChild(valueElement)
        
    def writeDefaultShader(self, parent) :
        shaderElement = self.doc.createShaderElement("s_noMat", "urn:xml3d:shader:phong");

        valueElement = self.doc.createFloat3Element(None, "diffuseColor")
        valueElement.setValue("0.3 0.3 0.3")
        shaderElement.appendChild(valueElement)
        
        valueElement = self.doc.createFloatElement(None, "ambientIntensity")
        valueElement.setValue("0.2")
        shaderElement.appendChild(valueElement)

        parent.appendChild(shaderElement)
        
    def writePhongShader(self, parent, material) :
        
        if material.specular_shader != 'PHONG' :
            print("WARNING: %s shader not supported. Using PHONG instead." % (material.specular_shader))
        
        shaderElement = self.doc.createShaderElement(material.name, "urn:xml3d:shader:phong");
        parent.appendChild(shaderElement)
        
        #TODO
        print("Write Material: " + material.name)
        hasTexture = False
        for textureIndex, texture in enumerate(material.texture_slots) :
            if not material.use_textures[textureIndex] or texture == None:
                continue
            
            if texture.texture_coords != 'UV' :
                print("WARNING: %s texture coordinates not supported. Using UV insted." % (texture.texture_coords))
            
            if not texture.use_map_color_diffuse or texture.diffuse_color_factor < 0.0001 :
                continue
            
            if texture.texture.type != 'IMAGE' :
                print("WARNING: %s not supported as texture type. Ignoring texture!" % (texture.texture.type))
                continue
                
            source = texture.texture.image.source
            if not (source == 'FILE' or source == 'VIDEO') :
                print("WARNING: %s not supported as image source. Ignoring texture!" % (source))
                continue
            
            imageFileName = bpy_extras.io_utils.path_reference(texture.texture.image.filepath,
                                                               os.path.dirname(bpy.data.filepath),
                                                               os.path.dirname(self.filepath),
                                                               self.pathMode,
                                                               "",
                                                               self.copySet,
                                                               texture.texture.image.library)
            
            textureElement = self.doc.createTextureElement(None, "diffuseTexture")
            img = self.doc.createImgElement(None, imageFileName)
            textureElement.appendChild(img)
            shaderElement.appendChild(textureElement)
            hasTexture = True
            
            valueElement = self.doc.createFloat3Element(None, "diffuseColor")
            #fac = 1.0 - mtex.colfac
            #valueElement.setValue("%f %f %f" % (material.rgbCol[0] * fac, material.rgbCol[1] * fac, material.rgbCol[2] * fac))
            valueElement.setValue("1 1 1")
            shaderElement.appendChild(valueElement)
            break;
            
        if not hasTexture:
            valueElement = self.doc.createFloat3Element(None, "diffuseColor")
            valueElement.setValue("%f %f %f" % tuple(material.diffuse_color))
            shaderElement.appendChild(valueElement)
        
        # AMBIENT INTENSITY
        ambientColor = self.scene.world.ambient_color #TODO Blender.World.GetCurrent()
        valueElement = self.doc.createFloatElement(None, "ambientIntensity")
        if ambientColor :
            valueElement.setValue(str(material.ambient * ambientColor.v))
        else :
            valueElement.setValue(str(material.ambient))
            
        shaderElement.appendChild(valueElement)
        
        # EMISSIVE COLOR
        if material.emit > 0.0001:
            valueElement = self.doc.createFloat3Element(None, "emissiveColor")
            valueElement.setValue("%f %f %f" % (material.diffuse_color[0] * material.emit, material.diffuse_color[1] * material.emit, material.diffuse_color[2] * material.emit))
            shaderElement.appendChild(valueElement)
        
        # SPECULAR COLOR
        valueElement = self.doc.createFloat3Element(None, "specularColor")
        valueElement.setValue("%f %f %f" % 
                          ((material.specular_color[0] * material.specular_intensity),
                           (material.specular_color[1] * material.specular_intensity),
                           (material.specular_color[2] * material.specular_intensity)))
        shaderElement.appendChild(valueElement)
        
        # SHININESS / SPECULAR HARDNESS
        valueElement = self.doc.createFloatElement(None, "shininess")
        valueElement.setValue(str(material.specular_hardness / 511.0))
        shaderElement.appendChild(valueElement)
        
        # TRANSPARENCY
        if (material.alpha < 9.9999 and material.use_transparency):
            valueElement = self.doc.createFloatElement(None, "transparency")
            valueElement.setValue(str(1.0 - material.alpha))
            shaderElement.appendChild(valueElement)
        
        # REFLECTION
        if material.raytrace_mirror.use :
            valueElement = self.doc.createFloat3Element(None, "reflective")
            valueElement.setValue("%f %f %f" % (material.mirror_color[0], material.mirror_color[1], material.mirror_color[2])) 
            shaderElement.appendChild(valueElement)
        
    def writeHeader(self) :
        doc = self.doc
        html = doc.createElementNS("http://www.w3.org/1999/xhtml", "html")
        html.setAttribute("xmlns", "http://www.w3.org/1999/xhtml")
        html.setAttribute("xmlns:webgl", "http://www.xml3d.org/2009/xml3d/webgl")
        html.setAttribute("xmlns:x3d", "http://www.web3d.org/specifications/x3d-namespace")
        doc.appendChild(html)
        
        head = doc.createElement("head")
        html.appendChild(head)
        
        link = doc.createElement("link")
        link.setAttribute("rel", "stylesheet")
        link.setAttribute("type", "text/css")
        link.setAttribute("media", "all")
        link.setAttribute("href", "http://www.xml3d.org/xml3d/script/xml3d.css")
        head.appendChild(link)
        
        body = doc.createElement("body")
        html.appendChild(body)
        header = doc.createElement("h1")
        header.appendChild(doc.createTextNode(bpy.data.filepath))
        body.appendChild(header)
        
        div = doc.createElement("div")
        body.appendChild(div)

        return div
    
    
    def writeScripts(self, parent):
        location = "http://www.xml3d.org/xml3d/script/"
        scripts = ["xml3d.js"]
      
        for script in scripts:
            scriptElem = self.doc.createScriptElement(None, location + script, "text/javascript")
            parent.appendChild(scriptElem)
      
    def writeLight(self, obj):
        group = self.doc.createGroupElement()
        group.setTransform("#t_%s" % obj.name)
        
        light = self.doc.createLightElement();
        light.setShader("#ls_%s" % obj.data.name)
        group.appendChild(light)
        
        return group
        
    def writeSceneGraph(self, parent) :
        if self.onlySelected :
            objects = bpy.context.selected_objects
        else :
            objects = bpy.context.scene.objects
        
        groups = {}
        objetNames = []
        
        for obj in objects :
            if obj.hide_render :
                continue
            
            if obj.type == 'MESH' :
                groups[obj.name] = obj, self.writeMeshObject(obj)
                objetNames.append(obj.name)
            elif obj.type == 'LAMP' and (not self.ignoreLamps) :
                groups[obj.name] = obj, self.writeLight(obj)
                objetNames.append(obj.name)
        
        for objName in objetNames :
            obj, group = groups[objName]
            if self.convertParenting :
                parent.appendChild(group)
            else :
                while not (obj.parent == None) :
                    if obj.parent.name in groups :
                        pObj, pGroup = groups[obj.parent.name]
                        pGroup.appendChild(group)
                        break
                    
                    pGroup = self.doc.createGroupElement(obj.parent.name)
                    pGroup.setTransform("#t_" + obj.parent.name)
                    pGroup.appendChild(group)
                    groups[obj.parent.name] = None, pGroup
                    group = pGroup
                    obj = obj.parent
                
                if (obj.parent == None) :
                    parent.appendChild(group)
        
        
    def writeViews(self, parent):
        if len(bpy.data.cameras) == 0 :
            view = self.doc.createViewElement("defaultView")
            parent.appendChild(view)
        else :
            for obj in bpy.data.objects :
                if obj.type == 'CAMERA' :
                    if obj.data.type != 'PERSP' :
                        print("WARNING: Other camera types than PERSP not supported. Skipping %s." % obj.name)
                        continue
                    
                    view = self.doc.createViewElement(obj.name);
                    matrix = None
                    if self.convertParenting :
                        matrix = obj.matrix_world
                    else :
                        matrix = obj.matrix_basis
                    
                    axis, angle = matrix.to_quaternion().to_axis_angle()
                    location = matrix.to_translation()
                    view.setPosition("%.6f %.6f %.6f" % (location.x, location.y, location.z))
                    view.setOrientation("%.6f %.6f %.6f %.6f" % (axis.x, axis.y, axis.z, angle))
                    view.setFieldOfView("%.6f" % obj.data.angle)
                    parent.appendChild(view)
      
    def write(self) :
        self.doc = xml3d.XML3DDocument()
        self.scene = bpy.context.scene
        self.copySet = set()
        
        print('--> START: Exporting XML3D to %s' % self.filepath)
        start_time = time.time()
        try:
            out = open(self.filepath, 'w')
        except:
            print('ERROR: Could not open %s' % self.filepath)
            return False
      
        divElem = None
        if self.writeHTMLHeader :
            divElem = self.writeHeader()
    
        world = self.scene.world
        
        view = None
        if self.exportCameras :
            if self.scene.camera :
                view = "#" + self.scene.camera.name
            else :
                firstCameraObj = None
                for obj in bpy.data.objects :
                    if obj.type == 'CAMERA' :
                        firstCameraObj = object
                        break
                if firstCameraObj :
                    print("WARNING: No active camera found. Using '%s' instead." % firstCameraObj.name)
                    view = "#" + firstCameraObj.name
                else :
                    print("WARNING: No camera found. Using a default view instead.")
                    view = "#defaultView"
        
        xml3dElem = self.doc.createXml3dElement(activeView_ = view)
        xml3dElem.setAttribute("xmlns", "http://www.xml3d.org/2009/xml3d")
        xml3dElem.setAttribute("webgl:showLog", "true")
        if self.annotatePhysics:
            xml3dElem.setAttribute("xmlns:physics", "http://www.xml3d.org/2010/physics")
            gravity = scene.gravity
            xml3dElem.setAttribute("physics:gravity", "%.6f %.6f %.6f" % (gravity[0], gravity[1], -gravity[2]))
        
        if self.exportCameras :
            renderSettings = self.scene.render
            resolution = renderSettings.resolution_x * renderSettings.resolution_percentage / 100, renderSettings.resolution_y * renderSettings.resolution_percentage / 100
            
            style = "width: %ipx; height: %ipx;" % (resolution[0], resolution[1])
            if world :
                bgColor = world.horizon_color
                style += " background-color:rgb(%i,%i,%i);" % (bgColor[0] * 255, bgColor[1] * 255, bgColor[2] * 255)
            
            xml3dElem.setAttribute("style", style)
            if self.useRaytracing :
                xml3dElem.setAttribute("renderer", "rtpie")
    
        if divElem :
            divElem.appendChild(xml3dElem)
            self.writeScripts(divElem)
        else :
            self.doc.appendChild(xml3dElem)
      
        self.writeMainDef(xml3dElem)
      
        if self.exportCameras :
            self.writeViews(xml3dElem)
      
        self.writeSceneGraph(xml3dElem)
    
        self.doc.writexml(out, "", "\t", "\n", "UTF-8")
    
        out.close()
        
        bpy_extras.io_utils.path_reference_copy(self.copySet)
        
        print('--> END: Exporting XML3D. Duration: %.2f' % (time.time() - start_time))
        return

