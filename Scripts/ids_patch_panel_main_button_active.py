#!/usr/bin/env python3
"""
IDS PATCH Panel - Collaboration Style
=====================================

Erstellt ein IDS PATCH Panel analog zum IFC Tester Panel.
Mit integrierter IFC Property Fix Funktionalität.
"""

import bpy
import json
import ifcopenshell
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty
from pathlib import Path


# IFC Property Fix Functions (from IFC_fix_properties.py)
def read_json_config(ifc_type, json_config):
    if ifc_type in json_config:
        return json_config[ifc_type]
    return None

def process_ifc_file(ifc_file, json_config):
    """Process IFC file with JSON configuration."""
    # Open the IFC file
    ifc_model = ifcopenshell.open(ifc_file)

    # Iterate through each IFC type in the JSON config
    for ifc_type, config in json_config.items():
        # Check if the IFC type exists in the model
        if ifc_model.by_type(ifc_type):
            instances = ifc_model.by_type(ifc_type)
            print(f"\nProcessing {len(instances)} instances of {ifc_type}")

            # Print all property values for each instance
            for instance in instances:
                print(f"\nInstance ID: {instance.id()}")

                # Check if the instance has the specified property set
                if 'IsDefinedBy' in dir(instance):
                    defined_by = instance.IsDefinedBy

                    # Iterate through each property set attached to the instance
                    for rel_defines in defined_by:
                        if rel_defines.is_a("IfcRelDefinesByProperties"):
                            property_set = rel_defines.RelatingPropertyDefinition

                            # Get the Property Set name
                            property_set_name = property_set.Name if 'Name' in dir(property_set) else "Unknown Property Set"

                            # Check if the property set is in the JSON config
                            if property_set_name in config['properties_values']:
                                # Print only the properties defined in the JSON config
                                print(f"\nProperty Set: {property_set_name}")

                                # check if Pset name should be replaced
                                if config['properties_values'][property_set_name].get('replace_name') is not None:
                                    # TODO: check if Pset with same name already exists
                                    print(f"Replace {property_set_name} by {config['properties_values'][property_set_name]['replace_name']}")
                                    property_set.Name = config['properties_values'][property_set_name]['replace_name']

                                # Iterate through each property in the property set
                                for property_single_value in property_set.HasProperties:
                                    handle_property_single_value(property_single_value, config['properties_values'][property_set_name])

    # Save the modified IFC model to a new file
    output_file = ifc_file.replace('.ifc', '_fixed.ifc')
    ifc_model.write(output_file)
    return output_file

def handle_property_single_value(property_single_value, properties_values):
    """Handle individual property value replacement."""
    property_name = property_single_value.Name
    if (properties_values.get(property_name) is not None and
            properties_values[property_name].get('replace_name') is not None):
        # TODO: check if Pset with same name already exists
        print(f"Replace {property_name} by {properties_values[property_name]['replace_name']}")
        property_single_value.Name = properties_values[property_name]['replace_name']

    if property_single_value.is_a("IfcPropertySingleValue"):
        # Check if NominalValue has a wrappedValue
        if property_single_value.NominalValue is not None and 'wrappedValue' in dir(property_single_value.NominalValue):
            property_value = property_single_value.NominalValue.wrappedValue

            # Check if the property is in the JSON config
            if property_name in properties_values:
                # Replace values based on the JSON config
                if properties_values[property_name].get('replace_values') is not None:
                    for old_value, new_value in properties_values[property_name]['replace_values'].items():
                        # Convert the old_value to the same type as property_value
                        old_value = type(property_value)(old_value)

                        if property_value == old_value:
                            # Print debugging information
                            print(f"Replacing {old_value} with {new_value} for Property: {property_name}")

                            # Convert the new_value to the same type as property_value
                            new_value = type(property_value)(new_value)
                            property_single_value.NominalValue.wrappedValue = new_value

class IDS_PATCH_OT_patch_ifc(Operator):
    """Patch IFC file with IDS requirements."""
    bl_idname = "ids_patch.patch_ifc"
    bl_label = "Patch IFC"
    bl_description = "Apply IDS match configuration to the loaded IFC file"
    
    def execute(self, context):
        scene = context.scene
        
        # Check if both files are loaded
        if not getattr(scene, 'ids_patch_ifc_file_loaded', False):
            self.report({'ERROR'}, "Please load an IFC file first")
            return {'CANCELLED'}
        
        if not getattr(scene, 'ids_patch_ids_file_loaded', False):
            self.report({'ERROR'}, "Please load an IDS match configuration first")
            return {'CANCELLED'}
        
        # Get file paths
        ifc_path = getattr(scene, 'ids_patch_ifc_file_path', '')
        ids_path = getattr(scene, 'ids_patch_ids_file_path', '')
        
        try:
            # Load JSON configuration
            with open(ids_path, 'r', encoding='utf-8') as json_file:
                json_config = json.load(json_file)
            
            print(f"Loaded JSON config: {json_config}")
            print(f"Patching IFC: {ifc_path}")
            print(f"With IDS patch configuration: {ids_path}")
            
            # Process IFC file with JSON config
            output_file = process_ifc_file(ifc_path, json_config)
            
            self.report({'INFO'}, f"🔧 IFC patching completed! Output: {Path(output_file).name}")
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
    """Load IDS patch file for patching."""
    bl_idname = "ids_patch.load_ids_file"
    bl_label = "Load IDS patch configuration"
    bl_description = "Load IDS configuration for patching"
    
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No IDS patch file selected")
            return {'CANCELLED'}
        
        scene = context.scene
        scene.ids_patch_ids_file_path = self.filepath
        scene.ids_patch_ids_file_loaded = True
        
        filename = Path(self.filepath).name
        self.report({'INFO'}, f"✅ IDS patch loaded: {filename}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class IDS_PATCH_PT_panel(Panel):
    """IDS PATCH panel in Collaboration."""
    bl_label = "IDS Patch"
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
        row.label(text="IDS Patch File", icon='FILE_TEXT')
        
        # File path field (read-only display)
        sub = row.row(align=True)
        sub.scale_x = 2.0
        if getattr(scene, 'ids_patch_ids_file_loaded', False):
            filename = Path(getattr(scene, 'ids_patch_ids_file_path', '')).name
            sub.label(text=filename[:30] + "..." if len(filename) > 30 else filename)
        else:
            sub.label(text="No IDS patch file loaded")
        
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
        name="IDS Patch File Path", 
        description="Path to the loaded IDS patch file",
        default=""
    )
    bpy.types.Scene.ids_patch_ids_file_loaded = BoolProperty(
        name="IDS Patch File Loaded",
        description="Whether an IDS patch file is loaded", 
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