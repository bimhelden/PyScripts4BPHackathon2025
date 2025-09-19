#!/usr/bin/env python3
"""
IFCfromIDS Panel für Bonsai Collaboration
=========================================

Generiert IFC-Strukturen, Templates und Validierungsregeln 
basierend auf IDS (Information Delivery Specification) Dateien.
"""

import bpy
import ifcopenshell
import ifcopenshell.api
import os
import json
from pathlib import Path
from bpy.types import Operator, Panel
from bpy.props import StringProperty, BoolProperty, EnumProperty
import bonsai.bim.ifc

try:
    from ifctester import ids
    IDS_AVAILABLE = True
except ImportError:
    IDS_AVAILABLE = False


class BIM_OT_load_ids_file(Operator):
    """Load IDS file and analyze specifications"""
    bl_idname = "bim.load_ids_file"
    bl_label = "Load IDS File"
    bl_description = "Load and analyze an IDS specification file"
    
    filename_ext = ".ids"
    filter_glob: StringProperty(default="*.ids", options={'HIDDEN'})
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        """Load and analyze the IDS file."""
        scene = context.scene
        
        if not IDS_AVAILABLE:
            self.report({'ERROR'}, "ifctester not installed. Run: pip install ifctester")
            return {'CANCELLED'}
        
        try:
            # Load IDS file
            ids_spec = ids.open(self.filepath)
            
            # Store path
            scene.ifcfromids_ids_path = self.filepath
            
            # Analyze specifications
            spec_count = len(ids_spec.specifications)
            scene.ifcfromids_spec_count = spec_count
            
            # Create summary
            summary = {
                'file': Path(self.filepath).name,
                'specifications': spec_count,
                'title': getattr(ids_spec, 'title', 'Unknown'),
                'author': getattr(ids_spec, 'author', 'Unknown')
            }
            
            scene.ifcfromids_summary = json.dumps(summary, indent=2)
            
            self.report({'INFO'}, f"IDS loaded: {spec_count} specifications found")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load IDS: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """Invoke file browser."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BIM_OT_generate_ifc_template(Operator):
    """Generate IFC template based on IDS specifications"""
    bl_idname = "bim.generate_ifc_template"
    bl_label = "Generate IFC Template"
    bl_description = "Create an IFC template with elements and properties defined in the IDS"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """Enable only when IDS is loaded."""
        scene = context.scene
        return (hasattr(scene, 'ifcfromids_ids_path') and 
                scene.ifcfromids_ids_path and 
                Path(scene.ifcfromids_ids_path).exists())

    def execute(self, context):
        """Generate IFC template from IDS."""
        scene = context.scene
        
        if not IDS_AVAILABLE:
            self.report({'ERROR'}, "ifctester not installed")
            return {'CANCELLED'}
        
        try:
            # Load IDS
            ids_spec = ids.open(scene.ifcfromids_ids_path)
            
            # Create new IFC file or use existing
            if scene.ifcfromids_use_current and bonsai.bim.ifc.IfcStore.get_file():
                ifc_file = bonsai.bim.ifc.IfcStore.get_file()
                self.report({'INFO'}, "Adding to current IFC model")
            else:
                # Create new IFC file
                ifc_file = ifcopenshell.file(schema="IFC4")
                
                # Create basic project structure
                project = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                              ifc_class="IfcProject", 
                                              name=f"Template from {Path(scene.ifcfromids_ids_path).stem}")
                
                site = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                           ifc_class="IfcSite", 
                                           name="Template Site")
                
                building = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                               ifc_class="IfcBuilding", 
                                               name="Template Building")
                
                storey = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                             ifc_class="IfcBuildingStorey", 
                                             name="Template Storey")
                
                # Create hierarchy
                ifcopenshell.api.run("aggregate.assign_object", ifc_file, 
                                    relating_object=project, product=site)
                ifcopenshell.api.run("aggregate.assign_object", ifc_file, 
                                    relating_object=site, product=building)
                ifcopenshell.api.run("aggregate.assign_object", ifc_file, 
                                    relating_object=building, product=storey)
            
            # Process IDS specifications
            elements_created = 0
            
            for spec in ids_spec.specifications:
                elements_created += self._process_specification(ifc_file, spec)
            
            # Save if new file
            if not (scene.ifcfromids_use_current and bonsai.bim.ifc.IfcStore.get_file()):
                output_path = scene.ifcfromids_output_path
                if not output_path:
                    output_path = str(Path(scene.ifcfromids_ids_path).with_suffix('.ifc'))
                
                ifc_file.write(output_path)
                scene.ifcfromids_output_path = output_path
                self.report({'INFO'}, f"IFC template saved: {Path(output_path).name}")
            
            self.report({'INFO'}, f"Template generated: {elements_created} elements created")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to generate template: {str(e)}")
            print(f"IFCfromIDS Error: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def _process_specification(self, ifc_file, spec):
        """Process a single IDS specification."""
        elements_created = 0
        
        try:
            # Get applicability - what elements this spec applies to
            for applicability in spec.applicability:
                if hasattr(applicability, 'name') and applicability.name:
                    element_type = applicability.name.upper()
                    
                    # Create template element
                    if element_type.startswith('IFC'):
                        element = self._create_template_element(ifc_file, element_type, spec)
                        if element:
                            elements_created += 1
            
        except Exception as e:
            print(f"Error processing specification {spec.name}: {e}")
        
        return elements_created
    
    def _create_template_element(self, ifc_file, element_type, spec):
        """Create a template element based on IDS specification."""
        try:
            # Create element
            element = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                          ifc_class=element_type, 
                                          name=f"Template {element_type}")
            
            # Assign to storey if available
            storeys = ifc_file.by_type("IfcBuildingStorey")
            if storeys:
                ifcopenshell.api.run("spatial.assign_container", ifc_file,
                                    relating_structure=storeys[0], product=element)
            
            # Process requirements - add properties, materials, etc.
            for requirement in spec.requirements:
                self._apply_requirement(ifc_file, element, requirement)
            
            return element
            
        except Exception as e:
            print(f"Error creating {element_type}: {e}")
            return None
    
    def _apply_requirement(self, ifc_file, element, requirement):
        """Apply a requirement to an element."""
        try:
            # Property requirements
            if hasattr(requirement, 'propertySet') and hasattr(requirement, 'baseName'):
                pset_name = requirement.propertySet
                prop_name = requirement.baseName
                
                if pset_name and prop_name and prop_name != "*":
                    # Add property set
                    pset = ifcopenshell.api.run("pset.add_pset", ifc_file,
                                               product=element, name=pset_name)
                    
                    # Add property with template value
                    template_value = "TEMPLATE_VALUE"
                    if hasattr(requirement, 'value') and requirement.value:
                        template_value = requirement.value
                    
                    ifcopenshell.api.run("pset.edit_pset", ifc_file,
                                        pset=pset, 
                                        properties={prop_name: template_value})
            
            # Material requirements  
            elif hasattr(requirement, 'value') and 'material' in requirement.__class__.__name__.lower():
                material_name = getattr(requirement, 'value', 'Template Material')
                if material_name and material_name != "*":
                    material = ifcopenshell.api.run("material.add_material", ifc_file, 
                                                   name=material_name)
                    ifcopenshell.api.run("material.assign_material", ifc_file,
                                        product=element, material=material)
        
        except Exception as e:
            print(f"Error applying requirement: {e}")


class BIM_OT_validate_current_ifc(Operator):
    """Validate current IFC against loaded IDS"""
    bl_idname = "bim.validate_current_ifc"
    bl_label = "Validate Current IFC"
    bl_description = "Validate the current IFC model against the loaded IDS specifications"

    @classmethod
    def poll(cls, context):
        """Enable when both IFC and IDS are loaded."""
        scene = context.scene
        return (bonsai.bim.ifc.IfcStore.get_file() is not None and
                hasattr(scene, 'ifcfromids_ids_path') and 
                scene.ifcfromids_ids_path and
                Path(scene.ifcfromids_ids_path).exists())

    def execute(self, context):
        """Validate IFC against IDS."""
        scene = context.scene
        
        if not IDS_AVAILABLE:
            self.report({'ERROR'}, "ifctester not installed")
            return {'CANCELLED'}
        
        try:
            # Get current IFC
            ifc_file = bonsai.bim.ifc.IfcStore.get_file()
            
            # Load IDS
            ids_spec = ids.open(scene.ifcfromids_ids_path)
            
            # Validate
            ids_spec.validate(ifc_file)
            
            # Create results summary
            total_specs = len(ids_spec.specifications)
            # Note: Detailed validation results would need more complex parsing
            
            self.report({'INFO'}, f"Validation completed: {total_specs} specifications checked")
            
        except Exception as e:
            self.report({'ERROR'}, f"Validation failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BIM_PT_ifcfromids_converter(Panel):
    """IFCfromIDS Panel unter Collaboration"""
    bl_label = "IFCfromIDS Converter"
    bl_idname = "BIM_PT_ifcfromids_converter"
    bl_parent_id = "BIM_PT_tab_collaboration"  # Subpanel unter Collaboration
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw the panel interface."""
        layout = self.layout
        scene = context.scene
        
        # Header
        box = layout.box()
        box.label(text="Generate IFC from IDS", icon='IMPORT')
        col = box.column(align=True)
        col.label(text="Create IFC templates and validate models")
        col.label(text="based on IDS specifications")
        
        # IDS File Loading
        layout.separator()
        col = layout.column(align=True)
        col.label(text="1. Load IDS File:", icon='FILE_TEXT')
        
        row = col.row()
        if hasattr(scene, 'ifcfromids_ids_path') and scene.ifcfromids_ids_path:
            row.label(text=Path(scene.ifcfromids_ids_path).name, icon='CHECKMARK')
        else:
            row.label(text="No IDS file loaded")
        
        col.operator("bim.load_ids_file", text="Load IDS File", icon='FILE_FOLDER')
        
        # Show IDS info if loaded
        if (hasattr(scene, 'ifcfromids_summary') and scene.ifcfromids_summary and
            hasattr(scene, 'ifcfromids_spec_count') and scene.ifcfromids_spec_count > 0):
            
            layout.separator()
            box = layout.box()
            box.label(text="IDS Information:", icon='INFO')
            col = box.column(align=True)
            col.label(text=f"Specifications: {scene.ifcfromids_spec_count}")
            
            # Show summary details
            try:
                summary = json.loads(scene.ifcfromids_summary)
                col.label(text=f"Title: {summary.get('title', 'N/A')}")
                col.label(text=f"Author: {summary.get('author', 'N/A')}")
            except:
                pass
        
        # Template Generation
        if (hasattr(scene, 'ifcfromids_ids_path') and scene.ifcfromids_ids_path and
            Path(scene.ifcfromids_ids_path).exists()):
            
            layout.separator()
            col = layout.column(align=True)
            col.label(text="2. Generate IFC Template:", icon='ADD')
            
            # Options
            col.prop(scene, "ifcfromids_use_current", text="Add to Current IFC")
            
            if not scene.ifcfromids_use_current:
                row = col.row()
                row.prop(scene, "ifcfromids_output_path", text="Output")
            
            # Generate button
            col.separator()
            col.operator("bim.generate_ifc_template", text="Generate Template", icon='EXPORT')
        
        # Validation
        if bonsai.bim.ifc.IfcStore.get_file() is not None:
            layout.separator()
            col = layout.column(align=True)
            col.label(text="3. Validate IFC:", icon='CHECKMARK')
            col.operator("bim.validate_current_ifc", text="Validate Against IDS", icon='ZOOM_ALL')
        
        # Info section
        layout.separator()
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Features:", icon='INFO')
        col.label(text="• Template generation from IDS")
        col.label(text="• Property set creation")
        col.label(text="• Material assignments")
        col.label(text="• IFC validation")
        
        if not IDS_AVAILABLE:
            layout.separator()
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.label(text="Missing Dependency:", icon='ERROR')
            col.label(text="pip install ifctester")


