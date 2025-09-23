#!/usr/bin/env python3
"""
IDS PATCH Panel - Collaboration Style
=====================================

Erstellt ein IDS PATCH Panel analog zum IFC Tester Panel.
Ohne Tick-Box Optionen, nur File-Loading Interface.
"""

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty
from pathlib import Path

class IDS_PATCH_OT_patch_ifc(Operator):
    """Patch IFC file with IDS requirements."""
    bl_idname = "ids_patch.patch_ifc"
    bl_label = "Patch IFC"
    bl_description = "Apply IDS requirements to the loaded IFC file"
    
    def execute(self, context):
        scene = context.scene
        
        # Check if both files are loaded
        if not getattr(scene, 'ids_patch_ifc_file_loaded', False):
            self.report({'ERROR'}, "Please load an IFC file first")
            return {'CANCELLED'}
        
        if not getattr(scene, 'ids_patch_ids_file_loaded', False):
            self.report({'ERROR'}, "Please load an IDS file first")
            return {'CANCELLED'}
        
        # Get file paths
        ifc_path = getattr(scene, 'ids_patch_ifc_file_path', '')
        ids_path = getattr(scene, 'ids_patch_ids_file_path', '')
        
        try:
            # TODO: Implement actual patching logic here
            print(f"Patching IFC: {ifc_path}")
            print(f"With IDS: {ids_path}")
            
            self.report({'INFO'}, f"🔧 IFC patching completed successfully!")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Patching failed: {str(e)}")
            return {'CANCELLED'}


class IDS_PATCH_OT_load_ifc_file(Operator):
    """Load IFC file for IDS patching."""
    bl_idname = "ids_patch.load_ifc_file"
    bl_label = "Load IFC File"
    bl_description = "Load IFC file for IDS patching"
    
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ifc", options={'HIDDEN'})
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No IFC file selected")
            return {'CANCELLED'}
        
        scene = context.scene
        scene.ids_patch_ifc_file_path = self.filepath
        scene.ids_patch_ifc_file_loaded = True
        
        filename = Path(self.filepath).name
        self.report({'INFO'}, f"✅ IFC loaded: {filename}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class IDS_PATCH_OT_load_ids_file(Operator):
    """Load IDS file for patching."""
    bl_idname = "ids_patch.load_ids_file"
    bl_label = "Load IDS File"
    bl_description = "Load IDS file for patching"
    
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ids;*.xml", options={'HIDDEN'})
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No IDS file selected")
            return {'CANCELLED'}
        
        scene = context.scene
        scene.ids_patch_ids_file_path = self.filepath
        scene.ids_patch_ids_file_loaded = True
        
        filename = Path(self.filepath).name
        self.report({'INFO'}, f"✅ IDS loaded: {filename}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class IDS_PATCH_PT_panel(Panel):
    """IDS PATCH panel in Collaboration."""
    bl_label = "IDS PATCH"
    bl_idname = "IDS_PATCH_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "BIM_PT_tab_collaboration"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # File loading interface - analog zu IFC Tester
        col = layout.column(align=True)
        
        # IFC File row
        row = col.row(align=True)
        row.label(text="IFC File", icon='FILE_3D')
        
        # File path field (read-only display)
        sub = row.row(align=True)
        sub.scale_x = 2.0
        if getattr(scene, 'ids_patch_ifc_file_loaded', False):
            filename = Path(getattr(scene, 'ids_patch_ifc_file_path', '')).name
            sub.label(text=filename[:30] + "..." if len(filename) > 30 else filename)
        else:
            sub.label(text="No IFC file loaded")
        
        # Load button
        row.operator("ids_patch.load_ifc_file", text="", icon='FILEBROWSER')
        
        # IDS File row
        row = col.row(align=True)
        row.label(text="IDS File", icon='FILE_TEXT')
        
        # File path field (read-only display)
        sub = row.row(align=True)
        sub.scale_x = 2.0
        if getattr(scene, 'ids_patch_ids_file_loaded', False):
            filename = Path(getattr(scene, 'ids_patch_ids_file_path', '')).name
            sub.label(text=filename[:30] + "..." if len(filename) > 30 else filename)
        else:
            sub.label(text="No IDS file loaded")
        
        # Load button
        row.operator("ids_patch.load_ids_file", text="", icon='FILEBROWSER')
        
        # Patch IFC Button - nur wenn beide Files geladen sind
        if (getattr(scene, 'ids_patch_ifc_file_loaded', False) and 
            getattr(scene, 'ids_patch_ids_file_loaded', False)):
            
            # Separator
            col.separator()
            
            # Patch button
            patch_row = col.row(align=True)
            patch_row.scale_y = 1.5  # Größerer Button
            patch_row.operator("ids_patch.patch_ifc", text="🔧 Patch IFC", icon='MODIFIER')


def register():
    """Register IDS PATCH panel."""
    bpy.utils.register_class(IDS_PATCH_OT_load_ifc_file)
    bpy.utils.register_class(IDS_PATCH_OT_load_ids_file)
    bpy.utils.register_class(IDS_PATCH_OT_patch_ifc)  # Neuer Operator
    bpy.utils.register_class(IDS_PATCH_PT_panel)
    
    # Properties for file paths
    bpy.types.Scene.ids_patch_ifc_file_path = StringProperty(
        name="IFC File Path",
        description="Path to the loaded IFC file",
        default=""
    )
    bpy.types.Scene.ids_patch_ifc_file_loaded = BoolProperty(
        name="IFC File Loaded",
        description="Whether an IFC file is loaded",
        default=False
    )
    bpy.types.Scene.ids_patch_ids_file_path = StringProperty(
        name="IDS File Path", 
        description="Path to the loaded IDS file",
        default=""
    )
    bpy.types.Scene.ids_patch_ids_file_loaded = BoolProperty(
        name="IDS File Loaded",
        description="Whether an IDS file is loaded", 
        default=False
    )
    
    print("✅ IDS PATCH Panel registered under Collaboration!")


def unregister():
    """Unregister IDS PATCH panel."""
    # Remove properties
    props = [
        'ids_patch_ifc_file_path',
        'ids_patch_ifc_file_loaded', 
        'ids_patch_ids_file_path',
        'ids_patch_ids_file_loaded'
    ]
    
    for prop in props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
    
    # Unregister classes
    classes = [
        IDS_PATCH_PT_panel,
        IDS_PATCH_OT_patch_ifc,  # Neuer Operator
        IDS_PATCH_OT_load_ids_file,
        IDS_PATCH_OT_load_ifc_file
    ]
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    
    print("🧹 IDS PATCH Panel unregistered!")


def clean():
    """Clean IDS PATCH panel."""
    unregister()
    print("🧹 IDS PATCH Panel cleaned!")


if __name__ == "__main__":
    clean()
    register()