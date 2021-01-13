from mycroft import MycroftSkill, intent_file_handler


class Knx(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('knx.intent')
    def handle_knx(self, message):
        self.speak_dialog('knx')


def create_skill():
    return Knx()

