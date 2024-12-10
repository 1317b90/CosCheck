from openai import OpenAI
import json
from pathlib import Path
import base64
from PIL import Image
import io

# 去除markdown语法
def removeMark(text):
    remove_chars = ["#", "**", "- ","\n\n","```json","```","\n","\t"," "]
    for char in remove_chars:
        text = text.replace(char, "")

    return text


class Zhipu():
    def __init__(self):
        self.client = OpenAI(
            api_key="b584a661b8ad396befa3796f23040a62.6eRLSQxYOITVLDaC",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
        )

    # 一般对话
    def chat(self,messages:list,model="GLM-4-Flash",temperature=0.0,top_p=0.7,isJson=False,isRemoveMark=True):
        response =self. client.chat.completions.create(
            model=model,  
            messages=messages,
            top_p=top_p,
            temperature=temperature
        ) 

        result=response.choices[0].message.content

        if isRemoveMark:
            result= removeMark(result)
        if isJson:
            try:
                result=json.loads(result)
            except Exception as e:
                print(str(e))
                print(result)
                result=None
        return result

    # 上传文件并返回id
    def up_file(self,filePath:str):
        fileData = self.client.files.create(file=Path(filePath), purpose="file-extract")
        return fileData.id

    # 解析文件
    def parse_file(self,fileId:str):
        return json.loads(self.client.files.content(fileId).content)["content"]

    # 删除文件
    def del_file(self,fileId:str):
        return  self.client.files.delete(
        file_id=fileId
        )

    # 上传文件，解析，删除文件，一次性
    def pack_file(self,filePath:str):
        fileId=self.up_file(filePath)
        content=self.parse_file(fileId)
        self.del_file(fileId)
        return content

# 智谱多模态
class ZhipuPlus():
    def __init__(self):
        self.client = OpenAI(
            api_key="b584a661b8ad396befa3796f23040a62.6eRLSQxYOITVLDaC",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
        )
    
    def chat(self,text:str,img_path:str,isRemoveMark=True):
        # 将路径中的图片读取，然后转为base64
        with Image.open(img_path) as img:
            # 将图片转换为字节流
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")  # 你可以根据需要更改格式，如JPEG
            img_byte = buffered.getvalue()
        
        img_base=base64.b64encode(img_byte).decode('utf-8')

        response = self.client.chat.completions.create(
            model="glm-4v-plus",  # 填写需要调用的模型名称
            messages=[
            {
                "role": "user",
                "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_base
                    }
                },
                {
                    "type": "text",
                    "text": text
                }
                ]
            }
            ]
        )

        result=response.choices[0].message.content

        if isRemoveMark:
            result= removeMark(result)

        return result


class Kimi():
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-q1wroyGTNXlUdZriqYZgJAAgKm6NdMeutgWoTDvDuFsrTlth",
            base_url="https://api.moonshot.cn/v1",
        )

    # 一般对话
    def chat(self,messages:list,temperature=0.0,top_p=0.7,isJson=False,isRemoveMark=True):
        response =self. client.chat.completions.create(
            model="moonshot-v1-128k",  
            messages=messages,
            top_p=top_p,
            temperature=temperature
        ) 


        result=response.choices[0].message.content

        if isRemoveMark:
            result= removeMark(response.choices[0].message.content)

        if isJson:
            try:
                result=json.loads(result)
            except:
                print(result)
                result=None
        return result
    
    # 上传文件并返回id
    def up_file(self,filePath:str):
        fileData = self.client.files.create(file=Path(filePath), purpose="file-extract")
        return fileData.id

    # 解析文件
    def parse_file(self,fileId:str):
        return json.loads(self.client.files.content(fileId).text)["content"]

    # 删除文件
    def del_file(self,fileId:str):
        return  self.client.files.delete(
        file_id=fileId
        )

    # 上传文件，解析，删除文件，一次性
    def pack_file(self,filePath:str):

        fileId=self.up_file(filePath)
        
        content=self.parse_file(fileId)
        
        self.del_file(fileId)
        return content

class DeepSeek():
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-42755e5134584426b7405843e4746a0d",
            base_url="https://api.deepseek.com",
        )

    # 一般对话
    def chat(self,messages:list,max_tokens=1024,temperature=1.0,isJson=False,isRemoveMark=True):
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.0 if isJson else temperature,
            stream=False,
            response_format= {
                'type': 'json_object' if isJson else 'text'
            }
        )
        result=response.choices[0].message.content
        
        if isRemoveMark:
            result= removeMark(result)

        if isJson:
            try:
                result=json.loads(result)
            except:
                print(result)
                result=None
        return result

if __name__ == "__main__":
    pass
