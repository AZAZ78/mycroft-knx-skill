#Import mycroft integration
from adapt.intent import IntentBuilder
from mycroft.skills.core import FallbackSkill
from mycroft.util.format import nice_number
from mycroft import MycroftSkill, intent_file_handler, intent_handler
from mycroft.util.log import getLogger

#Import yaml reader for configuration
import yaml

#Import pknx for communication to EIBNet/IP
from knxip.ip import KNXIPTunnel
from knxip.conversion import float_to_knx2, knx2_to_float, \
    knx_to_time, time_to_knx, knx_to_date, date_to_knx, datetime_to_knx,\
    knx_to_datetime
from knxip.core import KNXException, parse_group_address

__author__ = 'azaz78'

class KnxSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        super().__init__(name="KnxSkill")
        self._knx_tunnel = None

    def _setup(self, force=False):
        self.log.debug ("setup skill (force: {})".format(force))
        if self.settings is not None and (force or self._knx_tunnel is None):
            ip = self.settings.get('host')
            portnum = self.settings.get('portnum')

            # Check if user filled host and portnum
            if ip is None:
                self.log.error ("host is not defined")
                self.speak_dialog('knx.error.setup', data={
                              "field": "host"})
                return

            try:
                port = int(portnum)
            except:
                # String might be some rubbish (like '')
                self.log.error ("portnum is not defined or invalid")
                self.speak_dialog('knx.error.setup', data={
                              "field": "portnum"})
                return

            self.log.info ("create new tunnel to {}:{}".format(ip, port))
            self._knx_tunnel = KNXIPTunnel(ip, port)

            self._light_entities = yaml.safe_load(self.settings.get('light'))
            self._plug_entities = yaml.safe_load(self.settings.get('plug'))
            self._blind_entities = yaml.safe_load(self.settings.get('blind'))
            self._actions = yaml.safe_load(self.settings.get('actions'))

    def initialize(self):
        self.language = self.config_core.get('lang')
        #self.load_vocab_files(join(dirname(__file__), 'vocab', self.lang))

        # Check and then monitor for credential changes
        self.settings_change_callback = self.on_websettings_changed
        self._setup()
        
    def on_websettings_changed(self):
        # Force a setting refresh after the websettings changed
        # Otherwise new settings will not be regarded
        self._setup(True)

    @intent_handler(IntentBuilder("LightIntent")
                              .require("knx.light")
                              .require("knx.action"))
    def handle_knx_light(self, message):
        self.log.info ("Handle light intent")
        entities = self._light_entities
        actions = self._actions
        utterance = message.data.get('utterance')
        self.log.info ("Utterance: {}".format(utterance))
        target = self._get_target(utterance, entities)
        value = self._get_value(utterance, actions)
        if self._send_value(target, value) is True:
           self.speak_dialog('knx.success')
        else:
           self.speak_dialog('knx.error')

    def _send_value(self, target, value):
        self.log.info ("Send {} to {}".format(value, target))
        if target is None:
           self.log.warning ("No target found")
           self.speak_dialog('knx.error')
           return False
        if value is None:
           self.log.warning ("No action found")
           self.speak_dialog('knx.error')
           return False
        tunnel = self._knx_tunnel
        try:
           tunnel.connect()
           tunnel.group_write(parse_group_address(target), [value])
           tunnel.disconnect()
        except:
           self.log.warning ("Error sending data")
           return False
        return True

    def _get_target(self, text, entities):
        for key, target in entities.items():
            if key in text:
                if isinstance(target, dict):
                    return self._get_target (text, target)
                else:            
                    return target
        return None

    def _get_value(self, text, actions):
        for key, value in actions.items():
            if key in text:
                return int(value)
        return None
        

def create_skill():
    return KnxSkill()

