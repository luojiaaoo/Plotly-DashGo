from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
from Crypto.Random import get_random_bytes
from config.dash_melon_conf import EncryptConf
from typing import Optional


def encrypt_data(data: str, key: Optional[str] = None) -> str:
    """
    使用AES算法加密数据

    :param data: 要加密的数据
    :param key: 加密密钥字符串，必须是16、24或32字节长
    :return: 加密后的数据，Base64编码的字符串
    """
    if key is None:
        key = EncryptConf.CUSTOM_KEY
    key_bytes = bytes.fromhex(key)

    # 生成一个随机的16字节IV（初始化向量）
    iv = get_random_bytes(AES.block_size)

    # 创建AES cipher对象
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)

    # 对数据进行填充
    padded_data = pad(data.encode('utf-8'), AES.block_size)

    # 加密数据
    encrypted_data = cipher.encrypt(padded_data)

    # 将IV和加密数据拼接，并进行Base64编码
    encrypted_data_with_iv = iv + encrypted_data
    encoded_data = base64.b64encode(encrypted_data_with_iv).decode('utf-8')

    return encoded_data


def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    使用AES算法解密数据

    :param encrypted_data: 要解密的数据，Base64编码的字符串
    :param key: 解密密钥字符串，必须与加密时使用的密钥相同
    :return: 解密后的数据
    """
    if key is None:
        key = EncryptConf.CUSTOM_KEY
    key_bytes = bytes.fromhex(key)

    # 将Base64编码的字符串解码
    encrypted_data_with_iv = base64.b64decode(encrypted_data)

    # 提取IV和加密数据

    iv = encrypted_data_with_iv[: AES.block_size]
    encrypted_data = encrypted_data_with_iv[AES.block_size :]

    # 创建AES cipher对象
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)

    # 解密数据
    decrypted_padded_data = cipher.decrypt(encrypted_data)

    # 去除填充
    decrypted_data = decrypted_padded_data, AES.block_size.decode('utf-8')

    return decrypted_data
