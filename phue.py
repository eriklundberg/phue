#!/usr/bin/python

import urllib2
import httplib
import json
import os

# phue by Nathanaël Lécaudé - A Philips Hue Python library
# https://github.com/studioimaginaire/phue
# Original protocol hacking by rsmck : http://rsmck.co.uk/hue

class Light(object):
    def __init__(self, bridge, light_id):
        self.bridge = bridge
        self.light_id = light_id
        
        self._name = None
        self._on = None
        self._brightness = None
        self._hue = None
        self._saturation = None
        self._xy = None
        self._colortemp = None
        self._alert = None
       
    @property
    def name(self):
        self._name = self.bridge.get_state(self.light_id, 'name')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self.bridge.set_state(self.light_id, 'name', self._name)
        
        self.bridge.lights_by_name[self.name] = self 
        del self.bridge.lights_by_name[old_name]

    @property
    def on(self):
        self._on = self.bridge.get_state(self.light_id, 'on')
        return self._on

    @on.setter
    def on(self, value):
        self._on = value
        self.bridge.set_state(self.light_id, 'on', self._on)

    @property
    def brightness(self):
        self._brightness = self.bridge.get_state(self.light_id, 'bri')
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = value
        self.bridge.set_state(self.light_id, 'bri', self._brightness)
    
    @property
    def hue(self):
        self._hue = self.bridge.get_state(self.light_id, 'hue')
        return self._hue

    @hue.setter
    def hue(self, value):
        self._hue = value
        self.bridge.set_state(self.light_id, 'hue', self._hue)

    @property
    def saturation(self):
        self._saturation = self.bridge.get_state(self.light_id, 'sat')
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._saturation = value
        self.bridge.set_state(self.light_id, 'sat', self._saturation)

    @property
    def xy(self):
        self._xy = self.bridge.get_state(self.light_id, 'xy')
        return self._xy

    @xy.setter
    def xy(self, value):
        self._xy = value
        self.bridge.set_state(self.light_id, 'xy', self._xy)

    @property
    def colortemp(self):
        self._colortemp = self.bridge.get_state(self.light_id, 'ct')
        return self._colortemp

    @colortemp.setter
    def colortemp(self, value):
        self._colortemp = value
        self.bridge.set_state(self.light_id, 'ct', self._colortemp)

    @property
    def alert(self):
        self._colortemp = self.bridge.get_state(self.light_id, 'alert')
        return self._alert

    @alert.setter
    def alert(self, value):
        self._alert = value
        self.bridge.set_state(self.light_id, 'alert', self._alert)

class Bridge(object):
    def __init__(self, bridge_ip, username = None):
        self.config_file = os.path.join(os.getenv("HOME"),'.python_hue')
        self.bridge_ip = bridge_ip
        self.username = username
        self.lights_by_id = {}
        self.lights_by_name = {}
        self._name = None

        self.minutes = 600
        self.seconds = 10
        
        self.connect()
    
    @property
    def name(self):
        self._name = self.request('GET', '/api/' + self.username + '/config')['name']
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
        data = {'name' : self._name}
        self.request('PUT', '/api/' + self.username + '/config', json.dumps(data))

    def request(self,  mode = 'GET', address = None, data = None):
        connection = httplib.HTTPConnection(self.bridge_ip)
        if mode == 'GET':
            connection.request(mode, address)
        if mode == 'PUT' or mode == 'POST':
            connection.request(mode, address, data)

        result = connection.getresponse()
        connection.close()
        return json.loads(result.read())
    
    def register_app(self):
        registration_request = {"username": "python_hue", "devicetype": "python_hue"}
        data = json.dumps(registration_request)
        response = self.request('POST', '/api', data)
        for line in response:
            for key in line:
                if 'success' in key:
                    with open(self.config_file, 'w') as f:
                        print 'Writing configuration file to ' + self.config_file
                        f.write(json.dumps({self.bridge_ip : line['success']}))
                        print 'Reconnecting to the bridge'
                    self.connect()
                if 'error' in key:
                    if line['error']['type'] == 101:
                        print 'Please press button on bridge to register application and call connect() method'
                    if line['error']['type'] == 7:
                        print 'Unknown username'
    def connect(self):
        print 'Attempting to connect to the bridge'
        if self.username == None:
            try:
                with open(self.config_file) as f:
                    self.username =  json.loads(f.read())[self.bridge_ip]['username']
                    print 'Using username: ' + self.username
        
            except Exception as e:
                print 'Error opening config file, will attempt bridge registration'
                self.register_app()
        else:
            print 'Using username: ' + self.username

    #Returns a dictionary containing the lights, either by name or id (use 'id' or 'name' as the mode)
    def get_lights(self, mode):
        if self.lights_by_id == {}:
            lights = self.request('GET', '/api/' + self.username + '/lights/')
            for light in lights:
                self.lights_by_id[int(light)] = Light(self, int(light))
                self.lights_by_name[lights[light]['name']] = self.lights_by_id[int(light)]
        if mode == 'id':
            return self.lights_by_id
        if mode == 'name':
            return self.lights_by_name
        if mode == 'list':
            return [ self.lights_by_id[x] for x in range(1, len(self.lights_by_id) + 1) ]

    
    # Return the dictionary of the whole bridge
    def get_info(self):
        return self.request('GET', '/api/' + self.username)

    # Gets state by light_id and parameter
    def get_state(self, light_id, parameter):
        state = self.request('GET', '/api/' + self.username + '/lights/' + str(light_id))
        if parameter == 'name':
            return state[parameter]
        else:
            return state['state'][parameter]


    # light_id can be a single lamp or an array or lamps
    # parameters: 'on' : True|False , 'bri' : 0-254, 'sat' : 0-254, 'ct': 154-500
    def set_state(self, light_id, parameter, value = None):
        if type(parameter) == dict:
            data = parameter
        else:
            data = {parameter : value}
        light_id_array = light_id
        if type(light_id) == int:
            light_id_array = [light_id]
        for light in light_id_array:
            if parameter  == 'name':
                return self.request('PUT', '/api/' + self.username + '/lights/'+ str(light_id), json.dumps(data))
            else:
                return self.request('PUT', '/api/' + self.username + '/lights/'+ str(light) + '/state', json.dumps(data))


