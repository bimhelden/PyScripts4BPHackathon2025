#!/usr/bin/env python3
"""
IDS PATCH Panel - Complete Removal
==================================

Entfernt das IDS PATCH Panel komplett und sauber.
Für Bonsai-sicheren Cleanup ohne .blend Speichern.
"""

import bpy


def remove_ids_patch_properties():
    """Entfernt alle IDS PATCH Properties."""
    print("🧹 Removing IDS PATCH properties...")
    
    properties = [
        'ids_patch_ifc_file_path',
        'ids_patch_ifc_file_loaded',
        'ids_patch_ids_file_path', 
        'ids_patch_ids_file_loaded'
    ]
    
    removed_count = 0
    for prop in properties:
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
                print(f"  ✓ Removed: {prop}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed: {prop} - {e}")
    
    print(f"✅ Removed {removed_count} properties")
    return removed_count


def remove_ids_patch_classes():
    """Entfernt alle IDS PATCH Classes."""
    print("🧹 Removing IDS PATCH classes...")
    
    classes = [
        "IDS_PATCH_PT_panel",
        "IDS_PATCH_OT_load_ids_file",
        "IDS_PATCH_OT_load_ifc_file"
    ]
    
    removed_count = 0
    for class_name in classes:
        if hasattr(bpy.types, class_name):
            try:
                cls = getattr(bpy.types, class_name)
                bpy.utils.unregister_class(cls)
                print(f"  ✓ Unregistered: {class_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed: {class_name} - {e}")
    
    print(f"✅ Unregistered {removed_count} classes")
    return removed_count


def reset_scene_data():
    """Setzt Scene-Daten auf Default-Werte (Bonsai-sicher)."""
    print("🧹 Resetting scene data...")
    
    scene = bpy.context.scene
    reset_count = 0
    
    # Reset zu "unsichtbaren" Defaults
    try:
        if hasattr(scene, 'ids_patch_ifc_file_loaded'):
            scene.ids_patch_ifc_file_loaded = False
            print("  ✓ Reset ifc_file_loaded to False")
            reset_count += 1
    except:
        pass
    
    try:
        if hasattr(scene, 'ids_patch_ids_file_loaded'):
            scene.ids_patch_ids_file_loaded = False
            print("  ✓ Reset ids_file_loaded to False")
            reset_count += 1
    except:
        pass
    
    try:
        if hasattr(scene, 'ids_patch_ifc_file_path'):
            scene.ids_patch_ifc_file_path = ""
            print("  ✓ Reset ifc_file_path to empty")
            reset_count += 1
    except:
        pass
    
    try:
        if hasattr(scene, 'ids_patch_ids_file_path'):
            scene.ids_patch_ids_file_path = ""
            print("  ✓ Reset ids_file_path to empty")
            reset_count += 1
    except:
        pass
    
    print(f"✅ Reset {reset_count} scene values")
    return reset_count


def verify_cleanup():
    """Überprüft ob alles sauber entfernt wurde."""
    print("🔍 Verifying cleanup...")
    
    # Check Properties
    properties = ['ids_patch_ifc_file_path', 'ids_patch_ifc_file_loaded',
                 'ids_patch_ids_file_path', 'ids_patch_ids_file_loaded']
    
    remaining_properties = []
    for prop in properties:
        if hasattr(bpy.types.Scene, prop):
            remaining_properties.append(prop)
    
    # Check Classes
    classes = ["IDS_PATCH_PT_panel", "IDS_PATCH_OT_load_ifc_file", 
              "IDS_PATCH_OT_load_ids_file"]
    
    remaining_classes = []
    for class_name in classes:
        if hasattr(bpy.types, class_name):
            remaining_classes.append(class_name)
    
    # Report Status
    if not remaining_properties and not remaining_classes:
        print("✅ CLEANUP SUCCESSFUL - IDS PATCH completely removed!")
        return True
    else:
        print("⚠️ CLEANUP INCOMPLETE:")
        if remaining_properties:
            print(f"  Remaining Properties: {remaining_properties}")
        if remaining_classes:
            print(f"  Remaining Classes: {remaining_classes}")
        return False


def clean_ids_patch():
    """Hauptfunktion - Komplette IDS PATCH Entfernung."""
    print("🔥 CLEANING IDS PATCH PANEL")
    print("=" * 50)
    
    # Schritt 1: Scene Data reset (Bonsai-sicher)
    scene_count = reset_scene_data()
    print()
    
    # Schritt 2: Classes entfernen
    class_count = remove_ids_patch_classes()
    print()
    
    # Schritt 3: Properties entfernen
    prop_count = remove_ids_patch_properties()
    print()
    
    # Schritt 4: UI refresh
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        print("  ✓ UI refreshed")
    except:
        pass
    
    # Schritt 5: Cleanup verifizieren
    success = verify_cleanup()
    
    print("=" * 50)
    print("📊 CLEANUP SUMMARY:")
    print(f"  Scene data reset: {scene_count}")
    print(f"  Classes removed: {class_count}")
    print(f"  Properties removed: {prop_count}")
    print(f"  Status: {'✅ SUCCESS' if success else '⚠️ INCOMPLETE'}")
    print("=" * 50)
    
    if success:
        print("🎯 READY FOR FRESH IDS PATCH INSTALLATION!")
        print("✅ No .blend file saving required!")
    
    return success


def quick_status():
    """Schneller Status-Check."""
    panel_exists = hasattr(bpy.types, 'IDS_PATCH_PT_panel')
    props_exist = hasattr(bpy.types.Scene, 'ids_patch_ifc_file_loaded')
    
    print("🔍 IDS PATCH STATUS:")
    print(f"  Panel: {'✅ EXISTS' if panel_exists else '❌ NOT FOUND'}")
    print(f"  Properties: {'✅ EXISTS' if props_exist else '❌ NOT FOUND'}")
    
    if not panel_exists and not props_exist:
        print("✅ IDS PATCH is completely clean!")
    else:
        print("⚠️ IDS PATCH components found - use clean_ids_patch() to remove")


# Auto-execute
if __name__ == "__main__":
    print("🚀 AUTO-CLEANING IDS PATCH PANEL")
    clean_ids_patch()


# Available functions:
# clean_ids_patch()    # Complete removal (main function)
# quick_status()       # Quick status check
# verify_cleanup()     # Verification only