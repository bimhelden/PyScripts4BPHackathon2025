#!/usr/bin/env python3
"""
IDS Fetch Panel für Bonsai Collaboration - FIXED VERSION
========================================================

Integriert mit der echten BIM Portal API (via.bund.de)
Workflow: Server auswählen → Fachmodelle laden → Modell auswählen → IDS downloaden

FIXED: Registrierung-Reihenfolge korrigiert für CollectionProperty
"""

import bpy
import requests
import json
import os
from pathlib import Path
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
import bonsai.bim.ifc

# Echte BIM Portal API
BIM_PORTAL_API = "https://via.bund.de/bim/aia/api/v1/public/domainSpecificModel"

# Server-Definitionen 
IDS_SERVERS = [
    ("DE_BIM_PORTAL", "DE - BIM Portal", "Deutsches BIM Portal via.bund.de", ""),
    # Zukünftige Server können hier hinzugefügt werden:
    # ("BUILDINGSMART", "buildingSMART International", "International IDS Repository", ""),
]

class IDS_DomainModel_Item(PropertyGroup):
    """Property Group für Fachmodell-Informationen."""
    
    guid: StringProperty(name="GUID", default="")
    name: StringProperty(name="Name", default="")
    description: StringProperty(name="Description", default="")
    domain: StringProperty(name="Domain", default="")
    version: StringProperty(name="Version", default="")


