#!/usr/bin/env python3
"""
Complete IDS Fetch Panel Removal Script
========================================

Entfernt alle IDS Fetch Komponenten sauber und vollständig aus Blender/Bonsai.
Kann mehrmals ausgeführt werden ohne Fehler zu verursachen.
"""

import bpy

def remove_ids_fetch_properties():
    """Entfernt alle IDS Fetch Properties von Scene UND löscht gespeicherte Werte."""
    
    print("🧹 Removing IDS Fetch Properties...")
    
    properties_to_remove = [
        'ids_fetch_server_selection',
        'ids_fetch_server_connected',
        'ids_fetch_models_count', 
        'ids_fetch_domain_models',
        'ids_fetch_last_download',
        'ids_fetch_last_model_name',
        'ids_fetch_last_model_guid'
    ]
    
    removed_count = 0
    scene = bpy.context.scene
    
    for prop_name in properties_to_remove:
        # WICHTIG: Erst gespeicherte Werte aus Scene löschen
        if hasattr(scene, prop_name):
            try:
                # Gespeicherte Werte in der Scene löschen
                if prop_name == 'ids_fetch_domain_models':
                    # CollectionProperty leeren
                    scene.ids_fetch_domain_models.clear()
                    print(f"  🧹 Cleared scene data: {prop_name}")
                else:
                    # Einfache Properties zurücksetzen
                    if prop_name == 'ids_fetch_server_connected':
                        scene.ids_fetch_server_connected = False
                    elif prop_name == 'ids_fetch_models_count':
                        scene.ids_fetch_models_count = 0
                    elif prop_name in ['ids_fetch_last_download', 'ids_fetch_last_model_name', 'ids_fetch_last_model_guid']:
                        setattr(scene, prop_name, "")
                    print(f"  🧹 Reset scene data: {prop_name}")
            except Exception as e:
                print(f"  ⚠️ Could not reset scene data {prop_name}: {e}")
        
        # DANN Property-Definition entfernen
        if hasattr(bpy.types.Scene, prop_name):
            try:
                delattr(bpy.types.Scene, prop_name)
                print(f"  ✅ Removed property definition: {prop_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ Could not remove property {prop_name}: {e}")
        else:
            print(f"  ⚪ Property {prop_name} not found (already removed)")
    
    print(f"📊 Properties removed: {removed_count}/{len(properties_to_remove)}")


def remove_ids_fetch_classes():
    """Entfernt alle IDS Fetch Klassen."""
    
    print("🧹 Removing IDS Fetch Classes...")
    
    class_names = [
        "BIM_PT_ids_fetch",                    # Panel zuerst
        "BIM_OT_download_domain_model_ids",    # Operatoren
        "BIM_OT_connect_ids_server", 
        "IDS_DomainModel_Item"                 # PropertyGroup zuletzt
    ]
    
    removed_count = 0
    
    for class_name in class_names:
        try:
            if hasattr(bpy.types, class_name):
                cls = getattr(bpy.types, class_name)
                bpy.utils.unregister_class(cls)
                print(f"  ✅ Removed class: {class_name}")
                removed_count += 1
            else:
                print(f"  ⚪ Class {class_name} not found (already removed)")
        except Exception as e:
            print(f"  ❌ Could not remove class {class_name}: {e}")
    
    print(f"📊 Classes removed: {removed_count}/{len(class_names)}")


def check_ids_fetch_status():
    """Prüft ob noch IDS Fetch Komponenten vorhanden sind."""
    
    print("🔍 Checking IDS Fetch Status...")
    
    # Properties prüfen
    properties_to_check = [
        'ids_fetch_server_selection',
        'ids_fetch_server_connected', 
        'ids_fetch_models_count',
        'ids_fetch_domain_models',
        'ids_fetch_last_download',
        'ids_fetch_last_model_name',
        'ids_fetch_last_model_guid'
    ]
    
    remaining_properties = []
    for prop_name in properties_to_check:
        if hasattr(bpy.types.Scene, prop_name):
            remaining_properties.append(prop_name)
    
    # Klassen prüfen
    class_names = [
        "IDS_DomainModel_Item",
        "BIM_OT_connect_ids_server",
        "BIM_OT_download_domain_model_ids", 
        "BIM_PT_ids_fetch"
    ]
    
    remaining_classes = []
    for class_name in class_names:
        if hasattr(bpy.types, class_name):
            remaining_classes.append(class_name)
    
    # Status Report
    if not remaining_properties and not remaining_classes:
        print("✅ IDS Fetch Panel completely removed - all clean!")
        return True
    else:
        print("⚠️  Some components still remain:")
        if remaining_properties:
            print(f"  📝 Properties: {remaining_properties}")
        if remaining_classes:
            print(f"  🏷️  Classes: {remaining_classes}")
        return False


def force_remove_ids_fetch():
    """Forciert komplette Entfernung aller IDS Fetch Komponenten."""
    
    print("🚀 Force Remove IDS Fetch Panel")
    print("=" * 50)
    
    # Step 1: Properties entfernen
    remove_ids_fetch_properties()
    
    print()
    
    # Step 2: Klassen entfernen  
    remove_ids_fetch_classes()
    
    print()
    
    # Step 3: Status prüfen
    is_clean = check_ids_fetch_status()
    
    print("=" * 50)
    if is_clean:
        print("🎉 IDS Fetch Panel successfully removed!")
    else:
        print("⚠️  Some components may still remain - check console output")
    
    return is_clean