# Property definitions
def register_properties():
    """Register custom properties."""
    bpy.types.Scene.ifcfromids_ids_path = StringProperty(
        name="IDS File Path",
        description="Path to the loaded IDS file",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.ifcfromids_output_path = StringProperty(
        name="Output Path",
        description="Path for the generated IFC template",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.ifcfromids_use_current = BoolProperty(
        name="Use Current IFC",
        description="Add template elements to the current IFC instead of creating new file",
        default=False
    )
    
    bpy.types.Scene.ifcfromids_spec_count = bpy.props.IntProperty(
        name="Specification Count",
        description="Number of specifications in loaded IDS",
        default=0
    )
    
    bpy.types.Scene.ifcfromids_summary = StringProperty(
        name="IDS Summary",
        description="JSON summary of loaded IDS",
        default=""
    )


def unregister_properties():
    """Unregister custom properties."""
    del bpy.types.Scene.ifcfromids_ids_path
    del bpy.types.Scene.ifcfromids_output_path
    del bpy.types.Scene.ifcfromids_use_current
    del bpy.types.Scene.ifcfromids_spec_count
    del bpy.types.Scene.ifcfromids_summary


# Registration
classes = [
    BIM_OT_load_ids_file,
    BIM_OT_generate_ifc_template,
    BIM_OT_validate_current_ifc,
    BIM_PT_ifcfromids_converter,
]


def register():
    """Register all classes and properties."""
    register_properties()
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("IFCfromIDS Converter registered under Collaboration")


def unregister():
    """Unregister all classes and properties."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    unregister_properties()


if __name__ == "__main__":
    register()