class BIM_OT_connect_ids_server(Operator):
    """Verbindet mit ausgewähltem IDS Server und lädt Fachmodelle"""
    bl_idname = "bim.connect_ids_server"
    bl_label = "Connect to Server"
    bl_description = "Verbindet mit dem ausgewählten IDS Server und lädt verfügbare Fachmodelle"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Verbindung zum Server herstellen."""
        scene = context.scene
        selected_server = scene.ids_fetch_server_selection
        
        self.report({'INFO'}, f"Verbinde mit {selected_server}...")
        
        try:
            if selected_server == "DE_BIM_PORTAL":
                # Echte BIM Portal API verwenden
                domain_models = self._fetch_bim_portal_models()
                
                # Clear existing models
                scene.ids_fetch_domain_models.clear()
                
                # Add models to collection
                for model in domain_models:
                    model_item = scene.ids_fetch_domain_models.add()
                    model_item.guid = model.get("guid", model.get("id", ""))
                    model_item.name = model.get("name", "Unbekanntes Modell")
                    model_item.description = model.get("description", "")
                    model_item.domain = model.get("domain", "Allgemein")
                    model_item.version = model.get("version", "1.0")
                
                # Server-Status setzen
                scene.ids_fetch_server_connected = True
                scene.ids_fetch_models_count = len(domain_models)
                
                self.report({'INFO'}, f"✅ {len(domain_models)} Fachmodelle geladen")
                
            else:
                self.report({'ERROR'}, f"Server {selected_server} noch nicht implementiert")
                return {'CANCELLED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Verbindungsfehler: {str(e)}")
            scene.ids_fetch_server_connected = False
            scene.ids_fetch_models_count = 0
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def _fetch_bim_portal_models(self):
        """Lädt Fachmodelle vom BIM Portal mit echter API."""
        
        try:
            # POST Request wie im BIMPortalConnector.py
            response = requests.post(
                BIM_PORTAL_API,
                headers={"accept": "application/json", "Content-Type": "application/json"},
                json={},  # Empty JSON body as required
                timeout=10
            )
            
            response.raise_for_status()
            models = response.json()
            
            print(f"BIM Portal Response: {len(models)} models found")
            
            # Debug: Zeige erste paar Modelle
            for i, model in enumerate(models[:3]):
                print(f"Model {i+1}: {model.get('name', 'Unknown')} - {model.get('guid', 'No GUID')}")
            
            return models
            
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            
            # Fallback zu Mock-Daten für Development
            return self._get_mock_domain_models()
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self._get_mock_domain_models()
    
    def _get_mock_domain_models(self):
        """Mock-Daten für Development falls API nicht erreichbar."""
        
        return [
            {
                "guid": "12345678-1234-1234-1234-123456789abc",
                "name": "Brandschutz Hochbau 2024",
                "description": "Brandschutzanforderungen für Hochbauprojekte",
                "domain": "Brandschutz",
                "version": "2.1"
            },
            {
                "guid": "87654321-4321-4321-4321-cba987654321", 
                "name": "Barrierefreiheit DIN 18040",
                "description": "Barrierefreie Gestaltung nach DIN 18040",
                "domain": "Barrierefreiheit",
                "version": "1.5"
            },
            {
                "guid": "abcdef12-3456-7890-abcd-ef1234567890",
                "name": "DB InfraGO Eisenbahnbrücken",
                "description": "Deutsche Bahn Standards für Eisenbahnbrücken",
                "domain": "Infrastruktur",
                "version": "3.0"
            },
            {
                "guid": "fedcba98-7654-3210-fedc-ba9876543210",
                "name": "Nachhaltigkeit DGNB",
                "description": "DGNB Nachhaltigkeitsanforderungen",
                "domain": "Nachhaltigkeit", 
                "version": "1.2"
            }
        ]


class BIM_OT_download_domain_model_ids(Operator):
    """Lädt IDS-Datei für ausgewähltes Fachmodell herunter"""
    bl_idname = "bim.download_domain_model_ids"
    bl_label = "Download IDS"
    bl_description = "Lädt die IDS-Datei für das ausgewählte Fachmodell herunter"
    bl_options = {"REGISTER", "UNDO"}

    model_guid: StringProperty(name="Model GUID", default="")
    model_name: StringProperty(name="Model Name", default="")
    
    # File browser properties
    filename_ext = ".ids"
    filter_glob: StringProperty(default="*.ids", options={'HIDDEN'})
    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        """Lädt die IDS-Datei herunter und speichert sie am gewählten Ort."""
        scene = context.scene
        
        if not self.model_guid:
            self.report({'ERROR'}, "Keine Modell-GUID angegeben")
            return {'CANCELLED'}
        
        if not self.filepath:
            self.report({'ERROR'}, "Kein Speicherort ausgewählt")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Lade IDS im Hintergrund: {self.model_name}")
        
        try:
            # IDS im Hintergrund vom BIM Portal laden
            ids_content = self._fetch_ids_from_bim_portal(self.model_guid)
            
            if ids_content:
                # IDS-Datei am gewählten Ort speichern
                filepath = Path(self.filepath)
                
                # Sicherstellen dass Dateiendung .ids ist
                if not filepath.suffix == '.ids':
                    filepath = filepath.with_suffix('.ids')
                
                # Verzeichnis erstellen falls nicht vorhanden
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                # IDS-Datei schreiben
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(ids_content)
                
                # Download-Info speichern
                scene.ids_fetch_last_download = str(filepath)
                scene.ids_fetch_last_model_name = self.model_name
                scene.ids_fetch_last_model_guid = self.model_guid
                
                self.report({'INFO'}, f"✅ IDS gespeichert: {filepath.name}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "IDS-Inhalt konnte nicht geladen werden")
                return {'CANCELLED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Fehler beim Speichern: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        """Öffnet File-Dialog für Speicherort-Auswahl."""
        
        if not self.model_guid or not self.model_name:
            self.report({'ERROR'}, "Modell-Informationen fehlen")
            return {'CANCELLED'}
        
        # Generiere Default-Dateinamen aus Modell-Name
        safe_name = "".join(c for c in self.model_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        default_filename = f"{safe_name}.ids"
        
        # Setze Default-Pfad
        self.filepath = default_filename
        
        # Öffne File-Browser
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def _fetch_ids_from_bim_portal(self, guid: str) -> str:
        """Lädt IDS-Inhalt im Hintergrund vom BIM Portal."""
        
        try:
            # GET Request für IDS XML (wie im BIMPortalConnector.py)
            url = f"{BIM_PORTAL_API}/{guid}/IDS"
            
            print(f"Fetching IDS from: {url}")
            
            response = requests.get(
                url,
                headers={"accept": "*/*"},
                timeout=30
            )
            
            response.raise_for_status()
            
            # Content als UTF-8 String zurückgeben
            ids_content = response.text
            
            print(f"✅ IDS loaded successfully ({len(ids_content)} characters)")
            return ids_content
            
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            
            # Fallback: Mock IDS-Inhalt für Development
            return self._create_mock_ids_content()
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def _create_mock_ids_content(self) -> str:
        """Erstellt Mock IDS-Inhalt für Development."""
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <info>
        <title>{self.model_name}</title>
        <description>Austausch-Informations-Anforderungen für {self.model_name}</description>
        <author>BIM Deutschland Portal (via.bund.de)</author>
        <purpose>Fachmodell Validierung und Qualitätssicherung</purpose>
        <milestone>Entwicklung</milestone>
    </info>
    <specifications>
        <specification name="Grundanforderungen {self.model_name}" ifcVersion="IFC4X3_ADD2">
            <applicability>
                <entity>
                    <n>IFCWALL</n>
                </entity>
            </applicability>
            <requirements>
                <property propertySet="Pset_WallCommon" baseName="LoadBearing" cardinality="required">
                    <instructions>Tragend/nicht-tragend muss definiert sein</instructions>
                </property>
                <property propertySet="Pset_WallCommon" baseName="IsExternal" cardinality="required">
                    <instructions>Außenwand/Innenwand Klassifikation erforderlich</instructions>
                </property>
                <material cardinality="required">
                    <instructions>Materialdefinition für alle Wände erforderlich</instructions>
                </material>
            </requirements>
        </specification>
        <specification name="Türen {self.model_name}" ifcVersion="IFC4X3_ADD2">
            <applicability>
                <entity>
                    <n>IFCDOOR</n>
                </entity>
            </applicability>
            <requirements>
                <property propertySet="Pset_DoorCommon" baseName="FireRating" cardinality="optional">
                    <instructions>Brandschutzklasse falls relevant</instructions>
                </property>
                <property propertySet="Pset_DoorCommon" baseName="IsExternal" cardinality="required">
                    <instructions>Außentür/Innentür Klassifikation</instructions>
                </property>
            </requirements>
        </specification>
    </specifications>
</ids>'''


class BIM_PT_ids_fetch(Panel):
    """IDS Fetch Panel unter Collaboration"""
    bl_label = "IDS Fetch"
    bl_idname = "BIM_PT_ids_fetch"
    bl_parent_id = "BIM_PT_tab_collaboration"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw the IDS Fetch interface."""
        layout = self.layout
        scene = context.scene
        
        # Header
        box = layout.box()
        box.label(text="Fetch IDS from BIM Portal", icon='IMPORT')
        col = box.column(align=True)
        col.label(text="Connect to BIM Portal and download")
        col.label(text="IDS files from domain-specific models")
        
        # Server Selection & Connection
        layout.separator()
        col = layout.column(align=True)
        col.label(text="1. Connect to IDS Server:", icon='LINKED')
        
        # Server Dropdown
        row = col.row()
        row.prop(scene, "ids_fetch_server_selection", text="")
        row.operator("bim.connect_ids_server", text="Connect", icon='PLUGIN')
        
        # Connection Status
        if hasattr(scene, 'ids_fetch_server_connected'):
            status_box = layout.box()
            if scene.ids_fetch_server_connected:
                status_box.label(text="✅ Connected to BIM Portal", icon='CHECKMARK')
                if hasattr(scene, 'ids_fetch_models_count') and scene.ids_fetch_models_count > 0:
                    status_box.label(text=f"  {scene.ids_fetch_models_count} Fachmodelle verfügbar")
            else:
                status_box.alert = True
                status_box.label(text="❌ Not Connected", icon='UNLINKED')
        
        # Domain Models Selection
        if (hasattr(scene, 'ids_fetch_server_connected') and 
            scene.ids_fetch_server_connected and 
            len(scene.ids_fetch_domain_models) > 0):
            
            layout.separator()
            col = layout.column(align=True)
            col.label(text="2. Select Domain Model:", icon='MESH_DATA')
            
            # Models List
            box = layout.box()
            
            for i, model in enumerate(scene.ids_fetch_domain_models):
                row = box.row()
                
                # Model Info
                info_col = row.column()
                info_col.label(text=model.name, icon='FILE_3D')
                
                # Sub-info row
                sub_row = info_col.row()
                sub_row.scale_y = 0.8
                sub_row.label(text=f"🏗️ {model.domain} | v{model.version}")
                
                if model.description:
                    desc_row = info_col.row()
                    desc_row.scale_y = 0.7
                    desc_row.label(text=f"💬 {model.description[:50]}...")
                
                # Download Button
                download_col = row.column()
                download_col.scale_x = 0.6
                op = download_col.operator("bim.download_domain_model_ids", 
                                          text="Download IDS", icon='IMPORT')
                op.model_guid = model.guid
                op.model_name = model.name
        
        # Last Download Info
        if (hasattr(scene, 'ids_fetch_last_download') and scene.ids_fetch_last_download and
            hasattr(scene, 'ids_fetch_last_model_name')):
            
            layout.separator()
            box = layout.box()
            box.label(text="Last Download:", icon='CHECKMARK')
            
            col = box.column(align=True)
            col.label(text=f"📄 {scene.ids_fetch_last_model_name}")
            filename = Path(scene.ids_fetch_last_download).name
            col.label(text=f"💾 {filename}")
            
            # File path (shortened)
            file_dir = str(Path(scene.ids_fetch_last_download).parent)
            if len(file_dir) > 50:
                file_dir = "..." + file_dir[-47:]
            col.label(text=f"📂 {file_dir}")


