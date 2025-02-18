# ----------------------------------------------------------------------------------------------------------------------------------------------
# LNHR DAC II Telnetlib3 driver (Python)
# v0.1.2
# Copyright (c) Basel Precision Instruments GmbH (2025)
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the 
# Free Software Foundation, either version 3 of the License, or any later version. This program is distributed in the hope that it will be 
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details. You should have received a copy of the GNU General Public License along with this program.  
# If not, see <https://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------------------------------------------------------------------------

# imports --------------------------------------------------------------
import asyncio
import telnetlib3
from typing import Optional



# class ----------------------------------------------------------------

class LNHRDAC:
#init------------------------------------------------------------------    
    def __init__(self, 
                     ip: str, 
                     port: int, 
                     name: Optional[str] = None
                     ) -> None:
            """
            Initializes the Telnet client for the device.
            """
            self.ip = ip
            self.port = port
            self.name = name if name else f"Device-{ip}"

            self.connected = False
            self.reader = None
            self.writer = None
            self._std_com_delay = 0.003
            self._ctrl_cmd_delay = 0.2
            self._mem_wrt_delay = 0.3

            self._multi_line_output_commands = ("?", "help?", "soft?", "hard?", "idn?", 
                                                "health?", "ip?", "serial?", "contact?")

#end-init------------------------------------------------------------------    

#connect------------------------------------------------------------------    
    async def connect(self) -> None:
        """
        Establishes a Telnet connection to the device.
        Returns True if successful, False otherwise.
        """
        if self.connected:
            return True  # Already connected
        
        try:
            self.reader, self.writer = await telnetlib3.open_connection(self.ip, self.port)
            print("i am here 1")
            self.connected = True
            print(f"[{self.name}] Connected to {self.ip}:{self.port}")
            print("i am here 2")
            return True
        
        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")
            self.connected = False
            return False
        
#end-connect------------------------------------------------------------------    
#disconnect------------------------------------------------------------------    
    async def disconnect(self, hold_connection: bool = False) -> None:
        """
        Closes the Telnet connection if `hold_connection` is False.
        """
        if not self.connected or hold_connection:
            return  # No need to disconnect

        try:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
                print(f"[{self.name}] Disconnected from {self.ip}:{self.port}")
        except Exception as e:
            print(f"[{self.name}] Error while disconnecting: {e}")
        finally:
            self.connected = False
            self.reader = None
            self.writer = None

#end-disconnect------------------------------------------------------------------    
#send_command------------------------------------------------------------------    
    async def send_command(self, 
                       command: str, 
                       hold_connection: bool = False
                       ) -> bool:
        """
        Sends a command to the Telnet device.
        Returns True if successful, raises KeyError on failure.
        """
        if "?" in command:
            raise KeyError("Query commands are not allowed with send_command(), "
                           "use send_query() instead.")
        
        if not self.connected:
            success = await self.connect()
            if not success:
                raise ConnectionError(f"[{self.name}] Failed to connect to {self.ip}")
        print("i am here 3")
        # Send command
        self.writer.write(command + "\n")
        await self.writer.drain()
        print("i am here 4")
        # Read response
        try:
        # 🔹 Read a fixed size instead of waiting for "\r\n"
            print("i am here lolol")
            ans = await asyncio.wait_for(self.reader.read(1024), timeout=5)
            print(f"[{self.name}] Device response: {ans.strip()}")
        except asyncio.TimeoutError:
            print(f"[{self.name}] Device did not respond in time. Retrying...")
      


        print("i am here 5")
        # Handle delays for specific commands
        if command[0].lower() in ("c", "C"):  
            await asyncio.sleep(self._ctrl_cmd_delay)

            if "write" in command.lower():
                await asyncio.sleep(self._mem_wrt_delay)

        if ans.strip() == "0":
            await self.disconnect(hold_connection)
            return True
        else:
            await self.disconnect(hold_connection)
            raise KeyError(f"Error: send_command(\"{command}\") failed. "
                           f"Device response: {ans.strip()}")
        
#end-send_command------------------------------------------------------------------
#send_query------------------------------------------------------------------------    
    async def send_query(self, 
                             query: str, 
                             hold_connection: bool = False
                             ) -> str:
        """
        Sends a query command and returns the response.
        Raises KeyError if the command is invalid.
        """
        if "?" not in query:
            raise KeyError("Non-query commands are not allowed with send_query(), "
                           "use send_command() instead.")

        if not self.connected:
            success = await self.connect()
            if not success:
                raise ConnectionError(f"[{self.name}] Failed to connect to {self.ip}")

        # Determine end of message for multi-line outputs
        query = query.strip().lower()
        eom = b"\r\r" if query in self._multi_line_output_commands else b"\r\n"

        self.writer.write(query + "\n")
        await self.writer.drain()

        ans = await self.reader.readuntil(eom)

        # Handle delays
        if query[0].lower() in ("c", "m", "x"):
            await asyncio.sleep(self._ctrl_cmd_delay)

        if b"?" not in ans or eom == b"\r\r":
            await self.disconnect(hold_connection)
            return ans.decode("ascii").strip()
        else:
            await self.disconnect(hold_connection)
            raise KeyError(f"Error: \"{query}\" failed. "
                           f"Device response: {ans.strip()}")
#end send_query--------------------------------------------------------------------------------------------------
#expect_query_answer-----------------------------------------------------------------------------------------

    async def expect_query_answer(self, 
                                  query: str, 
                                  answer: str, 
                                  hold_connection: bool = False
                                  ) -> bool:
        """
        Sends a query command and verifies if the response matches the expected answer.
        """
        if "?" not in query:
            raise KeyError("Non-query commands are not allowed with "
                           "expect_query_answer(), use send_command() instead.")

        if not self.connected:
            success = await self.connect()
            if not success:
                raise ConnectionError(f"[{self.name}] Failed to connect to {self.ip}")

        query = query.strip().lower()
        eom = b"\r\r" if query in self._multi_line_output_commands else b"\r\n"

        self.writer.write(query + "\n")
        await self.writer.drain()

        ans = await self.reader.readuntil("\r\n")

        if query[0].lower() in ("c", "m", "x"):
            await asyncio.sleep(self._ctrl_cmd_delay)

        if b"?" in ans or eom == b"\r\r":
            await self.disconnect(hold_connection)
            raise KeyError(f"Error: \"{query}\" failed. "
                           f"Device response: {ans.strip()}")

        if ans.decode("ascii").strip() == answer:
            await self.disconnect(hold_connection)
            return True
        else:
            return False
    
#end expect_query-anwser------------------------------------------------------------------    








