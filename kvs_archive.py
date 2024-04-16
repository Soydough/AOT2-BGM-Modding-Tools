import glob
import argparse
import struct
import os

parser = argparse.ArgumentParser(description="AOT2 .ktsl2stbin files archiving tool.")
parser.add_argument("folder", help="folder with .kvs files")
args = parser.parse_args()
kfolder = args.folder

def read_bytes(filename):
    print("Reading file " + filename)
    b_list = []
    
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(1024)  
            if not piece:
                break
            b_list.append(piece)

    return b_list
    
def write_file(name, data):
    print("Writing file " + name)
    # First 96 bytes (0x60)
    # This probably only works with AOT2 because the header might be different in each game
    header = b'KTSR\x02\x94\xDD\xFC\x01\x00\x00\x01\xA8\x82=\x06\x00\x00\x00\x00\x00\x00\x00\x00\xC0r\xC31\xC0r\xC31\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    with open(name, "wb") as new_file:
        new_file.write(header + data)

files = glob.glob(kfolder+'/*.[kK][vV][sS]')
fbytes = []

for f in files:
    # Write header
    # Structure is like this:
    # 09 D4 F4 15 	4 Byte 	The signature of the subheader
    # Length with Subheader 	4 Byte 	An Int32 declaring the total size of the following KTSS including this subheader
    # Unknown 	4 Byte 	We can assume that it's some form of checksum. Doesn't seem to be important.
    # Subheader length 	4 Byte 	The length of the subheader itself
    # KVS length 	4 Byte 	The length of the KVS file
    # NULL Bytes 	Dynamic 	Subheader length - 20 Bytes = Count of NULL bytes
    kvs_bytes = read_bytes(f)

    # Calculate the padding needed
    bytes_needed_to_pad_kvs = 16 - sum(len(piece) for piece in kvs_bytes) % 16
     # if bytes_needed_to_pad_kvs == 16 and trail_padding > 0:
    if bytes_needed_to_pad_kvs == 16:
        bytes_needed_to_pad_kvs = 0
        
    added_padding = 0
    while added_padding < bytes_needed_to_pad_kvs:
        kvs_bytes[-1] = kvs_bytes[-1] + b"\00"
        added_padding = added_padding + 1      
        

    # Calculate the length of the actual data without padding
    kvs_length = os.path.getsize(f)

    length_with_subheader_binary = kvs_length + added_padding + 32

    length_binary = struct.pack('<I', kvs_length)
    padded_length_binary = length_binary.ljust(16, b'\x00')
    
    fbytes.append(b"\x09\xD4\xF4\x15")  # Magic
    
    fbytes.append(length_with_subheader_binary.to_bytes(4, byteorder='little'))  # Length with Subheader
    
    fbytes.append(b"\xFF\xFF\xFF\xFF")  # Unknown
    fbytes.append(b"\x20\x00\x00\x00")  # Header size
   
    fbytes.append(padded_length_binary) # Kvs length + padding
    
    fbytes.extend(kvs_bytes)  # Actual KVS data
    
write_file("mod.ktsl2stbin", b"".join(fbytes))
