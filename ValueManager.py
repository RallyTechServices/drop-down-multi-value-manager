import sys
import logging, logging.config
import json
from pyral import Rally, rallyWorkset

class ValueManager:
    preview = True
    
    def __init__(self, rally, preview = True, values_have_key=False):
        self.rally = rally
        self.preview = preview
        self.values_have_key = values_have_key
        if ( self.preview ):
            logger.info("PREVIEW MODE")
        return
    
    def run(self, element_name, attribute_name, desired_values_filename):
        desired_value_names = self.load_desired_values(desired_values_filename)
        
        response = self.rally.get('TypeDefinition', fetch=True, query='ElementName = "{0}"'.format(element_name))
        if response.errors:
            logger.error(response.errors)
        
        element_typedef = response.next()
        attributes = element_typedef.Attributes
        attribute = [attribute for attribute in attributes if attribute.Name == attribute_name][0]
        
        attribute_definition_objectid = attribute.ObjectID  # Post this to /create to add a value
        
        # Get the AllowedValue objects
        allowed_values = attribute.AllowedValues

        values_to_modify = self.values_to_modify(allowed_values, desired_value_names)
        old_new_values = [(value.LocalizedStringValue, desired_value) for (value, desired_value) in values_to_modify]
        logger.info("Values to modify: %s", len(values_to_modify))
        for (value, desired_name) in values_to_modify:
            self.modify_value(value, desired_name)
        
        allowed_names_to_modify = [old for (old, new) in old_new_values]
        new_names_to_modify = [new for (old, new) in old_new_values]
        
        value_objects_to_remove = self.value_objects_to_remove(allowed_values, desired_value_names)
        # Filter out any that we plan to modify
        value_objects_to_remove = [value for value in value_objects_to_remove if value.LocalizedStringValue not in allowed_names_to_modify]
        logger.info("Values to remove: %s", len(value_objects_to_remove))
        for value in value_objects_to_remove:
            self.remove_value(value)
    
        names_to_add = self.value_names_to_add(allowed_values, desired_value_names)
        # Filter out any that we plan to modify
        names_to_add = [name for name in names_to_add if name not in new_names_to_modify]
        logger.info("Values to add: %s", len(names_to_add))
        for name in names_to_add:
            self.add_value(attribute_definition_objectid, name)
            
        return
    
    def load_desired_values(self, filename):
        desired_values = []
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                desired_values.append(line)
        return desired_values
        
    def value_objects_to_remove(self, allowed_values, desired_value_names):
        result = []
        # Get the value objects that have a name not in the desired values. Don't attempt to remove the null value (if present). This is returned automatically
        # by the API when a field is not marked "Required"
        result = [value for value in allowed_values if value.LocalizedStringValue not in desired_value_names and value.LocalizedStringValue != '']
        return result
        
    def value_names_to_add(self, allowed_values, desired_value_names):
        result = []
        # Get the localized display names for each AllowedValue object
        allowed_value_names = [value.LocalizedStringValue for value in allowed_values]
        # Get the value names to add that aren't in the current list of allowed values
        result = [value for value in desired_value_names if value not in allowed_value_names]
        return result
        
    def values_to_modify(self, allowed_values, desired_value_names):
        result = []
        desired_value_keys = {}
        
        if self.values_have_key:
            # Build a hash of the desired values by "key"
            for name in desired_value_names:
                key = self.get_key(name)
                if key:
                    desired_value_keys[key] = name
            
            # For each of the allowed values, find any that have the same "key" but a different value
            for allowed_value in allowed_values:
                allowed_name = allowed_value.LocalizedStringValue
                key = self.get_key(allowed_name)
                if key and key in desired_value_keys:
                    desired_name = desired_value_keys[key]
                    if desired_name != allowed_name:
                        result.append((allowed_value, desired_name))
        return result
            
    def get_key(self, name):
        split = name.split(' ')
        if len(split) > 1:
            return split[0]
        else:
            return None
            
    def remove_value(self, value):
        logger.info("Removing '%s'", value.LocalizedStringValue)
        if not self.preview:
            self.rally.delete('AllowedAttributeValue', value.ObjectID)
        return
    
    def modify_value(self, value, desired_name):
        logger.info("Modifying '%s' to new value '%s'", value.LocalizedStringValue, desired_name)
        if not self.preview:
            self.rally.post('AllowedAttributeValue', {
                "ObjectID": value.ObjectID,
                "StringValue": desired_name
            })
        return
    
    def add_value(self, attribute_definition_objectid, name):
        logger.info("Adding '%s'", name)
        if not self.preview:
            self.rally.create('AllowedAttributeValue', {
                "StringValue": name,
                "AttributeDefinition": '/attributedefinition/{0}'.format(attribute_definition_objectid)
            })
        return

if __name__ == "__main__":
    config_filename = sys.argv[1]
    desired_values_filename = sys.argv[2]
    
    # Set up logging
    with open('config/logging.json', "r", encoding="utf-8") as fd:
        logging.config.dictConfig(json.load(fd))
    logger = logging.getLogger("ValueManager")
    logger.info("Starting...")
    
    with open(config_filename, "r") as config_file:
        config = json.load(config_file)
    
    options = [opt for opt in sys.argv[1:] if opt.startswith('--')]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(config['server'], user, password, apikey=apikey, workspace=config['workspace'], project=config['project'])

    manager = ValueManager(rally, preview=config['preview'], values_have_key=config['values_have_key'])
    manager.run(config['element_name'], config['attribute_name'], desired_values_filename)
    logger.info("Done")
        