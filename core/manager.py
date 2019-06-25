from core import configuration
from data_model import ua_manager
from xml.etree import ElementTree as ETree
import time
import struct
import logging
import gc


class Manager:

    def __init__(self):
        self.start_time = time.time()*1000
        self.config_dictionary = dict()

        # attributes responsible for the ua integration
        self.ua_integration = False
        self.ua_url = 'opc.tcp://localhost:4048'
        self.manager_ua = None

    def get_config(self, config_id):
        fb_element = None
        try:
            fb_element = self.config_dictionary[config_id]
        except KeyError as error:
            logging.error('can not find that configuration (4DIAC resource)')
            logging.error(error)

        return fb_element

    def set_config(self, config_id, config_element):
        self.config_dictionary[config_id] = config_element

    def parse_general(self, xml_data):
        # Parses the xml
        element = ETree.fromstring(xml_data)
        action = element.attrib['Action']
        request_id = element.attrib['ID']
        xml = None

        if action == 'CREATE':
            # Iterate over the list of children
            for child in element:
                # Create configuration (function block)
                if child.tag == 'FB':
                    conf_name = child.attrib['Name']
                    conf_type = child.attrib['Type']
                    # Checks if not exists the configuration
                    if conf_name not in self.config_dictionary:
                        # Creates the configuration
                        config = configuration.Configuration(conf_name, conf_type)
                        self.set_config(conf_name, config)
                        # check the options for ua_integration
                        if self.ua_integration:
                            # add try catch OSError: [Errno 98] Address already in use
                            # creates the new ua_manager
                            self.manager_ua = ua_manager.UaManager(conf_name, self.ua_url, config)

        elif action == 'QUERY':
            pass

        elif action == 'READ':
            # Iterate over the list of children
            for child in element:
                # Reads values from a watch
                if child.tag == 'Watches':
                    xml = ETree.Element('Watches')
                    # Gets all the watches from all the xml_data
                    for config_id, config in self.config_dictionary.items():
                        resource_xml, resource_len = config.read_watches(self.start_time)
                        # Appends only if has anything
                        if resource_len > 0:
                            xml.append(resource_xml)

                    resources_len = len(xml.findall('Resource'))
                    # If doesn't have any resource
                    if resources_len < 0:
                        xml = None

        elif action == 'KILL':
            # Iterate over the list of children
            for child in element:
                # Kill a configuration (could be a fb)
                if child.tag == 'FB':
                    fb_name = child.attrib['Name']
                    # Checks if exists the configuration
                    if fb_name in self.config_dictionary:
                        # Stops the configuration
                        config = self.get_config(fb_name)
                        config.stop_work()
                        # Release memory
                        gc.collect()
            # If we want to kill the device
            if len(element) == 0:
                pass

        elif action == 'DELETE':
            # Iterate over the list of children
            for child in element:
                # Deletes a configuration (could be a fb)
                if child.tag == 'FB':
                    conf_name = child.attrib['Name']
                    # Checks if exists the configuration
                    if conf_name in self.config_dictionary:
                        # Deletes the configuration
                        self.config_dictionary.pop(conf_name)
                        # Release memory
                        gc.collect()
            # check the options for ua_integration
            if self.ua_integration:
                # first stop the previous manager
                self.manager_ua.stop_ua()

        response = self.build_response(request_id, xml)
        return response

    def parse_configuration(self, xml_data, config_id):
        # Parses the xml
        element = ETree.fromstring(xml_data)
        action = element.attrib['Action']
        request_id = element.attrib['ID']
        xml = None

        if action == 'CREATE':
            # Iterate over the list of children
            for child in element:
                # Create function block
                if child.tag == 'FB':
                    fb_name = child.attrib['Name']
                    fb_type = child.attrib['Type']
                    fb, fb_xml = self.get_config(config_id).create_fb(fb_name, fb_type)
                    # check the options for ua_integration
                    if self.ua_integration:
                        # parses from fb
                        self.manager_ua.from_fb(fb, fb_xml)

                # Create connection
                elif child.tag == 'Connection':
                    connection_source = child.attrib['Source']
                    connection_destination = child.attrib['Destination']
                    self.get_config(config_id).create_connection(connection_source, connection_destination)

                # Create watch
                elif child.tag == 'Watch':
                    watch_source = child.attrib['Source']
                    watch_destination = child.attrib['Destination']
                    self.get_config(config_id).create_watch(watch_source, watch_destination)

        elif action == 'DELETE':
            # Iterate over the list of children
            for child in element:
                # Delete watch
                if child.tag == 'Watch':
                    watch_source = child.attrib['Source']
                    watch_destination = child.attrib['Destination']
                    self.get_config(config_id).delete_watch(watch_source, watch_destination)

        elif action == 'START':
            # Starts the configuration
            self.get_config(config_id).start_work()

        elif action == 'WRITE':
            # Iterate over the list of children
            for child in element:
                # Write a connection with value
                if child.tag == 'Connection':
                    connection_source = child.attrib['Source']
                    connection_destination = child.attrib['Destination']
                    self.get_config(config_id).write_connection(connection_source, connection_destination)

        response = self.build_response(request_id, xml)
        return response

    @staticmethod
    def build_response(request_id, xml_response):
        xml = ETree.Element('Response', {'ID': request_id})
        # Verifies if is a default response
        if xml_response is not None:
            xml.append(xml_response)

        response_xml = ETree.tostring(xml)
        hex_input = '{:04x}'.format(len(response_xml))
        second_byte = int(hex_input[0:2], 16)
        third_byte = int(hex_input[2:4], 16)
        response_len = struct.pack('BB', second_byte, third_byte)
        response_header = b''.join([b'\x50', response_len])

        response = b''.join([response_header, response_xml])
        return response

    def build_ua_manager(self, base_name, address, port, file_name):
        # creates the opc-ua manager
        config = configuration.Configuration(base_name, 'EMB_RES')
        self.set_config(base_name, config)
        self.ua_url = 'opc.tcp://{0}:{1}'.format(address, port)
        self.manager_ua = ua_manager.UaManager(base_name, self.ua_url, config)
        # parses the description file
        self.manager_ua.from_xml(file_name)
        # sets the option for ua_integration
        self.ua_integration = True