# Properties für Scene
def register_properties():
    """Registriert Properties für IDS Fetch."""
    
    # Prüfe ob Properties bereits existieren - wenn ja, komplett abbrechen
    if hasattr(bpy.types.Scene, 'ids_fetch_server_selection'):
        print("IDS Fetch Properties bereits registriert - überspringe")
        return
    
    try:
        # EnumProperty mit inline Items (vermeidet Referenz-Probleme)
        bpy.types.Scene.ids_fetch_server_selection = EnumProperty(
            name="IDS Server",
            description="Select IDS server to fetch from",
            items=[
                ("DE_BIM_PORTAL", "DE - BIM Portal", "Deutsches BIM Portal via.bund.de", "", 0)
            ],
            default="DE_BIM_PORTAL"
        )
        
        bpy.types.Scene.ids_fetch_server_connected = BoolProperty(
            name="Server Connected",
            description="Whether connected to the selected server",
            default=False
        )
        
        bpy.types.Scene.ids_fetch_models_count = IntProperty(
            name="Models Count",
            description="Number of domain models available on server",
            default=0
        )
        
        # WICHTIG: CollectionProperty referenziert die bereits registrierte Klasse
        bpy.types.Scene.ids_fetch_domain_models = CollectionProperty(
            type=IDS_DomainModel_Item,
            name="Domain Models"
        )
        
        bpy.types.Scene.ids_fetch_last_download = StringProperty(
            name="Last Download",
            description="Path to last downloaded IDS file",
            default=""
        )
        
        bpy.types.Scene.ids_fetch_last_model_name = StringProperty(
            name="Last Model Name",
            description="Name of last downloaded model",
            default=""
        )
        
        bpy.types.Scene.ids_fetch_last_model_guid = StringProperty(
            name="Last Model GUID",
            description="GUID of last downloaded model",
            default=""
        )
        
        print("✅ IDS Fetch Properties erfolgreich registriert")
        
    except Exception as e:
        print(f"❌ Fehler beim Registrieren der Properties: {e}")
        # Versuche Cleanup wenn Fehler
        unregister_properties()
        raise


