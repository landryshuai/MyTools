from pyDes import *
import pdb
def ByteToHex( byteStr ):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    """
    
    # Uses list comprehension which is a fractionally faster implementation than
    # the alternative, more readable, implementation below
    #   
    #    hex = []
    #    for aChar in byteStr:
    #        hex.append( "%02X " % ord( aChar ) )
    #
    #    return ''.join( hex ).strip()        

    return ''.join( [ "%02X " % ord( x ) for x in byteStr ] ).strip()
def hexTobytes(hexStr):
	"""
	convert hexS string to bytes
	"""
	bytes = [];
	hexStr = "".join(hexStr.split(" "));
	for i in range(0, len(hexStr), 2):
		bytes.append(chr(int(hexStr[i:i+2], 16)));
	return "".join(bytes)
def getKeyFromApdu(apdu):
	"""
	get key from Apdu
	"""
	lc = int(apdu[8:10], 16);
	return apdu[10: (10 + (lc -4)*2)];
def clacTransmitKey(mainKey, transmitKey):
	"""
	根据主密钥，和20号密钥，生成解密密钥的密钥
	"""
	keys = hexTobytes(mainKey);
	datas = hexTobytes(transmitKey);
	#pdb.set_trace();
	return clacDecrptKey(keys, datas)[1:17];
def clacWorkKey(transmitKey, workKey):
	"""
	计算出临时密钥，根据密钥明文和时间来分散
	"""
	result = clacDecrptKey(transmitKey, hexTobytes(workKey));
	return result[4:20];
def clacDecrptKey(key, data):
	"""
	加密数据：密钥和数据都是二进制数据
	"""
	length = len(key);
	if 8 == length:
		k = des(key, ECB , "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_NORMAL);
		return k.decrypt(data, padmode=PAD_NORMAL);
	elif length > 8:
		k = triple_des(key, ECB , "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_NORMAL);
		return k.decrypt(data, padmode=PAD_NORMAL);
	else:
		return ""
def clacEncrptKey(key, data):
	length = len(key);
	"""
	解密数据：密钥和数据都是二进制数据
	"""
	if 8 == length:
		k = des(key, ECB , "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_NORMAL);
		return k.encrypt(data, padmode=PAD_NORMAL);
	elif length > 8:
		k = triple_des(key, ECB , "\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_NORMAL);
		return k.encrypt(data, padmode=PAD_NORMAL);
	else:
		return ""
def desMac(key, data):
	trackLen = int(data[0:2]);
	value = data[2:(2+trackLen)];
	len8 = (trackLen/16)*16;
	trackStart = value[0:len8];
	trackEnd = value[len8:trackLen];
	return ByteToHex(clacDecrptKey(key, hexTobytes(trackStart))) + trackEnd;
####apdu keys
#key13 = "";
#key14 = "";
#key15 = "";
#key16 = "";
#key20 = "";
#apdu13 = getKeyFromApdu(key13);
#apdu14 = getKeyFromApdu(key14);
#apdu15 = getKeyFromApdu(key15);
#apdu16 = getKeyFromApdu(key16);
#apdu20 = getKeyFromApdu(key20);
########## 来自服务器的各种密钥
apdu13 = "B0260A171DFDF2886A6C3EF8570C75D54CCA0224C397F791";
apdu14 = "1399C70C50BBF14597BD5905D806E95DDE6868E03C488079";
apdu15 = "C17E6C8AEA508FE71FBB359AFA5D95D02998569238D71F56";
apdu16 = "4811AC2200DB64E02B18F6ADD9845C94B7488D00356F5B5F";
apdu20 = "5B6467B9D2B88F420D1C62B591FF0CF94B2E3146ECC8DBF5";
#####主密钥，注意生产和测试
mainKey = "11111111111111111111111111111111";

#####get plain keys
key1 = clacTransmitKey(mainKey, apdu20);
print "plain key1:" + ByteToHex(key1);
key13s = clacWorkKey(key1, apdu13);
key14s = clacWorkKey(key1, apdu14);
key15s = clacWorkKey(key1, apdu15);
key16s = clacWorkKey(key1, apdu16);
print "plain key13:" + ByteToHex(key13s);
print "plain key14:" + ByteToHex(key14s);
print "plain key15:" + ByteToHex(key15s);
print "plain key16:" + ByteToHex(key16s);

if __name__ == "__main__":
	####交易时候的参数
	timeFactor = "20140928152430" + "80";
	dynamicKeyData = "25D7CFAFC37D4144";
	### prepare temp keys
	print "timeFactor:" + timeFactor;
	print "dynamicKeyData:" + dynamicKeyData;
	tmp13key = clacEncrptKey(key13s,hexTobytes(timeFactor));
	tmp14key = clacEncrptKey(key14s,hexTobytes(timeFactor));
	tmp15key = clacEncrptKey(key15s,hexTobytes(timeFactor));
	tmp16key = clacEncrptKey(key16s,hexTobytes(timeFactor));
	tmp16key = clacEncrptKey(tmp16key,hexTobytes(dynamicKeyData));
	print "tmp key13:" + ByteToHex(tmp13key);
	print "tmp key14:" + ByteToHex(tmp14key);
	print "tmp key15:" + ByteToHex(tmp15key);
	print "tmp key16:" + ByteToHex(tmp16key);
	###解密密钥
	data14 = "AD673C28E746BB20";
	data14Result = clacDecrptKey(tmp14key, hexTobytes(data14));
	print "14 data:" + data14 + " and result is:" + ByteToHex(data14Result);
	###解密13号，账号金额等等
	data13 = "822084A3963779F1D06CABC7C3DE7228";
	data13Result = clacDecrptKey(tmp13key, hexTobytes(data13));
	print "13 data:" + data13 + " and result is:" + ByteToHex(data13Result);
	###解密16号，track
	data16 = "2931B68D3CA34C88A9D301022000000FFFFFFFFF"
	print "16 data:" + data16 + " and result is:" + desMac(tmp16key, data16);