#Import mycroft integration
from adapt.intent import IntentBuilder
from adapt.engine import IntentDeterminationEngine
from mycroft.skills.core import FallbackSkill
from mycroft.util.format import nice_number
from mycroft import MycroftSkill, intent_file_handler, intent_handler
from mycroft.util.log import getLogger

#Import yaml reader for configuration
import yaml
from dataclasses import dataclass
 
#Import pknx for communication to EIBNet/IP
from knxip.ip import KNXIPTunnel
from knxip.conversion import float_to_knx2, knx2_to_float, \
    knx_to_time, time_to_knx, knx_to_date, date_to_knx, datetime_to_knx,\
    knx_to_datetime
from knxip.core import KNXException, parse_group_address

__author__ = 'azaz78'

@dataclass
class KnxValue:
    value: int
    valuetype: str = None

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
                return False

            try:
                port = int(portnum)
            except:
                self.log.error ("portnum is not defined or invalid")
                self.speak_dialog('knx.error.setup', data={
                              "field": "portnum"})
                return False

            self.log.info ("create new tunnel to {}:{}".format(ip, port))
            self._knx_tunnel = KNXIPTunnel(ip, port)

            self._light_entities = yaml.safe_load(self.settings.get('light'))
            self._plug_entities = yaml.safe_load(self.settings.get('plug'))
            self._blind_entities = yaml.safe_load(self.settings.get('blind'))
            self._special_entities = yaml.safe_load(self.settings.get('special'))
            self._actions = yaml.safe_load(self.settings.get('actions'))
            
            return True

    def _register_special_intent(self, entities):
        if entities is None:
            return

        for keys, value in entities.items():
            for key in keys.split("|"):
                if key != "Default":
                    self.register_vocabulary(key, "knx.special")

        special_intent = IntentBuilder("SpecialIntent")\
            .require("knx.special")\
            .require("knx.action")\
            .build()

        self.register_intent(special_intent, self.handle_knx_special)

    def initialize(self):
        self.language = self.config_core.get('lang')
        # Check and then monitor for credential changes
        self.settings_change_callback = self.on_websettings_changed
        if self._setup() is True
            # Trigger for specials is only updated after restart, but no glue how to update it
            self._register_special_intent(self._special_entities)
        
    def on_websettings_changed(self):
        # Force a setting refresh after the websettings changed
        # Otherwise new settings will not be regarded
        self._setup(True)

    @intent_handler(IntentBuilder("LightIntent")
                              .require("knx.light")
                              .require("knx.action"))
    def handle_knx_light(self, message):
        self.log.info ("Handle light intent")
        utterance = message.data.get('utterance')
        self.log.info ("Utterance: {}".format(utterance))
        self._handle_knx(utterance, self._light_entities, self._actions)

    @intent_handler(IntentBuilder("BlindIntent")
                              .require("knx.blind")
                              .require("knx.action"))
    def handle_knx_blind(self, message):
        self.log.info ("Handle blind intent")
        utterance = message.data.get('utterance')
        self.log.info ("Utterance: {}".format(utterance))
        self._handle_knx(utterance, self._blind_entities, self._actions)

    @intent_handler(IntentBuilder("PlugIntent")
                              .require("knx.plug")
                              .require("knx.action"))
    def handle_knx_plug(self, message):
        self.log.info ("Handle plug intent")
        utterance = message.data.get('utterance')
        self.log.info ("Utterance: {}".format(utterance))
        self._handle_knx(utterance, self._plug_entities, self._actions)

    def handle_knx_special(self, message):
        self.log.info ("Handle special intent")
        utterance = message.data.get('utterance')
        self.log.info ("Utterance: {}".format(utterance))
        self._handle_knx(utterance, self._special_entities, self._actions)

    def _handle_knx(self, utterance, entities, actions):
        target = self._get_target(utterance, entities)
        value = self._get_value(utterance, actions)
        if self._send_value(target, value) is True:
           self.speak_dialog('knx.success')
        else:
           self.speak_dialog('knx.error')

    def _send_value(self, target, value):
        ret = False
        self.log.info ("Send {} to {}".format(value, target))
        if target is None:
           self.log.warning ("No target found")
           return False
        if value is None:
           self.log.warning ("No action found")
           return False
        tunnel = self._knx_tunnel
        try:
           tunnel.connect()
           if value.valuetype == None:
              tunnel.group_write(parse_group_address(target), [value.value])
              ret = True
           elif value.valuetype == "num":
              tunnel.group_write(parse_group_address(target), [value.value], 1)
              ret = True
           else:
              self.log.warning ("No valid type found")
        except ex:
           self.log.warning ("Error sending data: {}".format(ex))
        tunnel.disconnect()
        return ret

    def _get_target(self, text, entities):
        default = None
        for keys, target in entities.items():
            for key in keys.split("|"):
                if key in text:
                    self.log.debug ("Found {} in {}".format(key, text))
                    if isinstance(target, dict):
                        return self._get_target (text, target)
                    else:
                        return target
                if key == 'default':
                    default = target
        if default is not None:
            self.log.debug ("Found no key but default")
            if isinstance(default, dict):
                return self._get_target (text, default)
            else:
                return default
        return None

    def _get_value(self, text, actions):
        for key, value in actions.items():
            if key in text:
                val = value.split("|")
                count = len(val)
                if count == 1:
                    return KnxValue(int(val[0]))
                elif count == 2:
                    return KnxValue(int(val[0]), val[1])
        return None

def create_skill():
    return KnxSkill()