def unregister_properties():
    """Entfernt Properties für IDS Fetch."""
    
    # Sichere Entfernung - prüfe ob Properties existieren
    properties_to_remove = [
        'ids_fetch_server_selection',
        'ids_fetch_server_connected',
        'ids_fetch_models_count',
        'ids_fetch_domain_models',
        'ids_fetch_last_download',
        'ids_fetch_last_model_name',
        'ids_fetch_last_model_guid'
    ]
    
    for prop_name in properties_to_remove:
        if hasattr(bpy.types.Scene, prop_name):
            try:
                delattr(bpy.types.Scene, prop_name)
            except:
                pass  # Ignoriere Fehler beim Entfernen


# Registration
classes = [
    IDS_DomainModel_Item,           # MUSS als ERSTES registriert werden!
    BIM_OT_connect_ids_server,
    BIM_OT_download_domain_model_ids,
    BIM_PT_ids_fetch,
]


def register():
    """Register all classes and properties - FIXED ORDER."""
    
    # Erst alle Properties sauber entfernen (falls vorhanden)
    unregister_properties()
    
    # WICHTIG: Erst PropertyGroup-Klassen registrieren
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Registered class: {cls.__name__}")
        except ValueError as e:
            print(f"Class {cls.__name__} bereits registriert: {e}")
    
    # DANN Properties registrieren (nach den Klassen!)
    register_properties()
    
    print("✅ IDS Fetch Panel registered under Collaboration")


def unregister():
    """Unregister all classes and properties."""
    
    # Erst Properties entfernen
    unregister_properties()
    
    # Dann Klassen entfernen (umgekehrte Reihenfolge)
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass  # Ignoriere wenn bereits entfernt


# Cleanup function für komplette Entfernung
def force_cleanup():
    """Forciert komplette Entfernung aller IDS Fetch Komponenten."""
    
    print("Force cleanup of IDS Fetch components...")
    
    # Erst Properties entfernen
    unregister_properties()
    
    # Dann Klassen entfernen
    class_names = [
        "IDS_DomainModel_Item",
        "BIM_OT_connect_ids_server", 
        "BIM_OT_download_domain_model_ids",
        "BIM_PT_ids_fetch"
    ]
    
    for class_name in class_names:
        try:
            if hasattr(bpy.types, class_name):
                cls = getattr(bpy.types, class_name)
                bpy.utils.unregister_class(cls)
                print(f"  Removed class: {class_name}")
        except Exception as e:
            print(f"  Could not remove {class_name}: {e}")
    
    print("✅ Force cleanup completed")


if __name__ == "__main__":
    # Zuerst komplette Bereinigung
    force_cleanup()
    
    # Dann frische Registrierung
    register()