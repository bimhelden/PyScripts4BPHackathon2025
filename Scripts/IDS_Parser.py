import xml.etree.ElementTree as ET
import bpy

# Define namespaces used in the XML
NS = {
    "ids": "http://standards.buildingsmart.org/IDS",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}

def parse_ids(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Show the console window of Blender
    bpy.ops.wm.console_toggle()

    # Extract info section
    info = root.find("ids:info", NS)
    if info is not None:
        title = info.findtext("ids:title", default="", namespaces=NS)
        version = info.findtext("ids:version", default="", namespaces=NS)
        description = info.findtext("ids:description", default="", namespaces=NS)
        date = info.findtext("ids:date", default="", namespaces=NS)
        purpose = info.findtext("ids:purpose", default="", namespaces=NS)
        milestone = info.findtext("ids:milestone", default="", namespaces=NS)

        print("=== Info ===")
        print(f"Title: {title}")
        print(f"Version: {version}")
        print(f"Description: {description}")
        print(f"Date: {date}")
        print(f"Purpose: {purpose}")
        print(f"Milestone: {milestone}")
        print()

    # Extract specifications
    specifications = root.find("ids:specifications", NS)
    if specifications is not None:
        print("=== Specifications ===")
        for spec in specifications.findall("ids:specification", NS):
            name = spec.get("name")
            ifc_version = spec.get("ifcVersion")
            identifier = spec.get("identifier")

            print(f"Specification: {name}")
            print(f"  IFC Version: {ifc_version}")
            print(f"  Identifier: {identifier}")

            # Applicability (entity types)
            applicability = spec.find("ids:applicability", NS)
            if applicability is not None:
                entities = applicability.findall(".//ids:simpleValue", NS)
                entity_names = [e.text for e in entities if e.text]
                print(f"  Entities: {', '.join(entity_names)}")

            # Requirements (properties)
            requirements = spec.find("ids:requirements", NS)
            if requirements is not None:
                for prop in requirements.findall("ids:property", NS):
                    uri = prop.get("uri")
                    cardinality = prop.get("cardinality")
                    data_type = prop.get("dataType")

                    prop_set = prop.findtext("ids:propertySet/ids:simpleValue", default="", namespaces=NS)
                    base_name = prop.findtext("ids:baseName/ids:simpleValue", default="", namespaces=NS)

                    print("  Property:")
                    print(f"    URI: {uri}")
                    print(f"    Cardinality: {cardinality}")
                    print(f"    DataType: {data_type}")
                    print(f"    PropertySet: {prop_set}")
                    print(f"    BaseName: {base_name}")
            print()

if __name__ == "__main__":
    # Example usage: adjust the filename as needed
    parse_ids("C://Users//MatthiasWeise//Downloads//example.ids")
