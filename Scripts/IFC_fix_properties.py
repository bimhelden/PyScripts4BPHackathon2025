import ifcopenshell
import json
import bpy


def read_json_config(ifc_type, json_config):
    if ifc_type in json_config:
        return json_config[ifc_type]
    return None

def process_ifc_file(ifc_file, json_config):
    # Open the IFC file
    ifc_model = ifcopenshell.open(ifc_file)

    # Iterate through each IFC type in the JSON config
    for ifc_type, config in json_config.items():
        # Check if the IFC type exists in the model
        if ifc_model.by_type(ifc_type):
            instances = ifc_model.by_type(ifc_type)
            print(f"\nProcessing {len(instances)} instances of {ifc_type}")

            # Print all property values for each instance
            for instance in instances[:config['instances']]:
                print(f"\nInstance ID: {instance.id()}")

                # Check if the instance has the specified property set
                if 'IsDefinedBy' in dir(instance):
                    defined_by = instance.IsDefinedBy

                    # Iterate through each property set attached to the instance
                    for rel_defines in defined_by:
                        if rel_defines.is_a("IfcRelDefinesByProperties"):
                            property_set = rel_defines.RelatingPropertyDefinition

                            # Get the Property Set name
                            property_set_name = property_set.Name if 'Name' in dir(property_set) else "Unknown Property Set"

                            # Check if the property set is in the JSON config
                            if property_set_name in config['properties_values']:
                                # Print only the properties defined in the JSON config
                                print(f"\nProperty Set: {property_set_name}")

                                # check if Pset name should be replaced
                                if config['properties_values'][property_set_name].get('replace_name') is not None:
                                    # TODO: check if Pset with same name already exists
                                    print(f"Replace {property_set_name} by {config['properties_values'][property_set_name]['replace_name']}")
                                    property_set.Name = config['properties_values'][property_set_name]['replace_name']

                                # Iterate through each property in the property set
                                for property_single_value in property_set.HasProperties:
                                    handle_property_single_value(property_single_value, config['properties_values'][property_set_name])

    # Save the modified IFC model to a new file
    output_file = ifc_file.replace('.ifc', '_fixed.ifc')
    ifc_model.write(output_file)


def handle_property_single_value(property_single_value, properties_values):
    property_name = property_single_value.Name
    if (properties_values.get(property_name) is not None and
            properties_values[property_name].get('replace_name') is not None):
        # TODO: check if Pset with same name already exists
        print(f"Replace {property_name} by {properties_values[property_name]['replace_name']}")
        property_single_value.Name = properties_values[property_name]['replace_name']

    if property_single_value.is_a("IfcPropertySingleValue"):
        # Check if NominalValue has a wrappedValue
        if property_single_value.NominalValue is not None and 'wrappedValue' in dir(property_single_value.NominalValue):
            property_value = property_single_value.NominalValue.wrappedValue

            # Check if the property is in the JSON config
            if property_name in properties_values:
                # Replace values based on the JSON config
                if properties_values[property_name].get('replace_values') is not None:
                    for old_value, new_value in properties_values[property_name]['replace_values'].items():
                        # Convert the old_value to the same type as property_value
                        old_value = type(property_value)(old_value)

                        if property_value == old_value:
                            # Print debugging information
                            print(f"Replacing {old_value} with {new_value} for Property: {property_name}")

                            # Convert the new_value to the same type as property_value
                            new_value = type(property_value)(new_value)
                            property_single_value.NominalValue.wrappedValue = new_value

if __name__ == "__main__":
    # Specify the IFC file and JSON config file
    ifc_file = "IFC/Architektur_Tragwerksplanung.ifc"
    json_config_file = ifc_file.replace('.ifc', '_fix_instructions.json')

    # Show the console window of Blender
    bpy.ops.wm.console_toggle()

    # Load the JSON config
    with open(json_config_file, 'r', encoding='utf-8') as json_file:
        json_config = json.load(json_file)

    print(json_config)

    # Process the IFC file with the given JSON config
    process_ifc_file(ifc_file, json_config)
