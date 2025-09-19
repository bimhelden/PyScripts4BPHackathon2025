import bpy
import ifcopenshell
import os
from datetime import datetime

class BIM_OT_ifc2ids_converter(bpy.types.Operator):
    """
    IFC2IDS Converter - Generiert IDS aus IFC-Modell
    """
    bl_idname = "bim.ifc2ids_converter"
    bl_label = "IFC zu IDS konvertieren"
    bl_description = "Generiert Information Delivery Specification aus IFC-Modell"
    
    def execute(self, context):
        # Prüfen ob IFC-Datei geladen ist
        if not hasattr(context.scene, 'BIMProperties') or not context.scene.BIMProperties.ifc_file:
            self.report({'ERROR'}, "Keine IFC-Datei geladen")
            return {'CANCELLED'}
        
        ifc_file = context.scene.BIMProperties.ifc_file
        
        # Output-Pfad aus Properties holen
        output_path = context.scene.ifc2ids_output_path
        
        try:
            # IFC-Elemente analysieren
            elements = ifc_file.by_type("IfcProduct")
            self.report({'INFO'}, f"Analysiere {len(elements)} IFC-Elemente...")
            
            # IDS-XML generieren
            ids_content = self.generate_ids_xml(elements)
            
            # Datei schreiben
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ids_content)
            
            self.report({'INFO'}, f"IDS erfolgreich erstellt: {output_path}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Fehler: {str(e)}")
            return {'CANCELLED'}
    
    def generate_ids_xml(self, elements):
        """Generiert IDS-XML aus IFC-Elementen"""
        
        # IDS-Header
        ids_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
    <info>
        <title>IFC Model Requirements</title>
        <description>Generated from IFC model using BonsaiBIM</description>
        <author>BonsaiBIM IFC2IDS Tool</author>
        <date>{datetime.now().strftime('%Y-%m-%d')}</date>
    </info>
    <specifications>
'''
        
        # Element-Typen sammeln
        element_types = {}
        for element in elements:
            element_type = element.is_a()
            if element_type not in element_types:
                element_types[element_type] = []
            element_types[element_type].append(element)
        
        # Für jeden Element-Typ eine Specification erstellen
        for element_type, type_elements in element_types.items():
            ids_xml += f'''
        <specification name="{element_type}_Requirements">
            <applicability>
                <entity>
                    <name>
                        <simpleValue>{element_type}</simpleValue>
                    </name>
                </entity>
            </applicability>
            <requirements>
                <attribute instructions="Name is required">
                    <name>Name</name>
                </attribute>
            </requirements>
        </specification>'''
        
        ids_xml += '''
    </specifications>
</ids>'''
        
        return ids_xml

class BIM_PT_ifc2ids_tool(bpy.types.Panel):
    """
    Panel für IFC2IDS Converter
    """
    bl_label = "IFC2IDS Converter"
    bl_idname = "BIM_PT_ifc2ids_tool"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "BIM_PT_tab_collaboration"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, 'BIMProperties')
    
    def draw(self, context):
        layout = self.layout
        
        # Status-Info
        box = layout.box()
        box.label(text="IFC zu IDS Konvertierung")
        
        if context.scene.BIMProperties.ifc_file:
            ifc_file = context.scene.BIMProperties.ifc_file
            elements = ifc_file.by_type("IfcProduct")
            box.label(text=f"✓ IFC geladen: {len(elements)} Elemente")
        else:
            box.label(text="✗ Keine IFC-Datei geladen")
            return
        
        # Output-Pfad
        layout.separator()
        layout.prop(context.scene, "ifc2ids_output_path")
        
        # Convert-Button
        layout.separator()
        layout.operator("bim.ifc2ids_converter", text="IDS generieren", icon='EXPORT')

# Properties
bpy.types.Scene.ifc2ids_output_path = bpy.props.StringProperty(
    name="IDS Ausgabe",
    description="Pfad für die IDS-XML-Datei",
    default="/tmp/model_requirements.ids",
    subtype='FILE_PATH'
)

def register():
    bpy.utils.register_class(BIM_OT_ifc2ids_converter)
    bpy.utils.register_class(BIM_PT_ifc2ids_tool)

def unregister():
    bpy.utils.unregister_class(BIM_PT_ifc2ids_tool)
    bpy.utils.unregister_class(BIM_OT_ifc2ids_converter)
    del bpy.types.Scene.ifc2ids_output_path

if __name__ == "__main__":
    register()
    print("IFC2IDS Tool registriert")
