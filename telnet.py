# ----------------------------------------------------------------------------------------------------------------------------------------------
# LNHR DAC II Telnet driver (Python)
# v0.1.0
# Copyright (c) Basel Precision Instruments GmbH (2024)
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the 
# Free Software Foundation, either version 3 of the License, or any later version. This program is distributed in the hope that it will be 
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details. You should have received a copy of the GNU General Public License along with this program.  
# If not, see <https://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------------------------------------------------------------------------

# imports --------------------------------------------------------------

from typing import Optional
from time import sleep
import telnetlib

# class ----------------------------------------------------------------

class LNHRDAC:
    """
    This class provides simple methods to communicate with the LNHR DAC 
    II through Telnet. Commands for controlling the LNHR DAC II can be 
    found in the "Programmers Manual. Handshaking, timings and package 
    terminations as recommended in the manual are implemented. Any 
    command can be sent to the LNHR DAC II without "CR" and/or "LF" at 
    the end. Delays inbetween two commands are not necessary.
    """
    #-------------------------------------------------

    def __init__(self, 
                 ip: str, 
                 port: int, 
                 name: Optional[str] = None
                 ) -> None:
        """
        Constructor. This class provides simple methods to communicate 
        with the LNHR DAC II through Telnet. Commands for controlling the 
        LNHR DAC II can be found in the "Programmers Manual. Handshaking, 
        timings and package terminations as recommended in the manual are 
        implemented. Any command can be sent to the LNHR DAC II without 
        "CR" and/or "LF" at the end. Delays inbetween two commands are 
        not necessary.

        Parameters:
        ip: IP address of this DAC
        port: used Telnet Port of this DAC
        name (optional): name of this DAC
        """

        self.ip = ip
        self.port = port
        self.name = name
        
        self.connected = False
        self.telnet = None
        self._std_com_delay = 0.003
        self._ctrl_cmd_delay = 0.2
        self._mem_wrt_delay = 0.3

        try:
            self._connect_to_DAC()
            status = self.send_query("all s?")
            if type(self.name) == type(None):
                name = ""
            else:
                name = f"\"{self.name}\", "
            print(f"Connected to DAC ({name}{self.ip}) successfully. " 
                  + "The current status of all channels is shown below " 
                  + "(channel 1; channel 2; ... ):")
            print(status)
            self._disconnect_from_DAC()
        except ConnectionError:
            print(f"Establishing a connection to {self.ip} failed.")

    #-------------------------------------------------

    def _connect_to_DAC(self) -> None:
        """
        Connects to LNHR DAC using Telnet.
        Raises a ConnectionError if connecting fails
        """

        # connect to DAC using Telnet
        if not self.connected: 
            try: 
                self.telnet = telnetlib.Telnet(self.ip, self.port)
                self.telnet.timeout = 3
                self.connected = True

            except TimeoutError or ConnectionRefusedError: 
                raise ConnectionError("connecting to the LNHR DAC II" 
                                      + "failed")

    #-------------------------------------------------

    def _disconnect_from_DAC(self, 
                             hold_connection: bool = False
                             ) -> None:
        """
        Disconnects from LNHR DAC using Telnet.

        Parameters:
        hold_connection: If True, the Telnet connection is not terminated 
            after sending a command. Should be True in a long series of 
            commands. Might create issues if code crashes while connected
        """
        # disconnect from DAC using Telnet
        if not hold_connection:
            self.telnet.close()
            self.connected = False
            sleep(self._std_com_delay)

    #-------------------------------------------------

    def send_command(self, 
                     command: str, 
                     hold_connection: bool = False
                     ) -> None:
        """
        This method sends a Telnet command to the LNHR DAC II. Returns 
        True if successful, False if not successful. Only works for 
        commands that return an integer Error Code (write-commands). 
        For query commands (read-commands) use send_query().
        Raises a KeyError if the command is invalid
        
        Parameters:
        command: DAC command according to "programmers manual", without 
            "CR" and "LF", does not contain "?" 
        hold_connection: If True, the Telnet connection is not 
            terminated after sending a command. Should be True in a long 
            series of commands. Might create issues if code crashes while 
            connected
        """        

        # connect to DAC using Telnet
        self._connect_to_DAC()

        # query command is not allowed
        if "?" in command: 
            self._disconnect_from_DAC(hold_connection)
            raise KeyError("Query commands are not allowed with "
                           + "send_command(), use send_query() instead")
        else: 
            # send telnet command to DAC
            self.telnet.write(command.encode("ascii") + b"\r\n") 

        # read answer, until <LF> or 3s passed
        ans = self.telnet.read_until(b"\n", 3) 

        # in case of a control command, wait 200ms to allow for 
        # internal synchronisation
        # wait additional 0.3s in case of memory write command
        if command[0] == "c" or command[0] == "C": 
            sleep(self._ctrl_cmd_delay)
            if "write" in command: 
                sleep(self._mem_wrt_delay)

        # check for successful acknowledge (handshaking)
        if ans == b"0\r\n": 
            self._disconnect_from_DAC(hold_connection)
            return
        else:
            self._disconnect_from_DAC(hold_connection)
            raise KeyError("Error occured: send_command"
                            + f"(\"{command}\") could not be "
                            + "processed by LNHR DAC, "
                            + f"DAC answered: {ans}")

    #-------------------------------------------------

    def send_query(self, 
                   query: str, 
                   hold_connection: bool = False
                   ) -> str:
        """
        This method sends a Telnet query command to the LNHR DAC II and 
        returns the answer. Raises a KeyError if the command is invalid

        Parameters:
        query: DAC command according to "programmers manual", without 
            "CR" and "LF", always ends with "?" 
        hold_connection (optional): If True, the Telnet connection is not 
            terminated after sending a command. Should be True in a long 
            series of commands. Might create issues if code crashes
        
        Returns:
        (string): Returns answer from device or "?" if query was 
            not successful
        """

        # connect to DAC using Telnet
        self._connect_to_DAC()

        # non query command is not allowed
        if "?" not in query: 
            self._disconnect_from_DAC(hold_connection)
            raise KeyError("non-query commands are not allowed with "
                           + "send_query(), use send_command() instead")
        else: 
            # send telnet command to DAC
            self.telnet.write(query.encode("ascii") + b"\r\n") 

        # read answer, until <LF> or 3s passed
        ans = self.telnet.read_until(b"\n", 3) 

        # in case of a control command, wait 200ms to allow for 
        # internal synchronisation
        if query[0] == "c" or query[0] == "C": 
            sleep(self._ctrl_cmd_delay)

        # check for successful acknowledge (handshaking)
        if b"?" not in ans: 
            self._disconnect_from_DAC(hold_connection)
            return ans.decode("ascii")
        else:
            self._disconnect_from_DAC(hold_connection)
            raise KeyError(f"Error occured: \"{query}\" "
                 + "could not be processed by LNHR DAC,"
                 + f"DAC answered: {ans}")
   
    #-------------------------------------------------
        
    def expect_query_answer(self, 
                            query: str, 
                            answer: str, 
                            hold_connection: bool = False
                            ) -> bool:
        """
        This method sends a Telnet query command to the LNHR DAC II and 
        expects a certain answer. Raises a KeyError if the command is 
        invalid
 
        Parameters: 
        query: DAC command according to "programmers manual", without 
            "CR" and "LF", always ends with "?" 
        answer: Expected exact answer according to "programmers manual", 
            without "CR" and "LF"
        holdconnection (optional): If True, the Telnet connection is not 
            terminated after sending a command. Should be True in a long 
            series of commands. Might create issues if code crashes

        Returns:
        (bool): returns True if the expected answer is exactly matched by 
            the received answer, returns False otherwise
        """
        
        # connect to DAC using Telnet
        self._connect_to_DAC()

        # command is not allowed
        if "?" not in query: 
            self._disconnect_from_DAC(hold_connection)
            raise KeyError("non-query commands are not allowed with "
                 +" expect_query_answer(), use send_command() instead")
        else: 
            # send telnet command to DAC
            self.telnet.write(query.encode("ascii") + b"\r\n") 

        # read answer, until <LF> or 3s passed
        ans = self.telnet.read_until(b"\r\n", 3) 

        # in case of a control command, wait 200ms to allow for 
        # internal synchronisation
        if query[0] == "c" or query[0] == "C": 
            sleep(self._ctrl_cmd_delay)

        # check for successful acknowledge and expected answer 
        # (handshaking)
        if b"?" in ans:
            self._disconnect_from_DAC(hold_connection)
            raise KeyError(f"Error occured: \"{query}\" "
                 + "could not be processed by LNHR DAC,"
                 + f"DAC answered: {ans}")
        elif ans.decode("ascii") == answer + "\r\n": 
            self._disconnect_from_DAC(hold_connection)
            return True
        else:
            return False        
        
