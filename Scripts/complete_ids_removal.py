#!/usr/bin/env python3
"""
Komplette IDS Converter Entfernung
==================================

Entfernt BEIDE IDS Converter komplett:
- IFC2IDS Converter
- IFCfromIDS Converter
- Alle zugehörigen Panels, Operatoren und Properties
"""

import bpy

def complete_ids_removal():
    """Entfernt alle IDS-bezogenen Komponenten vollständig."""
    
    print("=" * 60)
    print("KOMPLETTE IDS CONVERTER ENTFERNUNG")
    print("=" * 60)
    print("Entferne IFC2IDS + IFCfromIDS Converter...")
    
    # Alle IDS-bezogenen Panels
    all_panels = [
        # IFC2IDS Panels
        "BIM_PT_ifc2ids_converter",
        "BIM_PT_ifc2ids_patch", 
        "BIM_PT_ifc2ids_results",
        
        # IFCfromIDS Panels
        "BIM_PT_ifcfromids_converter",
        "BIM_PT_ifcfromids_results",
        "BIM_PT_ifcfromids_validation"
    ]
    
    # Alle IDS-bezogenen Operatoren
    all_operators = [
        # IFC2IDS Operatoren
        "BIM_OT_generate_ids_from_ifc",
        "BIM_OT_execute_ifc2ids_patch",
        "BIM_OT_select_ids_output_path",
        "BIM_OT_select_ifc2ids_output_path",
        "BIM_OT_open_ifc2ids_output",
        "BIM_OT_open_ifc2ids_directory",
        "BIM_OT_show_ifc2ids_summary",
        "BIM_OT_show_ifc2ids_summary_popup",
        
        # IFCfromIDS Operatoren
        "BIM_OT_load_ids_file",
        "BIM_OT_generate_ifc_template", 
        "BIM_OT_validate_current_ifc",
        "BIM_OT_select_ifcfromids_output",
        "BIM_OT_show_ids_summary"
    ]
    
    # Alle IDS-bezogenen Properties
    all_properties = [
        # IFC2IDS Properties
        "ifc2ids_specification_name",
        "ifc2ids_output_path",
        "ifc2ids_include_geometry", 
        "ifc2ids_open_output",
        "ifc2ids_summary",
        
        # IFCfromIDS Properties
        "ifcfromids_ids_path",
        "ifcfromids_output_path",
        "ifcfromids_use_current",
        "ifcfromids_spec_count", 
        "ifcfromids_summary"
    ]
    
    # 1. Panels entfernen
    print("\n1. Entferne Panels...")
    panels_removed = 0
    for panel_name in all_panels:
        try:
            panel_class = getattr(bpy.types, panel_name, None)
            if panel_class:
                bpy.utils.unregister_class(panel_class)
                print(f"   ✓ {panel_name}")
                panels_removed += 1
        except Exception as e:
            print(f"   - {panel_name} (nicht gefunden)")
    
    # 2. Operatoren entfernen
    print("\n2. Entferne Operatoren...")
    operators_removed = 0
    for operator_name in all_operators:
        try:
            operator_class = getattr(bpy.types, operator_name, None)
            if operator_class:
                bpy.utils.unregister_class(operator_class)
                print(f"   ✓ {operator_name}")
                operators_removed += 1
        except Exception as e:
            print(f"   - {operator_name} (nicht gefunden)")
    
    # 3. Properties entfernen
    print("\n3. Entferne Properties...")
    properties_removed = 0
    for prop_name in all_properties:
        try:
            if hasattr(bpy.types.Scene, prop_name):
                delattr(bpy.types.Scene, prop_name)
                print(f"   ✓ {prop_name}")
                properties_removed += 1
        except Exception as e:
            print(f"   - {prop_name} (Fehler: {e})")
    
    # 4. Zusätzliche Aufräumarbeiten
    print("\n4. Zusätzliche Aufräumarbeiten...")
    
    # Temporäre Properties entfernen
    temp_properties = [
        "bim_portal_search",
        "ids_validation_results",
        "current_ids_spec"
    ]
    
    for prop_name in temp_properties:
        try:
            if hasattr(bpy.types.Scene, prop_name):
                delattr(bpy.types.Scene, prop_name)
                print(f"   ✓ Temp property: {prop_name}")
        except:
            pass
    
    # 5. Force Remove für übrig gebliebene IDS Komponenten
    print("\n5. Force Remove für übrig gebliebene Komponenten...")
    
    all_types = dir(bpy.types)
    force_removed = 0
    
    for type_name in all_types:
        if ('ifc2ids' in type_name.lower() or 
            'ifcfromids' in type_name.lower() or
            'ids_converter' in type_name.lower()):
            try:
                type_class = getattr(bpy.types, type_name)
                if hasattr(type_class, 'bl_rna'):
                    bpy.utils.unregister_class(type_class)
                    print(f"   ✓ Force removed: {type_name}")
                    force_removed += 1
            except Exception as e:
                print(f"   - Konnte {type_name} nicht entfernen: {e}")
    
    # 6. Abschlussprüfung
    print("\n6. Abschlussprüfung...")
    
    remaining_panels = [name for name in dir(bpy.types) 
                       if ('ifc2ids' in name.lower() or 'ifcfromids' in name.lower()) 
                       and name.startswith('BIM_PT')]
    
    remaining_operators = [name for name in dir(bpy.types)
                          if ('ifc2ids' in name.lower() or 'ifcfromids' in name.lower()) 
                          and name.startswith('BIM_OT')]
    
    remaining_props = [name for name in dir(bpy.types.Scene)
                      if ('ifc2ids' in name.lower() or 'ifcfromids' in name.lower())]
    
    # Ergebnisse
    print("\n" + "=" * 60)
    print("ENTFERNUNG ABGESCHLOSSEN")
    print("=" * 60)
    print(f"✓ Panels entfernt: {panels_removed}")
    print(f"✓ Operatoren entfernt: {operators_removed}")
    print(f"✓ Properties entfernt: {properties_removed}")
    print(f"✓ Force removed: {force_removed}")
    
    if remaining_panels or remaining_operators or remaining_props:
        print("\n⚠ WARNUNG - Noch vorhandene Komponenten:")
        if remaining_panels:
            print(f"   Panels: {remaining_panels}")
        if remaining_operators:
            print(f"   Operatoren: {remaining_operators}")
        if remaining_props:
            print(f"   Properties: {remaining_props}")
        print("\n   → Blender neu starten empfohlen!")
    else:
        print("\n✅ VOLLSTÄNDIG ENTFERNT")
        print("   Alle IDS Converter Komponenten wurden erfolgreich entfernt!")
    
    print("\n" + "=" * 60)


