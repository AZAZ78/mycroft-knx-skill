# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/laptop-house.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/> KNX
Smart home integration of KNX via EIBNnet/IP

## About
This skill let you control your smart home. it uses the pknx library from the the open-homeautomation project (https://github.com/open-homeautomation/pknx). control your lights, blinds and more ... simply with your voice!

## Examples
* "Turn the light on in the living room"
* "Turn off the light in the kitchen"
* "Shut down blinds for watching TV"

## Credits
Alexander Zeh (@AZAZ78)

## Category
**IoT**
Daily
Productivity

## Tags
#Knx
#Eib
#Smart home

## Installation and Configuration
The original pknx implementation has an issue with clean closing of tunnels. It should work with the modified version at https://github.com/AZAZ78/pknx/blob/master/dist/knxip-0.5.tar.gz
Installation of pknx:
- Download knxip-0.5.tar.gz: wget https://github.com/AZAZ78/pknx/blob/master/dist/knxip-0.5.tar.gz
- Install with pip: pip install knxip-0.5.tar.gz

Installation of mycroft-knx-skill
- mycroft-msm install https://github.com/AZAZ78/mycroft-knx-skill.git

Configure skill in https://account.mycroft.ai/skills

## Usage
tbd

## TODO
tbd