# main -----------------------------------------------------------------

if __name__ == "__main__":

    # create DAC object
    DAC = LNHRDAC("192.168.0.5", 23) 
    sleep(1)
    # The following script Tests the main features of this module and 
    # partly their correct funtion

    # send command
    # correct use of send_command()
    DAC.send_command("all off") 

    # provoke KeyError (wrong method)
    try:
        DAC.send_command("all s?") 
    except KeyError as ex:
        print(ex)

    # provoke KeyError (invalid command)
    try:
        DAC.send_command("al off") 
    except KeyError as ex:
        print(ex)

    # send query
    # correct use of send_query()
    DAC.send_query("all s?") 
    # provoke KeyError (wrong method)
    try:
        DAC.send_query("all off")
    except KeyError as ex:
        print(ex)
    # provoke KeyError (invalid command)
    try:
        DAC.send_query("al s?") 
    except KeyError as ex:
        print(ex)

    # expect query answer
    # correct use of expect_query_answer()
    DAC.expect_query_answer("1 s?", "OFF") 
    # provoke KeyError (wrong method)
    try:
        DAC.expect_query_answer("all off", "ON") 
    except KeyError as ex:
        print(ex)
    # provoke KeyError (invalid command)
    try:
        DAC.expect_query_answer("al s?", "ON") 
    except KeyError as ex:
        print(ex)