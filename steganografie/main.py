from PIL import Image
from bitarray import bitarray


 # 1. create object of class Steganography
 # 2. call method Encode or Decode
 # 3. if you want to encode text, set imagePath, message and encode to True
 # 4. if you want to encode file, set imagePath, file2encode and encode to True
 # 5. if you want to decode text, set imagePath and encode to False
 # 6. if you want to decode file, set imagePath and encode to False
 
# Example of encoding text
# steganography = Steganography(imagePath='image.png', message='Hello world', encode=True)

# Example of decoding text
# steganography = Steganography(imagePath='image.png', encode=False)

# Example of encoding file
# steganography = Steganography(imagePath='image.png', file2encode='file.txt', encode=True)

# Example of decoding file
# steganography = Steganography(imagePath='image.png', encode=False)



class Steganography:
    def __init__(self, imagePath: str, encode: bool = True, message: str = None, file2encode: str = None):
        self.imagePath = imagePath
        self.message = message
        self.encode = encode
        self.file2encode = file2encode
        self.file2encodeBinary = self.file2bitarray(file2encode) if file2encode is not None else None
        self.image = self.loadImage(imagePath)
        if encode is True:
            self.Encode()
        else:
            self.Decode()
                 
    def createHeader(self): 
        # 1 bit rika jestli se jedna o soubor
        is_file = True if self.file2encode is not None else False
        # Nazev souboru
        fileName = self.file2encode.split('\\')[-1] if is_file else 'file.txt'
        fileName_bits = self.message2Binary(fileName.ljust(64, ' '))  # Doplnění nulovými bity do délky 512 bitů
        # velikost hlavicky (65 bitu -> 1 bit pro typ zpravy, 64 bity pro zacatek a konec zpravy) (64x8 = 512 bitu pro nazev souboru)
        start_pos = 577
        # 32 bitu pro konec pozici
        end_pos = start_pos + self.getMessageBitCount(self.message) if self.message is not None else start_pos + len(self.file2encodeBinary)
        
        print(f'is_file: {is_file}, start_pos: {start_pos}, end_pos: {end_pos}, fileName: {fileName}')
        header_bits = bitarray()
        header_bits.append(is_file)
        header_bits.frombytes(start_pos.to_bytes(4, 'big'))
        header_bits.frombytes(end_pos.to_bytes(4, 'big'))
                
        header_bits.extend(fileName_bits)
        
        print(f'Header (binary): {header_bits.to01()}')
        print(f'size: {len(header_bits)}')
        return header_bits
            
    def getMessageBitCount(self, message):
        return len(self.message2Binary(message))
    
    def loadImage(self, path):
        return Image.open(path).convert('RGBA')
    
    def file2bitarray(self,file_path):
        with open(file_path, 'rb') as file:
            file_content = file.read()
            # Převod obsahu souboru na bitarray
            binary_content = bitarray()
            binary_content.frombytes(file_content)
        return binary_content
    
    def message2Binary(self, message):
        message_bits = bitarray()
        for char in message:
            char_bits = format(ord(char), "08b")
            message_bits.extend([int(bit) for bit in char_bits])
        print(f'Message - {message} (binary): {message_bits.to01()}')
        return message_bits
         
        
    def binary2Message(self, binary):
        return binary.tobytes().decode("utf-8")
    
    def binaryHeader2Text(self, binary):
        message = ""
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            message += chr(int(byte, 2))
        return message
    
    def Encode(self):
        imageCopy = self.image.copy()
        message = self.message2Binary(self.message) if self.message is not None else self.file2encodeBinary

        print(f'Image size: {len(imageCopy.getdata())*3 - 577} ') 
        print(f'Message size: {len(message)}')
        
        if len(message) > (len(imageCopy.getdata()) * 3 - 577): # 577 je velikost hlavičky
            print("Error: Zpráva je příliš dlouhá pro zakódování do tohoto obrázku.")
            return
        
        header = self.createHeader()
        messageIndex = 0
        headerIndex = 0
        for i, pixel in enumerate(imageCopy.getdata()):
            if headerIndex >= len(header):
                break
            r, g, b, a = pixel
            headerBits = header[headerIndex:headerIndex+3]
            headerIndex += 3
            #print(f'BEFORE HEADER pixel {pixel}, r: {r}, g: {g}, b: {b}, index: {i}')
            r, g, b = [self.changeLSB(component, headerBits[i]) if i < len(headerBits) else component for i, component in enumerate((r, g, b))]
            imageCopy.putpixel((i % imageCopy.width, i // imageCopy.width), (r, g, b, a))
            #print(f'AFTER  HEADER pixel {pixel}, r: {r}, g: {g}, b: {b}, index: {i}')
            
        for i ,pixel in enumerate(imageCopy.getdata()):
            if (i*3) < 577:
                continue
            if messageIndex >= len(message) :
                break
            r, g, b, a = pixel
            messageBits = message[messageIndex:messageIndex + 3]
            messageIndex += 3
            #print(f'BEFORE pixel {pixel}, r: {r}, g: {g}, b: {b}, index: {i}')
            r, g, b = [self.changeLSB(component, messageBits[i]) if i < len(messageBits) else component for i, component in enumerate((r, g, b))]          
            #print(f'AFTER  pixel {pixel}, r: {r}, g: {g}, b: {b}, index: {i}')
            imageCopy.putpixel((i % imageCopy.width, i // imageCopy.width), (r, g, b, a))

        
        imageCopy.save('output.png')
        print('Image encoded successfully')
        
    def Decode(self):
        header = bitarray()
        message = bitarray()
        bitReaded = 0
        
        # Čtení hlavičky
        for pixel in self.image.getdata():
            r, g, b, _ = pixel
            
            for component in (r, g, b):
                header.append(self.getLSB(component))
                bitReaded += 1
                
                if bitReaded >= 577:  # Konec hlavičky
                    break
            
            if bitReaded >= 577:
                break
        
        # Získání typu zprávy (text nebo soubor)
        messageType = header[0]    
        # Získání pozice začátku a konce zprávy
        messageStart = int(header[1:33].to01(), 2)
        messageEnd = int(header[33:65].to01(), 2)
        messageFileName = self.binary2Message(header[65:577])
        
        print(f'header len {len(header)}, messageType: {messageType}, messageStart: {messageStart}, messageEnd: {messageEnd}, messageFileName: {messageFileName}')
        
        # Posun na začátek zprávy
        readComponents = 0
        for pixel in self.image.getdata():
            r, g, b, _ = pixel
            for component in (r, g, b):
                if readComponents < messageStart + 2:
                    readComponents += 1
                    continue
                if readComponents >= messageEnd + 2:
                    break
                message.append(self.getLSB(component))
                readComponents += 1
            if readComponents >= messageEnd + 2:
                # Pokud jsme již přečetli celou zprávu, přestaňte číst
                break
        
        # Pokud je typ zprávy text, převede bitarray zprávy na řetězec
        if messageType == 0:
            decodedMessage = self.binary2Message(message)
            print(f"Decoded Text Message: {decodedMessage}")
        else:
            self.binary2textFile(message, 'decoded_' + messageFileName)


        
        # Pokud je typ zprávy text, převede bitarray zprávy na řetězec
        if messageType == 0:
            print(f'Decoded Text Message (binary): {message.to01()}')
            decodedMessage = self.binary2Message(message)
            print(f"Decoded Text Message: {decodedMessage}")
        else:
            self.binary2textFile(message, 'decoded_' + messageFileName)

    def changeLSB(self, byte, messageBit):
        #print(f'byte: {byte}, messageBit: {messageBit}, result: {(byte & 0b11111110) | messageBit}')
        return (byte & 0b11111110) | messageBit
    
    def getLSB(self, byte):
        #print(f'byte: {byte}, result: {byte & 1}')
        return byte & 1
    
    def binary2textFile(self,message, output_file_path):
        with open(output_file_path, 'wb') as file:
            # Převede bitarray na bytes a zapíše je do souboru
            file.write(message.tobytes())    
            
            


             



