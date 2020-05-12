
from Crypto.Cipher import AES
import base64
from lib.utils.wechat.utils import Prpcrypt


s="xUMdF8vWqJPrUT91OLLrLvZOtmhDAPJFOa/O9M5p5k5kenUUJaeA4BwTkFMlJHqWVnoh7sxc5+Z8hrx7jkhl0Y/DqkK38QIew8YyYLg9BjoAfWnQuUD74bwMWb3C2yEZlnQZrqY7MbvBMWpYL/jkl19LjWcBRptqeLOPWSi5MiP6nTo5+EcKmSR/PPLKkteXRAd549zN38nvSTHutPJzAp1vhbU3P/M6mRl0PcioyOQlIiqt4p9FotB6DgajwWJK1wbbZ/RBqjNgIP/D9+S/yzPqMgJgFzXIRV0jBKBie4LDycMYzg83gciFIV9o/g53W5mif3qUYdiRkGBVZJNGV5CCJsrG8BesmHL2HQlnovUmXUR5Y4ORLxCjtfMhRrfKMSfwZn5pXCq+S0r/FZV6np1HEKWtkkKV+bWtJN4v9FBSXf+23vdyLwk+x/6tpNT0zup5cTm+s8IoomCTR+TZIH+edxhZ03FT6Ag42VAdt1+wfJdXqNRizkBDiWA6iqLewdycHFRD9fOwQer/N8O8NAZ5yrRSmrT0LkwfmGxcBjHyjOfTBBWbqsjvPI7lkNvAx3fOi1Ja/5ZDarFB5FPmoA=="
key = base64.b64decode('FDl8GfVXfGWwKs9LKc11xE6N2f8DM6MB8cyMm6xYsac' + "=")

cryptor = AES.new(key, AES.MODE_CBC, key[:16])
# 使用BASE64对密文进行解码，然后AES-CBC解密
plain_text = cryptor.decrypt(base64.b64decode(s.encode("utf-8")))
print(plain_text)

pc = Prpcrypt(key)
xml_content = pc.decrypt(s.encode('utf-8'), "wxe87236d542cd0f94")