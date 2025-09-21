#!/usr/bin/env python3
"""
IFC2IDS Recipe for IfcPatch
============================

This recipe converts IFC model elements to Information Delivery Specification (IDS) files.
It generates IDS specifications based on the analysis of existing IFC elements, properties,
and relationships within the model.

Usage:
    ifcpatch -i input.ifc -r Ifc2Ids -a [output_path] [include_geometry] [specification_name]

Arguments:
    output_path (str, optional): Path for the output IDS file. Default: "output.ids"
    include_geometry (bool, optional): Whether to include geometric requirements. Default: False
    specification_name (str, optional): Name of the IDS specification. Default: "Generated from IFC"

Example:
    ifcpatch -i model.ifc -r Ifc2Ids -a "requirements.ids" True "Building Requirements"
"""

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.system
from ifctester import ids
import logging
from typing import List, Dict, Set, Optional, Any
import json
from pathlib import Path


class Patcher:
    """IFC to IDS converter patch recipe."""
    
    def __init__(
        self, 
        src: str, 
        file: ifcopenshell.file, 
        logger: logging.Logger,
        output_path: str = "output.ids",
        include_geometry: bool = False,
        specification_name: str = "Generated from IFC"
    ):
        """
        Initialize the IFC2IDS converter.
        
        Args:
            src: Source file path
            file: IfcOpenShell file object
            logger: Logger instance
            output_path: Path for the output IDS file
            include_geometry: Whether to include geometric requirements
            specification_name: Name of the IDS specification
        """
        self.src = src
        self.file = file
        self.logger = logger
        self.output_path = output_path
        self.include_geometry = include_geometry
        self.specification_name = specification_name
        
        # Analysis storage
        self.element_stats = {}
        self.property_stats = {}
        self.material_stats = {}
        self.classification_stats = {}
        
        # Process the IFC file
        self.patch()
    
    def patch(self) -> None:
        """Main processing method."""
        self.logger.info(f"Starting IFC2IDS conversion for {self.src}")
        
        # Analyze the IFC model
        self._analyze_model()
        
        # Create IDS specifications
        ids_spec = self._create_ids_specification()
        
        # Save the IDS file
        self._save_ids_file(ids_spec)
        
        self.logger.info(f"IFC2IDS conversion completed. Output: {self.output_path}")
    
    def _analyze_model(self) -> None:
        """Analyze the IFC model to extract relevant information."""
        self.logger.info("Analyzing IFC model structure...")
        
        # Analyze elements by type
        for element in self.file.by_type("IfcProduct"):
            if not element.is_a("IfcProduct"):
                continue
                
            element_type = element.is_a()
            
            # Count elements by type
            if element_type not in self.element_stats:
                self.element_stats[element_type] = {
                    'count': 0,
                    'properties': set(),
                    'materials': set(),
                    'classifications': set()
                }
            
            self.element_stats[element_type]['count'] += 1
            
            # Analyze properties
            self._analyze_element_properties(element, element_type)
            
            # Analyze materials
            self._analyze_element_materials(element, element_type)
            
            # Analyze classifications
            self._analyze_element_classifications(element, element_type)
    
    def _analyze_element_properties(self, element: ifcopenshell.entity_instance, element_type: str) -> None:
        """Analyze properties of an element."""
        try:
            psets = ifcopenshell.util.element.get_psets(element)
            
            for pset_name, properties in psets.items():
                if not isinstance(properties, dict):
                    continue
                    
                # Track property set usage
                pset_key = f"{pset_name}"
                if pset_key not in self.property_stats:
                    self.property_stats[pset_key] = {
                        'elements': set(),
                        'properties': {},
                        'count': 0
                    }
                
                self.property_stats[pset_key]['elements'].add(element_type)
                self.property_stats[pset_key]['count'] += 1
                self.element_stats[element_type]['properties'].add(pset_name)
                
                # Track individual properties
                for prop_name, prop_value in properties.items():
                    if prop_name not in self.property_stats[pset_key]['properties']:
                        self.property_stats[pset_key]['properties'][prop_name] = {
                            'values': set(),
                            'data_types': set(),
                            'count': 0
                        }
                    
                    prop_info = self.property_stats[pset_key]['properties'][prop_name]
                    prop_info['count'] += 1
                    
                    if prop_value is not None:
                        prop_info['values'].add(str(prop_value))
                        prop_info['data_types'].add(type(prop_value).__name__)
        
        except Exception as e:
            self.logger.warning(f"Could not analyze properties for {element}: {e}")
    
    def _analyze_element_materials(self, element: ifcopenshell.entity_instance, element_type: str) -> None:
        """Analyze materials associated with an element."""
        try:
            materials = ifcopenshell.util.element.get_materials(element)
            
            if materials:
                for material in materials:
                    if hasattr(material, 'Name') and material.Name:
                        material_name = material.Name
                        
                        if material_name not in self.material_stats:
                            self.material_stats[material_name] = {
                                'elements': set(),
                                'count': 0,
                                'type': material.is_a()
                            }
                        
                        self.material_stats[material_name]['elements'].add(element_type)
                        self.material_stats[material_name]['count'] += 1
                        self.element_stats[element_type]['materials'].add(material_name)
        
        except Exception as e:
            self.logger.warning(f"Could not analyze materials for {element}: {e}")
    
    def _analyze_element_classifications(self, element: ifcopenshell.entity_instance, element_type: str) -> None:
        """Analyze classifications associated with an element."""
        try:
            # Check for classification associations
            if hasattr(element, 'HasAssociations') and element.HasAssociations:
                for association in element.HasAssociations:
                    if association.is_a('IfcRelAssociatesClassification'):
                        classification = association.RelatingClassification
                        
                        if hasattr(classification, 'Name') and classification.Name:
                            class_name = classification.Name
                            
                            if class_name not in self.classification_stats:
                                self.classification_stats[class_name] = {
                                    'elements': set(),
                                    'count': 0
                                }
                            
                            self.classification_stats[class_name]['elements'].add(element_type)
                            self.classification_stats[class_name]['count'] += 1
                            self.element_stats[element_type]['classifications'].add(class_name)
        
        except Exception as e:
            self.logger.warning(f"Could not analyze classifications for {element}: {e}")
    
    def _create_ids_specification(self) -> ids.Ids:
        """Create IDS specification based on the analysis."""
        self.logger.info("Creating IDS specification...")
        
        # Create main IDS container
        project_info = self._get_project_info()
        
        ids_spec = ids.Ids(
            title=self.specification_name,
            description=f"IDS specification generated from IFC model: {Path(self.src).name}",
            author="IfcOpenShell IFC2IDS Recipe",
            purpose="Validation and quality control",
            milestone="Generated specification"
        )
        
        # Create specifications for common element types
        self._create_element_specifications(ids_spec)
        
        # Create property specifications
        self._create_property_specifications(ids_spec)
        
        # Create material specifications
        #self._create_material_specifications(ids_spec)
        
        # Create classification specifications
        #self._create_classification_specifications(ids_spec)
        
        return ids_spec
    
    def _get_project_info(self) -> Dict[str, Any]:
        """Extract project information from IFC."""
        project_info = {}
        
        try:
            project = self.file.by_type("IfcProject")[0]
            project_info['name'] = getattr(project, 'Name', 'Unknown Project')
            project_info['description'] = getattr(project, 'Description', '')
        except:
            project_info['name'] = 'Unknown Project'
            project_info['description'] = ''
        
        return project_info
    
    def _create_element_specifications(self, ids_spec: ids.Ids) -> None:
        """Create specifications for element types."""
        for element_type, stats in self.element_stats.items():
            if stats['count'] < 2:  # Skip types with very few instances
                continue
            
            # Create specification for this element type
            spec = ids.Specification(
                name=f"{element_type} Requirements",
                description=f"Requirements for {element_type} elements (found {stats['count']} instances)",
                instructions=f"All {element_type} elements must meet these requirements"
            )
            
            # Add applicability - the element type
            spec.applicability.append(ids.Entity(name=element_type))
            
            # Add basic requirements
            if self.include_geometry and element_type in ["IFCWALL", "IFCSLAB", "IFCBEAM", "IFCCOLUMN"]:
                # Add geometric representation requirement for structural elements
                requirement = ids.Attribute(
                    name="Representation",
                    cardinality="required",
                    instructions=f"{element_type} must have geometric representation"
                )
                spec.requirements.append(requirement)
            
            # Add property requirement if this type commonly has properties
            if stats['properties']:
                common_pset = max(stats['properties'], key=lambda x: 
                    self.property_stats.get(x, {}).get('count', 0))
                
                requirement = ids.Property(
                    baseName="*",  # Any property
                    propertySet=common_pset,
                    cardinality="optional",
                    instructions=f"Properties from {common_pset} should be provided where applicable"
                )
                spec.requirements.append(requirement)
            
            ids_spec.specifications.append(spec)
    
    def _create_property_specifications(self, ids_spec: ids.Ids) -> None:
        """Create specifications for important properties."""
        # Focus on most common property sets
        common_psets = sorted(
            self.property_stats.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:5]  # Top 5 most common property sets
        
        for pset_name, pset_info in common_psets:
            if pset_info['count'] < 3:  # Skip rarely used property sets
                continue
            
            spec = ids.Specification(
                name=f"{pset_name} Properties",
                description=f"Property requirements for {pset_name}",
                instructions=f"Elements with {pset_name} must have consistent property definitions"
            )
            
            # Apply to all element types that use this property set
            for element_type in pset_info['elements']:
                spec.applicability.append(ids.Entity(name=element_type))
            
            # Add requirements for critical properties
            critical_props = sorted(
                pset_info['properties'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:3]  # Top 3 most common properties in this set
            
            for prop_name, prop_info in critical_props:
                if prop_info['count'] >= 2:  # Property appears multiple times
                    requirement = ids.Property(
                        baseName=prop_name,
                        propertySet=pset_name,
                        cardinality="optional" if prop_info['count'] < pset_info['count'] * 0.5 else "required",
                        instructions=f"{prop_name} should be consistently defined"
                    )
                    spec.requirements.append(requirement)
            
            if spec.requirements:  # Only add if we have requirements
                ids_spec.specifications.append(spec)
    
    def _create_material_specifications(self, ids_spec: ids.Ids) -> None:
        """Create specifications for materials."""
        if not self.material_stats:
            return
        
        # Create general material specification
        spec = ids.Specification(
            name="Material Requirements",
            description="Material assignment requirements for building elements",
            instructions="All applicable elements must have proper material assignments"
        )
        
        # Apply to all element types that have materials
        material_element_types = set()
        for material_info in self.material_stats.values():
            material_element_types.update(material_info['elements'])
        
        for element_type in material_element_types:
            spec.applicability.append(ids.Entity(name=element_type))
        
        # Require material assignment
        requirement = ids.Material(
            value="*",  # Any material
            cardinality="required",
            instructions="All building elements must have material assignments"
        )
        spec.requirements.append(requirement)
        
        ids_spec.specifications.append(spec)
    
    def _create_classification_specifications(self, ids_spec: ids.Ids) -> None:
        """Create specifications for classifications."""
        if not self.classification_stats:
            return
        
        for class_name, class_info in self.classification_stats.items():
            if class_info['count'] < 2:
                continue
            
            spec = ids.Specification(
                name=f"Classification: {class_name}",
                description=f"Classification requirements for {class_name}",
                instructions=f"Elements classified as {class_name} must meet these requirements"
            )
            
            # Apply to all element types that use this classification
            for element_type in class_info['elements']:
                spec.applicability.append(ids.Entity(name=element_type))
            
            # Require the classification
            requirement = ids.Classification(
                value=class_name,
                cardinality="required",
                instructions=f"Must be classified as {class_name}"
            )
            spec.requirements.append(requirement)
            
            ids_spec.specifications.append(spec)
    
    def _save_ids_file(self, ids_spec: ids.Ids) -> None:
        """Save the IDS specification to file."""
        try:
            ids_spec.to_xml(self.output_path)
            self.logger.info(f"IDS file saved to: {self.output_path}")
            
            # Also create a summary report
            self._create_summary_report(ids_spec)
            
        except Exception as e:
            self.logger.error(f"Failed to save IDS file: {e}")
            raise
    
    def _create_summary_report(self, ids_spec: ids.Ids) -> None:
        """Create a summary report of the conversion."""
        summary_path = Path(self.output_path).with_suffix('.json')
        
        summary = {
            'source_ifc': self.src,
            'ids_output': self.output_path,
            'specification_name': self.specification_name,
            'analysis_summary': {
                'total_element_types': len(self.element_stats),
                'total_elements': sum(stats['count'] for stats in self.element_stats.values()),
                'property_sets_found': len(self.property_stats),
                'materials_found': len(self.material_stats),
                'classifications_found': len(self.classification_stats),
                'specifications_created': len(ids_spec.specifications)
            },
            'element_breakdown': {
                element_type: stats['count'] 
                for element_type, stats in self.element_stats.items()
            },
            'top_property_sets': [
                {'name': pset_name, 'usage_count': info['count']}
                for pset_name, info in sorted(
                    self.property_stats.items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:10]
            ]
        }
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary report saved to: {summary_path}")
        except Exception as e:
            self.logger.warning(f"Could not save summary report: {e}")


# Factory function for IfcPatch integration
def execute(args):
    """Execute the IFC2IDS patch recipe."""
    file = args.get("file")
    input_path = args.get("input", "")
    arguments = args.get("arguments", [])
    
    # Parse arguments
    output_path = arguments[0] if len(arguments) > 0 else "output.ids"
    include_geometry = bool(arguments[1]) if len(arguments) > 1 else False
    specification_name = arguments[2] if len(arguments) > 2 else "Generated from IFC"
    
    # Create logger
    logger = logging.getLogger(__name__)
    
    # Execute the patch
    patcher = Patcher(
        src=input_path,
        file=file,
        logger=logger,
        output_path=output_path,
        include_geometry=include_geometry,
        specification_name=specification_name
    )
    
    return None  # This recipe saves files directly


if __name__ == "__main__":
    # For testing purposes
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python Ifc2Ids.py <input.ifc> [output.ids] [include_geometry] [specification_name]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.ids"
    include_geom = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    spec_name = sys.argv[4] if len(sys.argv) > 4 else "Generated from IFC"
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load IFC file
    file = ifcopenshell.open(input_file)
    
    # Execute conversion
    patcher = Patcher(
        src=input_file,
        file=file,
        logger=logger,
        output_path=output_file,
        include_geometry=include_geom,
        specification_name=spec_name
    )
    
    print(f"Conversion completed. IDS file saved to: {output_file}")
