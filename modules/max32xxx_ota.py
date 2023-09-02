async def otas_update_firmware(self, client: BleakClient):
        #---------------------------------------------------------------------------------------------------#
        #TODO make this use indications instead of delays- this is a proof of concept                       #
        #     Move this method to a different file                                                          #
        #     All the varaibles below are directly from WDX related headers                                 #
        #---------------------------------------------------------------------------------------------------#
        global fileLen
        # UUIDs
        WDX_SERVICE = "0000FEF6-0000-1000-8000-00805F9B34FB"
        WDX_Device_Configuration_Characteristic = "005f0002-2ff2-4ed5-b045-4c7463617865"
        WDX_File_Transfer_Control_Characteristic = "005f0003-2ff2-4ed5-b045-4c7463617865"
        WDX_File_Transfer_Data_Characteristic = "005f0004-2ff2-4ed5-b045-4c7463617865"
        WDX_Authentication_Characteristic   = "005f0005-2ff2-4ed5-b045-4c7463617865"
        ARM_Propietary_Data_Characteristic ="e0262760-08c2-11e1-9073-0e8ac72e0001"

        #WDXS File List Configuration
        WDX_FLIST_HANDLE       = 0   #brief File List handle */
        WDX_FLIST_FORMAT_VER   = 1   #brief File List version */
        WDX_FLIST_HDR_SIZE     = 7   #brief File List header length */
        WDX_FLIST_RECORD_SIZE  = 40  #brief File List record length */

        # Size of WDXC file discovery dataset 
        DATC_WDXC_MAX_FILES  = 4
        # File Transfer Control Characteristic Operations
        WDX_FTC_OP_NONE         = 0        
        WDX_FTC_OP_GET_REQ      = (1).to_bytes(1,byteorder='little',signed=False)      
        WDX_FTC_OP_GET_RSP      = 2      
        WDX_FTC_OP_PUT_REQ      = (3).to_bytes(1,byteorder='little',signed=False)      
        WDX_FTC_OP_PUT_RSP      = 4       
        WDX_FTC_OP_ERASE_REQ    = 5       
        WDX_FTC_OP_ERASE_RSP    = 6       
        WDX_FTC_OP_VERIFY_REQ   = (7).to_bytes(1,byteorder='little',signed=False)           
        WDX_FTC_OP_VERIFY_RSP   = 8     
        WDX_FTC_OP_ABORT        = 9     
        WDX_FTC_OP_EOF          = 10

        WDX_DC_OP_SET           = (2).to_bytes(1,byteorder='little',signed=False)  
        WDX_DC_ID_DISCONNECT_AND_RESET = (37).to_bytes(1,byteorder='little',signed=False)

        WDX_FILE_HANDLE = (0).to_bytes(2,byteorder='little',signed = False)
        WDX_FILE_OFFSET = (0).to_bytes(4,byteorder='little',signed=False)
        WDX_FILE_TYPE = (0).to_bytes(1,byteorder='little',signed=False)
        maxFileRecordLength = ((WDX_FLIST_RECORD_SIZE * DATC_WDXC_MAX_FILES) \
                            + WDX_FLIST_HDR_SIZE).to_bytes(4,byteorder='little',signed=False)

        #determine block size depending on MTU size
        svc = client.services.get_service(WDX_SERVICE)
        wdx_data_char = svc.get_characteristic(WDX_File_Transfer_Control_Characteristic)
        # determine mtu size and subtract 4 to fit the address 
        # and another 4 just because
        blocksize = wdx_data_char.max_write_without_response_size - 8
        if blocksize > 224:
            blocksize = 224
        else :
            blocksize = 120
                        
        logging.info(f"MTU size: {wdx_data_char.max_write_without_response_size}")
        logging.info(f"blocksize: {blocksize}")
        try:
            delayTime = 0.005
            resp = 1
            # --------------------| Enable required notifications |---------------------

            await self.enableCharNotification(client,ARM_Propietary_Data_Characteristic)
            await self.enableCharNotification(client,WDX_Device_Configuration_Characteristic)
            await self.enableCharNotification(client,WDX_File_Transfer_Control_Characteristic)
            await self.enableCharNotification(client,WDX_File_Transfer_Data_Characteristic)
            await self.enableCharNotification(client,WDX_Authentication_Characteristic)
          
            
            # --------------------| File discovery |---------------------
            #this is not additioin this is a byte array
            packet_to_send = (WDX_FTC_OP_GET_REQ)   \
                        + (WDX_FILE_HANDLE)   \
                        + (WDX_FILE_OFFSET)   \
                        + (maxFileRecordLength) \
                        + (WDX_FILE_TYPE)
            
            logging.info("sent discovery: " + str(list(packet_to_send)))
            resp = await client.write_gatt_char(WDX_File_Transfer_Control_Characteristic, bytearray(packet_to_send), response = True)
            while resp != None:
                await asyncio.sleep(delayTime)
            # --------------------| send header |---------------------
            # get file len and crc
            crc32 = self.get_crc32(self.updateFileName)
            file_len_bytes = (fileLen).to_bytes(4,byteorder='little',signed=False)
            # assemble packet and send
            packet_to_send = file_len_bytes + (crc32).to_bytes(4,byteorder='little',signed=False)  
            logging.info("sent header: " + str(list(packet_to_send)))         
            resp = 1
            resp = await client.write_gatt_char(ARM_Propietary_Data_Characteristic, bytearray(packet_to_send), response = True)
            while resp != None:
                await asyncio.sleep(delayTime)  
            # --------------------| send put request |---------------------
            # assemble packet and send
            packet_to_send = WDX_FTC_OP_PUT_REQ \
                            + (1).to_bytes(2,byteorder='little',signed=False) \
                            + WDX_FILE_OFFSET \
                            + file_len_bytes  \
                            + file_len_bytes  \
                            + WDX_FILE_TYPE
            logging.info("sent put req: " + str(list(packet_to_send)))  
            
            self.erase_complete = False
            await client.write_gatt_char(WDX_File_Transfer_Control_Characteristic, bytearray(packet_to_send))
           
            while self.erase_complete == False :
                await asyncio.sleep(delayTime)
             # --------------------| send file   |---------------------
            tempLen = fileLen
            logging.info("Start of sending file")
            address = 0x00000000  
            with open(self.updateFileName, 'rb') as f:
                while True:
                    try:
                        rawBytes = f.read(blocksize)
                        tempLen = tempLen - len(rawBytes)
                        percent =int((1-(tempLen / fileLen))*100)
                        self.otas_progress_value.emit(percent)
                        if not rawBytes:
                            break
                        nextAddress=(address).to_bytes(4,byteorder='little',signed=False)
                        resp = 1
                        resp = await client.write_gatt_char(WDX_File_Transfer_Data_Characteristic, bytearray(nextAddress + rawBytes))
                        address +=len(rawBytes)
                        while resp != None:
                            await asyncio.sleep(delayTime)
                        # Smaller blocksize indicates we are using OTAS with internal flash which is much slower
                        if blocksize < 220:
                            await asyncio.sleep(0.02)
                        else:
                            await asyncio.sleep(delayTime)
                    except Exception as err:
                        logging.info(err)
            self.otasUpdate = False
            logging.info("End of sending file")  
            time.sleep(1)
            # --------------------| send verify file request   |---------------------
            # assemble packet and send
            # file handle is incremented
            WDX_FILE_HANDLE = (1).to_bytes(2,byteorder='little',signed = False)
            packet_to_send = WDX_FTC_OP_VERIFY_REQ +  WDX_FILE_HANDLE
            logging.info("sent verify req: " + str(list(packet_to_send)))   
            resp = await client.write_gatt_char(WDX_File_Transfer_Control_Characteristic, bytearray(packet_to_send))
            while resp != None:
                await asyncio.sleep(delayTime)
            
            # --------------------| send reset request   |---------------------
            # # assemble packet and send
            packet_to_send = WDX_DC_OP_SET + WDX_DC_ID_DISCONNECT_AND_RESET 
            logging.info("sent reset req: " + str(list(packet_to_send))) 
            resp = 1  
            resp = await client.write_gatt_char(WDX_Device_Configuration_Characteristic, bytearray(packet_to_send))
            while resp != None:
                print("waiting")
                await asyncio.sleep(delayTime)
            
            await asyncio.sleep(delayTime)
            
            logging.info("File sent. Firmware update done")
            # ## TODO see what is going on with indications 

            self.disconnect_triggered = True
            # # TODO make gui clean up method/signal for disconnect event

        except Exception as err:
            logging.getLogger().setLevel(logging.WARNING)
            logging.warning(err)
            logging.getLogger().setLevel(logging.INFO)
            self.otasUpdate = False
        self.writeChar = False