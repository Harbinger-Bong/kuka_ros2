# Copyright 2019 Norwegian University of Science and Technology.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Union
from kuka_eki.krl import RobotCommand, RobotState
from kuka_eki.tcp_client import TcpClient
from kuka_eki.krl import Axis, Pos, CommandType


class EkiMotionClient:
    MOTION_PORT: int = 54600

    def __init__(self, ip_address: str) -> None:
        self._tcp_client = TcpClient((ip_address, self.MOTION_PORT))

    def connect(self) -> None:
        self._tcp_client.connect()

    def ptp(self, target: Union[Axis, Pos], max_velocity_scaling=1.0, approx: int = 0) -> None:
        command_type: CommandType
        if isinstance(target, Axis):
            command_type = CommandType.PTP_AXIS
        elif isinstance(target, Pos):
            command_type = CommandType.PTP_CART
        else:
            raise TypeError("Expected argument of type Axis or Pos")
        command: RobotCommand = RobotCommand(command_type, target, max_velocity_scaling, approx)
        self._tcp_client.sendall(command.to_xml())

    def ptp_rel(self, target: Axis, max_velocity_scaling: float = 1.0, approx: int = 0) -> None:
        if not isinstance(target, Axis):
            raise TypeError("Expected argument of Axis")
        command: RobotCommand = RobotCommand(
            CommandType.PTP_AXIS_REL, target, max_velocity_scaling, approx
        )
        self._tcp_client.sendall(command.to_xml())

    def lin(self, target: Pos, max_velocity_scaling=1.0, approx: int = 0) -> None:
        if not isinstance(target, Pos):
            raise TypeError("Expected argument of Pos")
        command: RobotCommand = RobotCommand(
            CommandType.LIN_CART, target, max_velocity_scaling, approx
        )
        self._tcp_client.sendall(command.to_xml())

    def lin_rel(self, target: Pos, max_velocity_scaling=1.0, approx: int = 0) -> None:
        if not isinstance(target, Pos):
            raise TypeError("Expected argument of Pos")
        command: RobotCommand = RobotCommand(
            CommandType.LIN_CART_REL, target, max_velocity_scaling, approx
        )
        self._tcp_client.sendall(command.to_xml())


class EkiStateClient:
    STATE_PORT: int = 54601

    def __init__(self, ip_address: str) -> None:
        self._tcp_client: TcpClient = TcpClient((ip_address, self.STATE_PORT))
        self._buf: bytes = b""

    def connect(self) -> None:
        self._tcp_client.connect()

    def state(self) -> RobotState:
        while True:
            start = self._buf.find(b"<RobotState")
            if start == -1:
                # no doc start in buffer yet -- drop any leading garbage
                self._buf = b""
            else:
                end = self._buf.find(b"</RobotState>", start)
                if end != -1:
                    end += len(b"</RobotState>")
                    doc = self._buf[start:end]
                    self._buf = self._buf[end:]  # keep anything after, for the next call
                    return RobotState.from_xml(doc)
                else:
                    self._buf = self._buf[start:]  # keep partial doc, wait for more

            chunk = self._tcp_client.recv(4096)
            if not chunk:
                raise ConnectionError("EKI state socket closed by peer")
            self._buf += chunk

            
