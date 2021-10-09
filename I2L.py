#!/usr/local/Cellar/python/3.7.7/bin/python3
import os
import base64
import requests
import json
from PIL import ImageGrab
import pyperclip
import io

env = os.environ
default_headers = {
    'app_id': env.get('APP_ID', '你的APP_ID'),
    'app_key': env.get('APP_KEY', '你的APP_KEY'),
    'Content-type': 'application/json'
}
service = 'https://api.mathpix.com/v3/latex'

#
# Return the base64 encoding of an image with the given filename.
#
def image_uri(filename):
    image_data = open(filename, "rb").read()
    return "data:image/jpg;base64," + base64.b64encode(image_data).decode()

#
# Call the Mathpix service with the given arguments, headers, and timeout.
#
def latex(args, headers=default_headers, timeout=30):
    r = requests.post(service,
                      data=json.dumps(args), headers=headers, timeout=timeout)
    return json.loads(r.text)

# 替换字符串内指定字符
def replace_char(string, char, index):
    string = list(string)
    string[index] = char
    return ''.join(string)

# 减少返回的 latex 字段中的空格
def reduce_space(string):
    # 找到本身是空格的位置,并且前后的字符都是字母或数字,便将其替换成$, 之后替换掉全部空格,在替换$为空格.
    # 这样替换的原因是,假如某一个空格前后都是字母.去掉这个空格容易引起 latex 格式混乱.
    for i in range(len(string) - 2):
        if string[i + 1] == " " and string[i].isalnum() and string[i + 2].isalnum():
            string = replace_char(string, "$", i + 1)
    string = string.replace(" ", "")
    string = string.replace("$", " ")
    return string

# 更新文件内容,path 为文件地址,content 为新写入的内容
def update_file(path,content):
    with open(path, 'r+') as f:
        f.seek(0)
        f.truncate()  # 清空
        f.write(content)

# 这三个文件分别是用来保存 api 调用次数,调用是否成功的状态,以及调用返回的结果,主要是为了配合Keyboard Maestro使用.
record_file_path=r'E:\Document\PAD\I2L\record'
status_file_path=r'E:\Document\PAD\I2L\status'
result_file_path=r'E:\Document\PAD\I2L\result'

def mathpix():
    # 从剪贴板获取公式
    image = ImageGrab.grabclipboard()  # 获取剪贴板文件 返回an image, or None if the clipboard does not contain image data.

    if image is not None:
        # 更新调用的次数
        with open(record_file_path, 'r+') as recordf:
            num = int(recordf.read())
            num = num + 1
            recordf.seek(0)
            recordf.truncate()
            recordf.write(str(num))

        imgByteArr = io.BytesIO()
        image.save(imgByteArr, format='JPEG')
        imgByteArr = imgByteArr.getvalue()
        # 转 base64
        base64_data = base64.b64encode(imgByteArr)
        s = "data:image/jpg;base64," + base64_data.decode()

        latex_result = latex({
            'src': s,
            "ocr": ["math", "text"],
            'formats': ['latex_normal']
        })

        # 假如你要识别的图片里没有数学公式,那返回的结果里会有 error 字段.
        if 'error' not in latex_result.keys():
            # 把识别的结果 print 出来,在 Maestro 里调用这个脚本,会把 print 的内容保存到剪切板里
            print('$'+reduce_space(latex_result['latex_normal'])+'$')
            # 把识别的结果也保存到 result 这个文件里.
            update_file(result_file_path,'$'+reduce_space(latex_result['latex_normal'])+'$')
            # 更新 status 这个文件里的内容为成功 
            update_file(status_file_path,"成功")
            pyperclip.copy('$'+latex_result['latex_normal']+'$')
        else:
            update_file(result_file_path, "图像里不含数学公式")
            update_file(status_file_path, "失败")
    else:
        update_file(result_file_path, "剪切板没有图像文件")
        update_file(status_file_path, "失败")

if __name__ == '__main__':
    mathpix()
  