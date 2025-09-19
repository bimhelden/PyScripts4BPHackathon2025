import bpy
import requests
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, EnumProperty

# BIM Portal API Client
class BIMPortalClient:
    BASE_URL = "https://via.bund.de/bim"
    
    @classmethod
    def get_organisations(cls):
        try:
            response = requests.get(f"{cls.BASE_URL}/infrastruktur/api/v1/public/organisation")
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    @classmethod
    def search_properties(cls, search_string, org_guid=None):
        try:
            body = {"searchString": search_string, "pageNumber": 0}
            if org_guid:
                body["organisationGuids"] = [org_guid]
            
            response = requests.post(f"{cls.BASE_URL}/merkmale/api/v1/public/property", json=body)
            return response.json() if response.status_code == 200 else []
        except:
            return []

# Property Group für BIM Portal Einstellungen
class BIMPortalProperties(PropertyGroup):
    search_string: StringProperty(
        name="Suche",
        description="Suchbegriff für BIM Portal Merkmale",
        default=""
    )
    
    def get_org_items(self, context):
        items = [("NONE", "Alle Organisationen", "")]
        orgs = BIMPortalClient.get_organisations()
        for org in orgs:
            name = org.get('name', 'Unbekannt')
            guid = org.get('guid', '')
            items.append((guid, name, name))
        return items
    
    selected_organisation: EnumProperty(
        name="Organisation",
        description="Wähle BIM Portal Organisation",
        items=get_org_items
    )

# Operator für BIM Portal Suche
class BIM_PORTAL_OT_search(Operator):
    bl_idname = "bim_portal.search_properties"
    bl_label = "Suche Merkmale"
    bl_description = "Suche nach Merkmalen im BIM Portal Deutschland"
    
    def execute(self, context):
        props = context.scene.bim_portal_props
        search_term = props.search_string
        org_guid = props.selected_organisation if props.selected_organisation != "NONE" else None
        
        if not search_term:
            self.report({'WARNING'}, "Bitte Suchbegriff eingeben")
            return {'CANCELLED'}
        
        # API-Call ausführen
        properties = BIMPortalClient.search_properties(search_term, org_guid)
        
        if properties:
            # Ergebnisse in Konsole ausgeben (später: in UI-Liste)
            print(f"=== BIM Portal Suchergebnisse für '{search_term}' ===")
            for i, prop in enumerate(properties[:10], 1):
                name = prop.get('name', 'Unbekannt')
                org = prop.get('organisationName', 'Unbekannt')
                print(f"{i}. {name} ({org})")
            
            self.report({'INFO'}, f"{len(properties)} Merkmale gefunden")
        else:
            self.report({'WARNING'}, "Keine Merkmale gefunden")
        
        return {'FINISHED'}

# Operator um Merkmal auf ausgewählte IFC-Elemente anzuwenden
class BIM_PORTAL_OT_apply_property(Operator):
    bl_idname = "bim_portal.apply_property"
    bl_label = "Eigenschaft anwenden"
    bl_description = "Wendet BIM Portal Merkmal auf ausgewählte IFC-Elemente an"
    
    property_name: StringProperty()
    property_value: StringProperty()
    
    def execute(self, context):
        # Hier würde die IFC-Integration erfolgen
        selected_objects = [obj for obj in context.selected_objects if hasattr(obj, 'BIMObjectProperties')]
        
        if not selected_objects:
            self.report({'WARNING'}, "Keine IFC-Objekte ausgewählt")
            return {'CANCELLED'}
        
        # Placeholder für IFC-Property Anwendung
        for obj in selected_objects:
            print(f"Wende '{self.property_name}' auf {obj.name} an")
            # Hier würde ifcopenshell.api.run() verwendet werden
        
        self.report({'INFO'}, f"Eigenschaft '{self.property_name}' auf {len(selected_objects)} Objekte angewendet")
        return {'FINISHED'}

# Subpanel in Quality and Coordination > Collaboration
class BIM_PT_portal_deutschland(Panel):
    bl_label = "BIM Portal Deutschland"
    bl_idname = "BIM_PT_portal_deutschland"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "BIM_PT_tab_collaboration"  # Parent Panel in BonsaiBIM
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # Nur anzeigen wenn BonsaiBIM aktiv ist
        return hasattr(context.scene, 'BIMProperties')
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.bim_portal_props
        
        # Organisation auswählen
        layout.prop(props, "selected_organisation")
        
        # Suchfeld
        row = layout.row()
        row.prop(props, "search_string")
        row.operator("bim_portal.search_properties", text="", icon='VIEWZOOM')
        
        # Info-Box
        box = layout.box()
        box.label(text="Deutsche BIM-Standards")
        box.label(text="Suche: Tür, Wand, Feuerwiderstand, ...")
        
        # Placeholder für Ergebnisliste (später dynamic)
        if props.search_string:
            layout.separator()
            layout.label(text="Ergebnisse:")
            # Hier würde eine dynamische Liste der Suchergebnisse kommen

# Registrierung
classes = [
    BIMPortalProperties,
    BIM_PORTAL_OT_search,
    BIM_PORTAL_OT_apply_property,
    BIM_PT_portal_deutschland,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.bim_portal_props = bpy.props.PointerProperty(type=BIMPortalProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.bim_portal_props

# Für Python Console Test
if __name__ == "__main__":
    register()
    print("BIM Portal Deutschland Subpanel registriert")
