import json

'''
JSON Structure
{
    "name": "name",
    "width": "width",
    "height": "height"
}
'''

# only allow edits the events of scene: onframe, onstart
class PhaserScene:
    def __init__(self):
        pass

# fixme: raise NotSavedProjectException
class PhaserProject:
    def __init__(self, json=None):
        self.json = json
        self.name = ''
        self.width = 0
        self.height = 0
        self.scenes = []

        if json:
            self.fill_from_json(json)
    
    def fill_from_json(self, jsonstring):
        '''
        args:
            + json: json string

        fills the instance with data from json string
        '''
        _dict = json.loads(jsonstring)
        self.name = _dict['name']
        self.width = _dict['width']
        self.height = _dict['height']

    def get_json(self):
        '''
        returns the json representation of project
        '''
        _dict = {
            name: self.name,
            width: self.width,
            height: self.height
        }
        return json.dumps(_dict)