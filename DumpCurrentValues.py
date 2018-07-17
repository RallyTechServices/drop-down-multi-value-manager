import sys
import json
from pyral import Rally, rallyWorkset

class DumpCurrentValues:
    
    def __init__(self, rally):
        self.rally = rally
        return
    
    def run(self, element_name, attribute_name):
        
        response = self.rally.get('TypeDefinition', fetch=True, query='ElementName = "{0}"'.format(element_name))
        if response.errors:
            print(response.errors)
        
        element_typedef = response.next()
        attributes = element_typedef.Attributes
        attribute = [attribute for attribute in attributes if attribute.Name == attribute_name][0]
        
        attribute_definition_objectid = attribute.ObjectID  # Post this to /create to add a value
        
        # Get the AllowedValue objects
        allowed_values = attribute.AllowedValues
        
        for value in allowed_values:
            print(value.StringValue, value.ValueIndex)

if __name__ == "__main__":
    config_filename = sys.argv[1]
    
    with open(config_filename, "r") as config_file:
        config = json.load(config_file)
    
    options = [opt for opt in sys.argv[1:] if opt.startswith('--')]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    rally = Rally(config['server'], user, password, apikey=apikey, workspace=config['workspace'], project=config['project'])

    manager = DumpCurrentValues(rally)
    manager.run(config['element_name'], config['attribute_name'])
        