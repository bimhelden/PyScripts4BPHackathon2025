#!/usr/bin/env python3
"""
IDS Match - Improved Tree Display
=================================

Verbesserungen:
1. Tree eingeklappt anzeigen
2. Alle IFC-Klassen/Nodes zeigen  
3. Blaue Markierung mit weißer Schrift statt rot
"""

import bpy
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty

# IDS Parser Integration
def get_namespaces(root):
    """Extract default namespace dynamically from root element."""
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0].strip("{")
        return {"ids": uri}
    else:
        return {"ids": ""}  # no namespace

def parse_ids(xml_file):
    """Parse IDS file to JSON structure."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    NS = get_namespaces(root)

    result = {}

    specifications = root.find("ids:specifications", NS)
    if specifications is None:
        return result

    for spec in specifications.findall("ids:specification", NS):
        spec_name = spec.get("name", "")
        applicability = spec.find("ids:applicability", NS)
        requirements = spec.find("ids:requirements", NS)

        if applicability is None or requirements is None:
            continue

        for entity in applicability.findall("ids:entity", NS):
            name = entity.findtext("ids:name/ids:simpleValue", default="", namespaces=NS)
            predefined = entity.findtext("ids:predefinedType/ids:simpleValue", default="", namespaces=NS)

            # Build entity key: Entity.PredefinedType (or just Entity if no predefinedType)
            if predefined:
                entity_key = f"{name}.{predefined}"
            else:
                entity_key = name

            # Duplicate check
            if entity_key in result:
                print(f"WARNING: Duplicate entity key '{entity_key}' found")

            # Ensure structure exists
            if entity_key not in result:
                result[entity_key] = {
                    "name": spec_name,  # store specification name
                    "properties": {}
                }

            # Add properties
            for prop in requirements.findall("ids:property", NS):
                prop_set = prop.findtext("ids:propertySet/ids:simpleValue", default="", namespaces=NS)
                base_name = prop.findtext("ids:baseName/ids:simpleValue", default="", namespaces=NS)

                if prop_set:
                    if prop_set not in result[entity_key]["properties"]:
                        result[entity_key]["properties"][prop_set] = {}

                    if base_name:
                        # Create empty node for baseName
                        if base_name not in result[entity_key]["properties"][prop_set]:
                            result[entity_key]["properties"][prop_set][base_name] = {}

    return result

class SimpleTreeNode(PropertyGroup):
    name: StringProperty(name="Name", default="")
    node_type: StringProperty(name="Type", default="")
    level: IntProperty(name="Tree Level", default=0)
    expanded: BoolProperty(name="Expanded", default=False)  # Standardmäßig eingeklappt
    has_children: BoolProperty(name="Has Children", default=False)

class SIMPLE_OT_load_file1(Operator):
    bl_idname = "simple.load_file1"
    bl_label = "📁 Load IDS File 1"
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ids;*.xml;*.json", options={'HIDDEN'})
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        scene = context.scene
        scene.simple_file1_loaded = True
        scene.simple_file1_name = Path(self.filepath).name
        scene.simple_file1_path = self.filepath
        self.report({'INFO'}, f"✅ Loaded: {scene.simple_file1_name}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class SIMPLE_OT_load_file2(Operator):
    bl_idname = "simple.load_file2"
    bl_label = "📁 Load IDS File 2"
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ids;*.xml;*.json", options={'HIDDEN'})
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        scene = context.scene
        scene.simple_file2_loaded = True
        scene.simple_file2_name = Path(self.filepath).name
        scene.simple_file2_path = self.filepath
        self.report({'INFO'}, f"✅ Loaded: {scene.simple_file2_name}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class SIMPLE_OT_toggle_node(Operator):
    bl_idname = "simple.toggle_node"
    bl_label = "Toggle Node"
    bl_description = "Expand/collapse node or select it"
    
    node_index: IntProperty(default=0)
    
    def execute(self, context):
        scene = context.scene
        
        if 0 <= self.node_index < len(scene.simple_tree_nodes):
            node = scene.simple_tree_nodes[self.node_index]
            
            # Toggle expand/collapse nur für Nodes mit Children
            if node.has_children:
                node.expanded = not node.expanded
                print(f"Toggled {node.name}: {'expanded' if node.expanded else 'collapsed'}")
            
            # Immer Selection setzen
            scene.simple_selected_index = self.node_index
        
        return {'FINISHED'}

class SIMPLE_OT_analyze_ids(Operator):
    bl_idname = "simple.analyze_ids"
    bl_label = "🔍 Analyze IDS"
    
    def execute(self, context):
        scene = context.scene
        
        if not scene.simple_file1_loaded:
            self.report({'ERROR'}, "Please load an IDS file first")
            return {'CANCELLED'}
        
        try:
            # Parse IDS file using your parser
            file_path = scene.simple_file1_path
            
            if file_path.endswith('.json'):
                # Direct JSON loading
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            elif file_path.endswith(('.ids', '.xml')):
                # Parse IDS/XML using your parser
                print(f"Parsing IDS file: {file_path}")
                json_data = parse_ids(file_path)
                print(f"Parsed {len(json_data)} entities from IDS file")
            else:
                self.report({'ERROR'}, "Unsupported file format. Use .ids, .xml, or .json files")
                return {'CANCELLED'}
            
            # Clear existing tree
            scene.simple_tree_nodes.clear()
            
            if not json_data:
                self.report({'WARNING'}, "No entities found in IDS file")
                return {'CANCELLED'}
            
            # Build complete tree structure from parsed IDS data
            entity_count = 0
            for entity_key, entity_data in json_data.items():
                # Add main entity node (IFC Class)
                entity_node = scene.simple_tree_nodes.add()
                entity_node.name = entity_key
                entity_node.node_type = "Entity"
                entity_node.level = 0
                entity_node.expanded = False  # Standardmäßig eingeklappt
                entity_count += 1
                
                # Check if entity has properties - FIX: Explizite Boolean-Zuweisung
                if (isinstance(entity_data, dict) and 
                    "properties" in entity_data and 
                    entity_data["properties"]):
                    entity_node.has_children = True
                    has_properties = True
                else:
                    entity_node.has_children = False
                    has_properties = False
                
                # Add properties (für Tree-Structure)
                if has_properties:
                    for pset_name, pset_data in entity_data["properties"].items():
                        # PropertySet node
                        pset_node = scene.simple_tree_nodes.add()
                        pset_node.name = pset_name
                        pset_node.node_type = "PropertySet"
                        pset_node.level = 1
                        pset_node.expanded = False
                        
                        # FIX: Explizite Boolean-Zuweisung für has_children
                        if isinstance(pset_data, dict) and pset_data:
                            pset_node.has_children = True
                        else:
                            pset_node.has_children = False
                        
                        # Individual properties
                        if isinstance(pset_data, dict):
                            for prop_name in pset_data.keys():
                                prop_node = scene.simple_tree_nodes.add()
                                prop_node.name = prop_name
                                prop_node.node_type = "Property"
                                prop_node.level = 2
                                prop_node.expanded = False
                                prop_node.has_children = False  # Properties haben keine Children
            
            # Show tree
            scene.simple_show_tree = True
            scene.simple_selected_index = -1  # Keine Selection initially
            
            self.report({'INFO'}, f"🌳 Parsed IDS: {entity_count} IFC entities, {len(scene.simple_tree_nodes)} total nodes")
            return {'FINISHED'}
            
        except ET.ParseError as e:
            self.report({'ERROR'}, f"XML Parse Error: {str(e)}")
            return {'CANCELLED'}
        except FileNotFoundError:
            self.report({'ERROR'}, "IDS file not found")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error parsing IDS file: {str(e)}")
            return {'CANCELLED'}

class SIMPLE_PT_ids_panel(Panel):
    bl_label = "IDS Match"
    bl_idname = "SIMPLE_PT_ids_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "BIM_PT_tab_collaboration"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # File Loading Section
        box = layout.box()
        box.label(text="📂 Load IDS Files", icon='FILE_FOLDER')
        
        row = box.row()
        col = row.column()
        col.operator("simple.load_file1", text="Load IDS File 1", icon='IMPORT')
        if getattr(scene, 'simple_file1_loaded', False):
            col.label(text=f"✅ {getattr(scene, 'simple_file1_name', '')}", icon='CHECKMARK')
        
        col = row.column()
        col.operator("simple.load_file2", text="Load IDS File 2", icon='IMPORT')
        if getattr(scene, 'simple_file2_loaded', False):
            col.label(text=f"✅ {getattr(scene, 'simple_file2_name', '')}", icon='CHECKMARK')
        
        # Analysis Section
        if getattr(scene, 'simple_file1_loaded', False):
            box = layout.box()
            box.label(text="🔍 Analysis", icon='ZOOM_ALL')
            row = box.row()
            row.operator("simple.analyze_ids", text="Analyze IDS", icon='OUTLINER_OB_MESH')
        
        # Tree Display Section
        if getattr(scene, 'simple_show_tree', False):
            box = layout.box()
            filename = getattr(scene, 'simple_file1_name', 'File 1')
            box.label(text=f"🌳 Tree: {filename}", icon='OUTLINER_OB_MESH')
            
            if hasattr(scene, 'simple_tree_nodes') and len(scene.simple_tree_nodes) > 0:
                self._draw_tree_nodes(box, scene)
            else:
                box.label(text="No tree data available", icon='INFO')
    
    def _draw_tree_nodes(self, layout, scene):
        """Zeichnet die Tree-Nodes mit verbesserter Logik."""
        selected_idx = getattr(scene, 'simple_selected_index', -1)
        
        # Zeige alle Entities (Level 0) immer
        for i, node in enumerate(scene.simple_tree_nodes):
            if node.level == 0:  # Entity level - immer zeigen
                self._draw_single_node(layout, scene, node, i, selected_idx)
                
                # Zeige PropertySets nur wenn Entity expanded ist
                if node.expanded and node.has_children:
                    self._draw_children(layout, scene, i, selected_idx)
    
    def _draw_single_node(self, layout, scene, node, index, selected_idx):
        """Zeichnet einen einzelnen Node."""
        row = layout.row()
        
        # Indentation
        for _ in range(node.level):
            row.label(text="", icon='BLANK1')
        
        # NEUE: Blaue Markierung mit weißer Schrift statt rot
        if index == selected_idx:
            # Blue background instead of red alert
            sub = row.row()
            sub.alert = False  # Kein rotes Alert mehr
            sub.operator("simple.toggle_node", text=node.name, depress=True)  # Blauer "pressed" Style
            sub.operator("simple.toggle_node", text="").node_index = index
            sub.prop(scene, "simple_selected_index", text="", icon='RADIOBUT_ON')  # Blue radio button
        else:
            # Expand/Collapse icon für Nodes mit Children
            if node.has_children:
                icon = 'TRIA_DOWN' if node.expanded else 'TRIA_RIGHT'
                row.operator("simple.toggle_node", text="", icon=icon).node_index = index
            else:
                row.label(text="", icon='DOT')
            
            # Node icon
            if node.node_type == "Entity":
                icon = 'MESH_CUBE'
            elif node.node_type == "PropertySet":
                icon = 'PROPERTIES'
            else:
                icon = 'DOT'
            
            # Node button
            op = row.operator("simple.toggle_node", text=node.name, icon=icon)
            op.node_index = index
    
    def _draw_children(self, layout, scene, parent_index, selected_idx):
        """Zeichnet Children-Nodes eines expanded Parents."""
        parent_node = scene.simple_tree_nodes[parent_index]
        
        # Finde alle direkten Children
        for i in range(parent_index + 1, len(scene.simple_tree_nodes)):
            child_node = scene.simple_tree_nodes[i]
            
            # Stop wenn wir zu einem anderen Parent kommen
            if child_node.level <= parent_node.level:
                break
            
            # Zeige nur direkte Children (level = parent_level + 1)
            if child_node.level == parent_node.level + 1:
                self._draw_single_node(layout, scene, child_node, i, selected_idx)
                
                # Rekursiv für expanded PropertySets
                if child_node.expanded and child_node.has_children:
                    self._draw_children(layout, scene, i, selected_idx)

def register():
    bpy.utils.register_class(SimpleTreeNode)
    bpy.utils.register_class(SIMPLE_OT_load_file1)
    bpy.utils.register_class(SIMPLE_OT_load_file2)
    bpy.utils.register_class(SIMPLE_OT_toggle_node)
    bpy.utils.register_class(SIMPLE_OT_analyze_ids)
    bpy.utils.register_class(SIMPLE_PT_ids_panel)
    
    bpy.types.Scene.simple_file1_loaded = BoolProperty(default=False)
    bpy.types.Scene.simple_file1_name = StringProperty(default="")
    bpy.types.Scene.simple_file1_path = StringProperty(default="")
    bpy.types.Scene.simple_file2_loaded = BoolProperty(default=False)
    bpy.types.Scene.simple_file2_name = StringProperty(default="")
    bpy.types.Scene.simple_file2_path = StringProperty(default="")
    bpy.types.Scene.simple_tree_nodes = CollectionProperty(type=SimpleTreeNode)
    bpy.types.Scene.simple_selected_index = IntProperty(default=-1)
    bpy.types.Scene.simple_show_tree = BoolProperty(default=False)
    
    print("✅ IDS Match Panel registered - Improved Tree!")

def unregister():
    props = ['simple_file1_loaded', 'simple_file1_name', 'simple_file1_path',
             'simple_file2_loaded', 'simple_file2_name', 'simple_file2_path',
             'simple_tree_nodes', 'simple_selected_index', 'simple_show_tree']
    for prop in props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
    
    classes = [SIMPLE_PT_ids_panel, SIMPLE_OT_analyze_ids, SIMPLE_OT_toggle_node,
               SIMPLE_OT_load_file2, SIMPLE_OT_load_file1, SimpleTreeNode]
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass

def clean():
    unregister()
    print("🧹 Cleaned!")

if __name__ == "__main__":
    clean()
    register()