def nuclear_option_ids_cleanup():
    """NUKLEAR-OPTION: Entfernt ALLES was mit IDS zu tun hat."""
    
    print("\n🚨 NUKLEAR-OPTION AKTIVIERT 🚨")
    print("Entferne ALLES was mit IDS zu tun hat...")
    
    # Alle Typen durchgehen und alles mit 'ids' entfernen
    all_types = list(dir(bpy.types))
    nuclear_removed = 0
    
    for type_name in all_types:
        if ('ids' in type_name.lower() and 
            any(prefix in type_name for prefix in ['BIM_', 'IFC_', 'Ifc']) and
            type_name not in ['BIM_PT_ids', 'BIM_OT_ids']):  # Basis-Namen ausschließen
            try:
                type_class = getattr(bpy.types, type_name)
                if hasattr(type_class, 'bl_rna'):
                    bpy.utils.unregister_class(type_class)
                    print(f"   💥 Nuclear removed: {type_name}")
                    nuclear_removed += 1
            except Exception as e:
                print(f"   ❌ Nuclear failed on {type_name}: {e}")
    
    # Alle Scene Properties mit 'ids' entfernen
    scene_props = list(dir(bpy.types.Scene))
    for prop_name in scene_props:
        if 'ids' in prop_name.lower():
            try:
                delattr(bpy.types.Scene, prop_name)
                print(f"   💥 Nuclear removed property: {prop_name}")
                nuclear_removed += 1
            except:
                pass
    
    print(f"\n💥 Nuclear Option entfernte {nuclear_removed} zusätzliche Komponenten")


def main():
    """Hauptfunktion - Komplette Entfernung."""
    
    try:
        # Standard komplette Entfernung
        complete_ids_removal()
        
        # Uncomment für nuklear Option:
        # nuclear_option_ids_cleanup()
        
    except Exception as e:
        print(f"\n❌ FEHLER bei der Entfernung: {e}")
        print("Versuche nuklear Option...")
        nuclear_option_ids_cleanup()
    
    print("\n🔄 EMPFEHLUNG:")
    print("   Starte Blender jetzt neu für eine vollständig saubere Umgebung!")
    print("   Alle IDS Converter wurden entfernt.")


# Ausführung
if __name__ == "__main__":
    main()
