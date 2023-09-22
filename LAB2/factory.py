import json
import xml.etree.ElementTree as ET
from player import Player
import player_pb2 as protblog_pb2



class PlayerFactory:
    def to_json(self, players):
        returned_json = []
        for player in players:
            new_player = {
                "nickname": player.nickname,
                "email": player.email,
                "date_of_birth": player.date_of_birth.strftime("%Y-%m-%d"),
                "xp": player.xp,
                "class": player.cls
            }
            returned_json.append(new_player)
        return returned_json

    def from_json(self, list_of_dict):
        players = []
        for dict in list_of_dict:
            new_player = Player(dict['nickname'], dict['email'], dict['date_of_birth'], int(
                dict['xp']), dict['class'])
            players.append(new_player)
        return players


    def from_xml(self, xml_string):
        root = ET.fromstring(xml_string)

        players = []

        for player_elem in root.findall("player"):
            nickname = player_elem.find("nickname").text
            email = player_elem.find("email").text
            date_of_birth = player_elem.find("date_of_birth").text
            xp = int(player_elem.find("xp").text)
            cls = player_elem.find("class").text

            player = Player(nickname, email, date_of_birth, xp, cls)
            players.append(player)

        return players

    def to_xml(self, list_of_players):

        data = ET.Element("data")


        for player in list_of_players:
            player_elem = ET.SubElement(data, "player")

            nickname = ET.SubElement(player_elem, "nickname")
            nickname.text = player.nickname

            email = ET.SubElement(player_elem, "email")
            email.text = player.email

            date_of_birth = ET.SubElement(player_elem, "date_of_birth")
            date_of_birth.text = player.date_of_birth.strftime("%Y-%m-%d")

            xp = ET.SubElement(player_elem, "xp")
            xp.text = str(player.xp)

            cls = ET.SubElement(player_elem, "class")
            cls.text = player.cls


        return ET.tostring(data, encoding="unicode", method="xml")

    def from_protobuf(self, binary):
        players_list_proto = protblog_pb2.PlayersList()
        players_list_proto.ParseFromString(binary)

        players = [Player(
            player_proto.nickname,
            player_proto.email,
            player_proto.date_of_birth,
            player_proto.xp,
            protblog_pb2.Class.Name(player_proto.cls)
        ) for player_proto in players_list_proto.player]

        return players

    def to_protobuf(self, list_of_players):
        players_list_proto = protblog_pb2.PlayersList()

        for player in list_of_players:
            player_proto = players_list_proto.player.add()
            player_proto.nickname = player.nickname
            player_proto.email = player.email
            player_proto.date_of_birth = player.date_of_birth.strftime("%Y-%m-%d")
            player_proto.xp = player.xp
            player_proto.cls = getattr(protblog_pb2.Class, player.cls)

        return players_list_proto.SerializeToString()

