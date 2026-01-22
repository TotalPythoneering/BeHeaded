# MISSION: Create an independant tag file manager.
# STATUS: Research
# VERSION: 1.0.0
# NOTES: NamedDict Definition
# DATE: 2026-01-21 17:51:15
# FILE: named_dict.py
# AUTHOR: Randall Nagy
#

class NamedDict:
    ''' Files are / were just named sets of data. '''
    def __init__(self):
        self.name = None
        self.data = None

    @staticmethod
    def Create(name:str, data:dict):
        result = NamedDict()
        if name and not isinstance(name, str):
            name = str(name)
        if data and not isinstance(data, dict):
            data = dict()
        result.name = name
        result.data = data
        return result

    def __set_item__(self, key, value):
        ''' Support classic scripting 'ops. '''
        self.data[key] = str(value)
        
    def __get_item__(self, key):
        ''' Support classic scripting 'ops. '''
        return str(self.data[key])

    def __iter__(self):
        ''' Support classic iteratable 'ops. '''
        for key in self.data:
            yield key

    def __eq__(self, obj)->bool:
        ''' Provide an equality test. '''
        if id(self) == id(obj):
            return True
        if not isinstance(obj, NamedDict):
            return False
        if self.name != obj.name:
            return False
        return self.data == obj.data

    def is_null(self)->bool:
        ''' See if the instance can be used. '''
        if self.name == None or self.data == None:
            return True
        return isinstance(self.name, str) and isinstance(self.data, dict)


if __name__ == '__main__':
    # Core test cases - rest elsewhere.
    sut = NamedDict()
    if sut != sut:
        print("Error 10000")
    elif not NamedDict.Create(None, None).is_null():
        print("Error 10010")
    elif not NamedDict.Create('zoom', None).is_null():
        print("Error 10020")
    elif not NamedDict.Create('zoom', dict()).is_null():
        print("Error 10030")
    else:
        print("Testing Success.")
