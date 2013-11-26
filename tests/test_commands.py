from StringIO import StringIO
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.protocol import ClientFactory
from MQTT import  MQTTClient


class MQTTClientFactory(ClientFactory):
    username = "testuser"
    password = "testpwd"

    def buildProtocol(self, addr):
        return MQTTClient(username=self.username, password=self.password)

class CommandsTestCase(unittest.TestCase):
    def setUp(self):
        factory = MQTTClientFactory()
        self.proto = factory.buildProtocol(('127.0.0.1', 0))
        self.tr = proto_helpers.StringTransport()
        self.proto.makeConnection(self.tr)

    def _make_fixed_header(self, command, dup, qos, retain, remainning_length):
        header = bytearray()
        header.append(command << 4 | dup << 3 | qos << 1 | retain)
        header.extend(remainning_length)
        return header

    def _make_variable_header_connect(self,
                                      protocol_name,
                                      version,
                                      user_name_flag,
                                      password_flag,
                                      will_retain,
                                      will_qos,
                                      will_flag,
                                      clean_session,
                                      keep_alive_timer):
        header = bytearray()
        header.extend(self.proto._encodeString(protocol_name))
        header.append(version)

        header.append(user_name_flag << 7 |
                      password_flag << 6 |
                      will_retain << 5 |
                      will_qos << 4 |
                      will_flag << 2 |
                      clean_session << 1 |
                      0)
        header.extend(self.proto._encodeValue(keep_alive_timer / 1000))
        return header

    def _make_payload_connect(self,
                              client_id,
                              will_topic,
                              will_message,
                              user_name,
                              password):
        payload = bytearray()

        if client_id:
            payload.extend(self.proto._encodeString(client_id))

        if will_message and will_topic:
            payload.extend(self.proto._encodeString(will_topic))
            payload.extend(self.proto._encodeString(will_message))

        if user_name and password:
            payload.extend(self.proto._encodeString(user_name))
            payload.extend(self.proto._encodeString(password))

        return payload

    def test_connect(self):
        """
            test connect command
        """

        """ when default parameters """

        variable_header = self._make_variable_header_connect("MQIsdp", 3, 1, 1, 0, 0, 0, 1, 3000)
        payload = self._make_payload_connect(self.proto.clientId, None, None, "testuser", "testpwd")
        fixed_header = self._make_fixed_header(0x01, 0, 0, 0, self.proto._encodeLength(len(variable_header) + len(payload)))

        st = StringIO()
        st.write(fixed_header)
        st.write(variable_header)
        st.write(payload)
        self.assertEqual(self.proto.transport.value(), "".join(
            map(lambda x: str(x), [fixed_header, variable_header, payload])))
