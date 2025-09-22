import xml.etree.ElementTree as ET

# Extract default namespace dynamically from root element
def get_namespaces(root):
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0].strip("{")
        return {"ids": uri}
    else:
        return {"ids": ""}  # no namespace


def parse_ids(xml_file):
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


if __name__ == "__main__":
    data = parse_ids("C://Users//MatthiasWeise//Downloads//example2.ids")
    output_file = "C://Users//MatthiasWeise//Downloads//example2.json"
    import json
    print(json.dumps(data, indent=2))

    # Export to JSON with UTF-8 encoding
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"JSON export finished: {output_file}")
