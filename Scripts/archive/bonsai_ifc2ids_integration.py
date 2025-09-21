#!/usr/bin/env python3
"""
Bonsai IFC2IDS Integration
==========================

This module integrates the IFC2IDS converter into Bonsai (BlenderBIM) as a UI panel
and operator, allowing users to generate IDS specifications directly from their IFC models.

Installation:
1. Copy Ifc2Ids.py to: src/ifcpatch/ifcpatch/recipes/
2. Copy this file to: src/bonsai/bonsai/bim/module/ifcpatch/
3. Update the UI registration in the ifcpatch module

Usage:
- Open an IFC model in Bonsai
- Go to the IFC Patch panel
- Select "IFC2IDS Converter"
- Configure options and click "Generate IDS"
"""

import bpy
import bmesh
import ifcopenshell
import ifcopenshell.api
import ifcpatch
import os
import logging
from pathlib import Path
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty
import bonsai.bim.ifc
from bonsai.bim.prop import StrProperty, Attribute
from bonsai.bim.module.ifcpatch.data import IfcPatchData


class BIM_OT_execute_ifc2ids_patch(Operator):
    """Generate IDS specification from current IFC model"""
    bl_idname = "bim.execute_ifc2ids_patch"
    bl_label = "Generate IDS from IFC"
    bl_description = "Generate Information Delivery Specification (IDS) from the current IFC model"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Enable only when an IFC file is loaded."""
        return bonsai.bim.ifc.IfcStore.get_file() is not None

    def execute(self, context):
        """Execute the IFC2IDS conversion."""
        props = context.scene.BIMIfcPatchProperties
        
        # Get the current IFC file
        ifc_file = bonsai.bim.ifc.IfcStore.get_file()
        if not ifc_file:
            self.report({'ERROR'}, "No IFC file is currently loaded")
            return {'CANCELLED'}
        
        # Get output path
        output_path = props.ifc2ids_output_path
        if not output_path:
            # Default to same directory as IFC file with .ids extension
            ifc_path = bonsai.bim.ifc.IfcStore.get_path()
            if ifc_path:
                output_path = str(Path(ifc_path).with_suffix('.ids'))
            else:
                output_path = str(Path(bpy.path.abspath("//")).joinpath("output.ids"))
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Prepare arguments for the patch
            arguments = [
                output_path,
                props.ifc2ids_include_geometry,
                props.ifc2ids_specification_name or "Generated from Bonsai"
            ]
            
            # Execute the IFC2IDS patch
            patch_args = {
                "input": bonsai.bim.ifc.IfcStore.get_path() or "",
                "file": ifc_file,
                "recipe": "Ifc2Ids",
                "arguments": arguments
            }
            
            self.report({'INFO'}, f"Starting IDS generation...")
            
            # Execute the patch
            result = ifcpatch.execute(patch_args)
            
            # Report success
            self.report({'INFO'}, f"IDS specification generated successfully: {output_path}")
            
            # Update the output path property with the actual path used
            props.ifc2ids_output_path = output_path
            
            # Optionally open the output directory
            if props.ifc2ids_open_output:
                self._open_output_directory(output_path)
            
        except Exception as e:
            error_msg = f"Failed to generate IDS: {str(e)}"
            self.report({'ERROR'}, error_msg)
            print(f"IFC2IDS Error: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def _open_output_directory(self, output_path: str):
        """Open the output directory in the system file manager."""
        import subprocess
        import platform
        
        try:
            output_dir = str(Path(output_path).parent)
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(["explorer", output_dir])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", output_dir])
            elif system == "Linux":
                subprocess.run(["xdg-open", output_dir])
        except Exception as e:
            print(f"Could not open output directory: {e}")


class BIM_OT_select_ifc2ids_output_path(Operator):
    """Select output path for IDS file"""
    bl_idname = "bim.select_ifc2ids_output_path"
    bl_label = "Select Output Path"
    bl_description = "Select the output path for the IDS file"
    
    filename_ext = ".ids"
    filter_glob: StringProperty(default="*.ids", options={'HIDDEN'})
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        """Set the selected file path."""
        context.scene.BIMIfcPatchProperties.ifc2ids_output_path = self.filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """Invoke the file browser."""
        # Set default filename based on current IFC
        ifc_path = bonsai.bim.ifc.IfcStore.get_path()
        if ifc_path:
            default_name = Path(ifc_path).stem + ".ids"
            self.filepath = default_name
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BIM_PT_ifc2ids_patch(Panel):
    """Panel for IFC2IDS conversion in the IFC Patch interface"""
    bl_label = "IFC2IDS Converter"
    bl_idname = "BIM_PT_ifc2ids_patch"
    bl_parent_id = "BIM_PT_ifcpatch"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        """Show only when IFC Patch is available."""
        return bonsai.bim.ifc.IfcStore.get_file() is not None

    def draw(self, context):
        """Draw the panel interface."""
        layout = self.layout
        props = context.scene.BIMIfcPatchProperties
        
        # Info box
        box = layout.box()
        box.label(text="Generate IDS from Current IFC Model", icon='FILE_TEXT')
        
        col = box.column(align=True)
        col.label(text="Creates Information Delivery Specification")
        col.label(text="for validation and quality control")
        
        # Configuration section
        layout.separator()
        
        col = layout.column(align=True)
        col.label(text="Configuration:", icon='SETTINGS')
        
        # Specification name
        row = col.row()
        row.prop(props, "ifc2ids_specification_name", text="Specification Name")
        
        # Output path selection
        row = col.row()
        row.prop(props, "ifc2ids_output_path", text="Output Path")
        row.operator("bim.select_ifc2ids_output_path", text="", icon='FILE_FOLDER')
        
        # Options
        col.separator()
        col.prop(props, "ifc2ids_include_geometry", text="Include Geometric Requirements")
        col.prop(props, "ifc2ids_open_output", text="Open Output Directory After Generation")
        
        # Generation button
        layout.separator()
        
        col = layout.column()
        col.scale_y = 1.5
        
        if not props.ifc2ids_output_path:
            col.label(text="Output path will be auto-generated", icon='INFO')
        
        # Main action button
        row = col.row()
        row.operator("bim.execute_ifc2ids_patch", text="Generate IDS", icon='EXPORT')
        
        # Additional info
        layout.separator()
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Generated IDS will include:", icon='INFO')
        col.label(text="• Element type specifications")
        col.label(text="• Property requirements")
        col.label(text="• Material assignments")
        col.label(text="• Classification references")
        if props.ifc2ids_include_geometry:
            col.label(text="• Geometric requirements")


class BIM_PT_ifc2ids_results(Panel):
    """Panel to show results and actions after IDS generation"""
    bl_label = "IDS Results"
    bl_idname = "BIM_PT_ifc2ids_results"
    bl_parent_id = "BIM_PT_ifc2ids_patch"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        """Show only when output path exists."""
        props = context.scene.BIMIfcPatchProperties
        return (props.ifc2ids_output_path and 
                Path(props.ifc2ids_output_path).exists())

    def draw(self, context):
        """Draw the results panel."""
        layout = self.layout
        props = context.scene.BIMIfcPatchProperties
        
        if not props.ifc2ids_output_path:
            return
        
        output_path = Path(props.ifc2ids_output_path)
        
        if output_path.exists():
            # Success info
            box = layout.box()
            box.label(text="✓ IDS Generated Successfully", icon='CHECKMARK')
            
            col = box.column(align=True)
            col.label(text=f"File: {output_path.name}")
            col.label(text=f"Size: {self._format_file_size(output_path.stat().st_size)}")
            
            # Actions
            layout.separator()
            col = layout.column(align=True)
            
            row = col.row()
            row.operator("bim.open_ifc2ids_output", text="Open IDS File", icon='FILE_TEXT')
            row.operator("bim.open_ifc2ids_directory", text="Open Directory", icon='FILE_FOLDER')
            
            # Show summary if available
            summary_path = output_path.with_suffix('.json')
            if summary_path.exists():
                col.separator()
                col.operator("bim.show_ifc2ids_summary", text="Show Analysis Summary", icon='TEXT')
        else:
            layout.label(text="Output file not found", icon='ERROR')
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"


class BIM_OT_open_ifc2ids_output(Operator):
    """Open the generated IDS file"""
    bl_idname = "bim.open_ifc2ids_output"
    bl_label = "Open IDS File"
    bl_description = "Open the generated IDS file in the default application"

    def execute(self, context):
        """Open the IDS file."""
        props = context.scene.BIMIfcPatchProperties
        output_path = props.ifc2ids_output_path
        
        if not output_path or not Path(output_path).exists():
            self.report({'ERROR'}, "IDS file not found")
            return {'CANCELLED'}
        
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(["start", output_path], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", output_path])
            elif system == "Linux":
                subprocess.run(["xdg-open", output_path])
            
            self.report({'INFO'}, f"Opened IDS file: {Path(output_path).name}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Could not open file: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BIM_OT_open_ifc2ids_directory(Operator):
    """Open the directory containing the IDS file"""
    bl_idname = "bim.open_ifc2ids_directory"
    bl_label = "Open Directory"
    bl_description = "Open the directory containing the generated IDS file"

    def execute(self, context):
        """Open the directory."""
        props = context.scene.BIMIfcPatchProperties
        output_path = props.ifc2ids_output_path
        
        if not output_path:
            self.report({'ERROR'}, "No output path specified")
            return {'CANCELLED'}
        
        try:
            import subprocess
            import platform
            
            output_dir = str(Path(output_path).parent)
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(["explorer", output_dir])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", output_dir])
            elif system == "Linux":
                subprocess.run(["xdg-open", output_dir])
            
            self.report({'INFO'}, f"Opened directory: {output_dir}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Could not open directory: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BIM_OT_show_ifc2ids_summary(Operator):
    """Show the analysis summary"""
    bl_idname = "bim.show_ifc2ids_summary"
    bl_label = "Show Analysis Summary"
    bl_description = "Show the analysis summary from the IDS generation"

    def execute(self, context):
        """Show summary in a popup."""
        props = context.scene.BIMIfcPatchProperties
        output_path = props.ifc2ids_output_path
        
        if not output_path:
            self.report({'ERROR'}, "No output path specified")
            return {'CANCELLED'}
        
        summary_path = Path(output_path).with_suffix('.json')
        
        if not summary_path.exists():
            self.report({'ERROR'}, "Summary file not found")
            return {'CANCELLED'}
        
        try:
            import json
            
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            # Store summary in scene for popup display
            context.scene.ifc2ids_summary = json.dumps(summary, indent=2)
            
            # Show popup
            bpy.ops.bim.show_ifc2ids_summary_popup('INVOKE_DEFAULT')
            
        except Exception as e:
            self.report({'ERROR'}, f"Could not read summary: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BIM_OT_show_ifc2ids_summary_popup(Operator):
    """Popup to display IDS generation summary"""
    bl_idname = "bim.show_ifc2ids_summary_popup"
    bl_label = "IDS Generation Summary"
    bl_description = "Display the summary of IDS generation process"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        """Invoke the popup."""
        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        """Draw the popup content."""
        layout = self.layout
        
        if not hasattr(context.scene, 'ifc2ids_summary'):
            layout.label(text="No summary available")
            return
        
        try:
            import json
            summary = json.loads(context.scene.ifc2ids_summary)
            
            # Header
            layout.label(text="IDS Generation Summary", icon='FILE_TEXT')
            layout.separator()
            
            # Basic info
            col = layout.column(align=True)
            col.label(text=f"Source: {Path(summary.get('source_ifc', '')).name}")
            col.label(text=f"Specification: {summary.get('specification_name', 'N/A')}")
            
            layout.separator()
            
            # Analysis summary
            analysis = summary.get('analysis_summary', {})
            box = layout.box()
            box.label(text="Analysis Results:", icon='ANALYZE')
            
            col = box.column(align=True)
            col.label(text=f"Element Types: {analysis.get('total_element_types', 0)}")
            col.label(text=f"Total Elements: {analysis.get('total_elements', 0)}")
            col.label(text=f"Property Sets: {analysis.get('property_sets_found', 0)}")
            col.label(text=f"Materials: {analysis.get('materials_found', 0)}")
            col.label(text=f"Classifications: {analysis.get('classifications_found', 0)}")
            col.label(text=f"IDS Specifications Created: {analysis.get('specifications_created', 0)}")
            
            # Element breakdown
            if 'element_breakdown' in summary:
                layout.separator()
                box = layout.box()
                box.label(text="Element Breakdown:", icon='OUTLINER')
                
                breakdown = summary['element_breakdown']
                sorted_elements = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
                
                col = box.column(align=True)
                for element_type, count in sorted_elements[:10]:  # Show top 10
                    col.label(text=f"{element_type}: {count}")
                
                if len(sorted_elements) > 10:
                    col.label(text=f"... and {len(sorted_elements) - 10} more types")
            
            # Top property sets
            if 'top_property_sets' in summary:
                layout.separator()
                box = layout.box()
                box.label(text="Common Property Sets:", icon='PROPERTIES')
                
                col = box.column(align=True)
                for pset in summary['top_property_sets'][:5]:  # Show top 5
                    col.label(text=f"{pset['name']}: {pset['usage_count']} uses")
        
        except Exception as e:
            layout.label(text=f"Error displaying summary: {str(e)}")


# Property definitions for the IFC2IDS converter
def add_ifc2ids_properties():
    """Add IFC2IDS properties to the BIMIfcPatchProperties."""
    from bpy.props import StringProperty, BoolProperty
    
    # Get the existing property group
    bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_specification_name = StringProperty(
        name="Specification Name",
        description="Name for the generated IDS specification",
        default="Generated from Bonsai"
    )
    
    bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_output_path = StringProperty(
        name="Output Path",
        description="Path where the IDS file will be saved",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_include_geometry = BoolProperty(
        name="Include Geometry",
        description="Include geometric requirements in the IDS specification",
        default=False
    )
    
    bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_open_output = BoolProperty(
        name="Open Output Directory",
        description="Open the output directory after generation",
        default=True
    )


# Registration functions
classes = [
    BIM_OT_execute_ifc2ids_patch,
    BIM_OT_select_ifc2ids_output_path,
    BIM_OT_open_ifc2ids_output,
    BIM_OT_open_ifc2ids_directory,
    BIM_OT_show_ifc2ids_summary,
    BIM_OT_show_ifc2ids_summary_popup,
    BIM_PT_ifc2ids_patch,
    BIM_PT_ifc2ids_results,
]


def register():
    """Register all classes and properties."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add properties
    add_ifc2ids_properties()


def unregister():
    """Unregister all classes and properties."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Remove properties
    if hasattr(bpy.types.Scene.BIMIfcPatchProperties, 'ifc2ids_specification_name'):
        del bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_specification_name
    if hasattr(bpy.types.Scene.BIMIfcPatchProperties, 'ifc2ids_output_path'):
        del bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_output_path
    if hasattr(bpy.types.Scene.BIMIfcPatchProperties, 'ifc2ids_include_geometry'):
        del bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_include_geometry
    if hasattr(bpy.types.Scene.BIMIfcPatchProperties, 'ifc2ids_open_output'):
        del bpy.types.Scene.BIMIfcPatchProperties.ifc2ids_open_output


if __name__ == "__main__":
    register()
