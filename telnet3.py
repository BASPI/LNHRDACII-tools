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
 
            self.connected = True
            print(f"[{self.name}] Connected to {self.ip}:{self.port}")

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
                self.writer.close()  # Close the writer

                # Check if `wait_closed()` exists before calling it
                if hasattr(self.writer, "wait_closed"):
                    await self.writer.wait_closed()

                print(f"[{self.name}] Disconnected from {self.ip}:{self.port}")

        except Exception as e:
            print(f"[{self.name}] Error while disconnecting: {e}")

        finally:
            self.connected = False
            self.reader = None
            self.writer = None  # Ensure cleanup


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

        # Send command
        self.writer.write(command + "\r\n")
        await self.writer.drain()

        try:
            print(f"[{self.name}] Before sending command")
    
            # Ensure the writer exists
            if not hasattr(self, 'writer') or self.writer is None:
                print(f"[{self.name}] Error: self.writer is None")
                return
    
            # Check if command is None
            if command is None:
                print(f"[{self.name}] Error: Command is None!")
                return
            
            # Ensure the command is a proper string
            if not isinstance(command, str):
                print(f"[{self.name}] Error: Command is not a string! Type: {type(command)}")
                return
    
            # Ensure the command ends with CRLF (\r\n)
            if not command.endswith("\r\n"):
                command += "\r\n"
            
            if command[0].lower() == "c":  # Control command
                print(f"[{self.name}] Control command detected, waiting {self._ctrl_cmd_delay} seconds")
                await asyncio.sleep(self._ctrl_cmd_delay)  # Wait for internal synchronization
                await self.writer.drain()

                if "write" in command.lower():  # Memory write command
                    print(f"[{self.name}] Memory write command detected, waiting additional {self._mem_wrt_delay} seconds")
                    await asyncio.sleep(self._mem_wrt_delay)
                    await self.writer.drain()

            # Send the command as a string
            if command[0].lower() != "c":  # Control command
                self.writer.write(command)  # Directly send the string with CRLF
                await self.writer.drain()  # Ensure it's sent
                print(f"[{self.name}] Sent command: {command.strip()} (with CRLF)")
    
            print(f"[{self.name}] Waiting for device response...")
    
            # Wait for response (if any), but handle timeout
            try:
                response = await asyncio.wait_for(self.reader.read(1024), timeout=5)
                print(f"[{self.name}] Device response: {response.strip()}")
            except asyncio.TimeoutError:
                print(f"[{self.name}] No response from device (which might be expected).")
    
        except Exception as e:
            print(f"[{self.name}] Unexpected error: {e}")

        
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

        self.writer.write(query + "\r\n")
        await self.writer.drain()

        ans = await self.reader.readuntil(eom)

        # Handle delays
        if query and query[0].lower() == "c":
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

        self.writer.write(query + "\r\n")
        await self.writer.drain()

        ans = await self.reader.readuntil(b"\r\n")

        if query and query[0].lower() == "c":
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