def safe_remove_ids_fetch():
    """Sichere Entfernung mit Bestätigung."""
    
    print("🛡️  Safe Remove IDS Fetch Panel")
    print("=" * 50)
    
    # Erst Status prüfen
    print("Current status:")
    has_components = not check_ids_fetch_status()
    
    if not has_components:
        print("✅ Nothing to remove - IDS Fetch Panel already clean!")
        return True
    
    print("\n⚠️  Found IDS Fetch components - proceeding with removal...")
    print()
    
    # Dann entfernen
    return force_remove_ids_fetch()


# Verschiedene Entfernungsoptionen
def remove_only_ui():
    """Entfernt nur das UI Panel, behält Properties."""
    
    print("🎨 Removing only UI components...")
    
    ui_classes = [
        "BIM_PT_ids_fetch",
        "BIM_OT_connect_ids_server",
        "BIM_OT_download_domain_model_ids"
    ]
    
    for class_name in ui_classes:
        try:
            if hasattr(bpy.types, class_name):
                cls = getattr(bpy.types, class_name)
                bpy.utils.unregister_class(cls)
                print(f"  ✅ Removed UI class: {class_name}")
        except Exception as e:
            print(f"  ❌ Could not remove {class_name}: {e}")
    
    print("📊 UI components removed (Properties kept)")


def remove_only_properties():
    """Entfernt nur Properties, behält Klassen."""
    
    print("📝 Removing only Properties...")
    remove_ids_fetch_properties()
    print("📊 Properties removed (Classes kept)")


def interactive_removal():
    """Interaktive Entfernung mit Wahlmöglichkeiten."""
    
    print("🎛️  Interactive IDS Fetch Removal")
    print("=" * 40)
    print("Choose removal option:")
    print("1. Complete removal (Properties + Classes)")
    print("2. Remove only UI (keep Properties)")  
    print("3. Remove only Properties (keep Classes)")
    print("4. Just check status")
    print("5. Force complete cleanup")
    
    # Für Script-Ausführung - einfach Option hier setzen:
    choice = 1  # Ändere diese Zahl für andere Optionen
    
    print(f"\nSelected option: {choice}")
    print("-" * 40)
    
    if choice == 1:
        return safe_remove_ids_fetch()
    elif choice == 2:
        remove_only_ui()
        return check_ids_fetch_status()
    elif choice == 3:
        remove_only_properties()
        return check_ids_fetch_status()
    elif choice == 4:
        return check_ids_fetch_status()
    elif choice == 5:
        return force_remove_ids_fetch()
    else:
        print("❌ Invalid choice")
        return False


# Haupt-Ausführung
if __name__ == "__main__":
    # Verschiedene Optionen - eine davon auskommentieren:
    
    # Standard: Sichere komplette Entfernung
    safe_remove_ids_fetch()
    
    # Alternativen:
    # force_remove_ids_fetch()      # Forciert ohne Fragen
    # interactive_removal()          # Interaktiv mit Optionen
    # check_ids_fetch_status()       # Nur Status prüfen
    # remove_only_ui()               # Nur UI entfernen
    # remove_only_properties()       # Nur Properties entfernen


# Quick-Funktionen für einfache Nutzung:

def clean():
    """Shortcut: Komplette saubere Entfernung."""
    return safe_remove_ids_fetch()


def nuke():
    """Shortcut: Forcierte Entfernung.""" 
    return force_remove_ids_fetch()


def status():
    """Shortcut: Status prüfen."""
    return check_ids_fetch_status()


def reset_scene_data():
    """Shortcut: Nur Scene-Daten zurücksetzen (für Testing)."""
    scene = bpy.context.scene
    
    print("🔄 Resetting IDS Fetch scene data...")
    
    try:
        if hasattr(scene, 'ids_fetch_domain_models'):
            scene.ids_fetch_domain_models.clear()
            print("  🧹 Cleared domain models")
        
        if hasattr(scene, 'ids_fetch_server_connected'):
            scene.ids_fetch_server_connected = False
            print("  🔄 Reset server connection")
        
        if hasattr(scene, 'ids_fetch_models_count'):
            scene.ids_fetch_models_count = 0
            print("  🔄 Reset models count")
        
        # String properties zurücksetzen
        string_props = ['ids_fetch_last_download', 'ids_fetch_last_model_name', 'ids_fetch_last_model_guid']
        for prop in string_props:
            if hasattr(scene, prop):
                setattr(scene, prop, "")
                print(f"  🔄 Reset {prop}")
        
        print("✅ Scene data reset complete")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting scene data: {e}")
        return False


# Verwendung im Script Editor:
# clean()           # Für normale Entfernung
# nuke()            # Für forcierte Entfernung  
# status()          # Für Status-Check
# reset_scene_data() # Nur Scene-Daten zurücksetzen