# 成分表校验
import asyncio
import json
import time
import AI
import PDFtoIMG
from fastapi import FastAPI, UploadFile,Body,Form
from typing import Union
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()

# 配置跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有请求头
)


# 设置报错信息（不设置该函数，程序报错会自动终止）
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return {"code": 500, "msg": str(exc)}


# ocr文本获取
@app.post("/ocr")
async def ocr(file: UploadFile):
    # 保存上传的文件
    timestamp = str(int(time.time()))
    file_path = f"./file/{timestamp}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    mod=AI.Zhipu()
    # 将PDF转为图片（因为有的PDF无法被AI解析，所以先转为图片）
    try:
        file_path=PDFtoIMG.pdf_to_img(file_path)
    except Exception as e:
        return {"code":500,"msg":"PDF转图片失败："+str(e)}
    
    # 将图片上传到AI，并返回解析后的文本
    try:
        file_content=mod.pack_file(file_path)
    except Exception as e:
        return {"code":500,"msg":"文档解析失败："+str(e)}
    
    return {"code":200,"msg":"文档解析成功","data":file_content}


# 成分表检验
@app.post("/component")
def component_verify(target_text:str=Form(),all_text:str=Form()):
    system_prompt = """
    # 角色：
    你是一位专业的文本分析师，专门处理化妆品成分表的OCR识别匹配任务。

    # 任务：
    你的任务是从一个包含化妆品包装OCR识别文本的总文本中，找到与待匹配成分表完全一致的成分序列，并判断是否匹配成功。需要遵循以下规则来分析和生成结果：

    # 规则：
    - 成分的匹配要求逐项对比，必须完全一致，包括内容和顺序。
    - 如果总文本中成分表与待匹配文本完全一致，返回匹配成功。
    - 如果总文本中成分表中的成分缺失待匹配成分表中的任意项，返回部分成分缺失。
    - 如果成分表中的成分顺序不同，但内容完全存在，返回顺序不一致。
    - 注意：微量成分表和成分表是两个不同的东西，只需要匹配成分表
    - 输出格式必须为 JSON，包含以下字段：
    -- verify: 布尔值，表示是否成功匹配。
    -- data: 在总文本中找到的最符合的成分表。
    -- msg: 描述匹配结果的详细信息。

    # 示例输出
    1. 成功匹配：
    {
        "verify": true,
        "data": 水, 甘油, 丙二醇, 葡糖氨基葡聚糖,
        "msg": "匹配成功"
    }
    2. 成分缺失：
    {
        "verify": false,
        "data": 水, 甘油, 丙二醇,
        "msg": "部分成分缺失"
    }
    3. 顺序不一致：
    {
        "verify": false,
        "data": 甘油, 丙二醇, 水,
        "msg": "化妆品包装的成分表中成分顺序不一致"
    }

    """

    mod=AI.Zhipu()  

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content":f"# 待校验文本：{target_text}\n# 总文本：{all_text}"}]
    
    result=mod.chat(messages,isJson=True)
    if not result:
        result={"verify":False,"data":"","msg":"AI获取结果失败"}
    return result

# 微量成分校验
@app.post("/micro")
def micro_verify(target_text:str=Form(),all_text:str=Form()):
    system_prompt = """
    # 角色：
    你是一位专业的文本分析师，专门处理化妆品微量成分表的OCR识别匹配任务。

    # 任务：
    你的任务是从一个包含化妆品包装OCR识别文本的总文本中，找到与待匹配微量成分表完全一致的成分集合，并判断是否匹配成功。无需考虑成分顺序，但所有成分必须完整匹配。需要遵循以下规则来分析和生成结果：

    # 规则：
    - 微量成分的匹配要求逐项对比，内容必须完全一致，但成分的排列顺序可以不同。
    - 如果总文本中成分表与待匹配成分表的所有成分完全一致（无遗漏、无多余），返回匹配成功。
    - 如果总文本中成分表缺少待匹配成分表中的任何成分，返回部分成分缺失。
    - 如果总文本中有多余的成分，返回匹配失败并说明原因。
    - 注意：微量成分表和成分表是两个不同的东西，只需要匹配微量成分表
    - 输出格式必须为 JSON，包含以下字段：
    -- verify: 布尔值，表示是否成功匹配。
    -- data: 在总文本中找到的最符合的成分表。
    -- msg: 描述匹配结果的详细信息。

    # 示例输出
    1. 成功匹配：
    {
        "verify": true,
        "data": 水, 甘油, 丙二醇, 葡糖氨基葡聚糖,
        "msg": "匹配成功"
    }
    2. 成分缺失：
    {
        "verify": false,
        "data": 水, 甘油, 丙二醇,
        "msg": "部分成分缺失"
    }

    """

    mod=AI.Zhipu()  

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content":f"# 待校验文本：{target_text}\n# 总文本：{all_text}"}]
    
    result=mod.chat(messages,isJson=True)
    if not result:
        result={"verify":False,"data":"","msg":"AI获取结果失败"}
    return result

# 通用校验
@app.post("/general")
def general_verify(target_text:str=Form(),all_text:str=Form(),theme:str=Form()):
    system_prompt = """
    # 角色设定：
    你将扮演一位专业的文字识别和校验分析师，专注于分析化妆品包装盒上的OCR识别结果文本，并与用户提供的成分表或其他相关文本进行精确对比。你的任务是确保比对过程全面、准确，同时提供详细的对比结果。

    # 规则：
    - 仔细检查总文本中的所有内容，包括产品名称、成分列表、使用说明、注意事项、品牌信息等。
    - 优先根据用户提供的匹配主题定位相关文本区域，进行详细比对。
    - *主题名称不一定和总文本中的完全一致，需要根据主题名称的含义去做对比，例如用户提供的主题名称为“生产企业名称”，但实际上在总文本为“生产企业”*。
    - 在匹配主题时，允许主题名称包含前缀、后缀或同义词，例如“使用方法”可以匹配“产品使用方法”、“使用方法如下”等。
    - 如果主题名称在总文本中以变体形式出现，仍视为匹配成功。
    - 忽略标点符号、空格等格式差异，仅关注内容的匹配。
    - 输出仅限JSON格式，避免输出多余信息或额外解释。
    - 如果总文本中不存在匹配主题，需明确提示并合理返回。

    # 输出规则：
    1. 如果匹配主题在总文本中找到，且待校验文本完全匹配：
    {"verify": true, "data": 总文本中匹配到的内容, "msg": "匹配成功"}
    2. 如果匹配主题在总文本中找到，但待校验文本未完全匹配：
    {"verify": false, "data": 总文本中匹配到的内容, "msg": "匹配失败"}
    3. 如果匹配主题未在总文本中找到：
    {"verify": false, "data": , "msg": "匹配主题未找到"}

    # 注意事项：
    - 确保对比时无遗漏，总文本中可能存在换行符、特殊符号或分隔符，请预处理后再进行比对。
    - 返回结果中的data字段应为总文本中匹配到的内容，以便追溯。
    - 如果有多个匹配到的结果，请返回第一个匹配到的结果

    # 示例输出
    1. 成功匹配：
    {"verify": true, "data": 水, 甘油, 丙二醇, 葡糖氨基葡聚糖, "msg": "匹配成功"}
    2. 部分匹配失败：
    {"verify": false, "data": 水, 甘油, 丙二醇, "msg": "匹配失败"}
    3. 匹配主题不存在：
    {"verify": false, "data": "", "msg": "匹配主题未找到"}

    # 流程：
    1. 接收用户输入：匹配主题、待校验文本、总文本。
    2. 在OCR总文本中定位匹配主题对应的文本区域。
    3. 对定位区域内的文本与待校验文本逐项进行完全匹配比对（忽略符号差异）。
    4. 按照上述规则生成JSON格式输出。
    """

    mod=AI.Zhipu()  

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content":f"# 匹配主题：{theme}\n# 待校验文本：{target_text}\n# 总文本：{all_text}"}]
    
    result=mod.chat(messages,isJson=True)
    if not result:
        result={"verify":False,"data":"","msg":"AI获取结果失败"}
    return result

# 解释说明校验
@app.post("/explanation")
def explanation_verify(target_text:str=Form(),all_text:str=Form()):
    system_prompt = """
# 角色设定：
你是一位专业的化妆品文本分析与验证专家，专注于从化妆品包装OCR识别文本中提取并验证产品名称相关的解释说明。你的任务是确保这些解释说明（包括商标名、通用名、属性名）被准确提取，并以结构化形式返回。如果信息不完整或无法匹配用户预期，需返回明确的验证状态和失败信息。

# 任务目标：
提取并核对产品名称相关的解释说明，包括：
- **商标名**：商标是否为注册商标，是否有其他含义。
- **通用名**：产品名称中术语或功能的具体解释。
- **属性名**：产品的物理属性、功能性特征及使用方式。

# 规则：
1. **提取范围**：
   - 在OCR识别结果中，优先定位与产品名称相关的部分，提取产品名称及其解释说明。
   - 如果信息不完整或未明确标注，需合理补充，或注明为“无相关信息”。
2. **验证逻辑**：
   - 如果用户提供的字段信息（如商标名或通用名）与OCR文本完全一致，验证通过。
   - 如果不一致或信息缺失，验证失败，需明确说明失败原因。
3. **输出格式**：
   统一使用JSON格式返回，包括以下字段：
   {
       "verify": (true/false),
       "msg": (验证结果信息，例如“匹配成功”或失败原因),
       "data": {
           "产品名称": (产品名称字符串),
           "商标名": (商标相关说明字符串),
           "通用名": (通用名称解释字符串),
           "属性名": (属性相关说明字符串)
       }
   }

# 输出规则：
1. **成功匹配**：
   - "verify": true
   - "msg": "匹配成功"
   - "data" 包含完整的提取内容。
2. **部分匹配或信息缺失**：
   - "verify": false
   - "msg": 描述具体失败原因（如“商标名不一致”或“属性名未找到”）。
   - "data" 仍需包含所有提取的字段，缺失内容标注为“无相关信息”。
3. **完全未匹配**：
   - "verify": false
   - "msg": "未找到相关信息"
   - "data": 所有字段内容为空或为“无相关信息”。

# 示例输出
1. 完整匹配：
   {
       "verify": true,
       "msg": "匹配成功",
       "data": {
           "产品名称": "芙蕾恩肌肤补水能量喷雾",
           "商标名": "芙蕾恩为注册商标，无其他含义。",
           "通用名": "肌肤补水能量，肌肤补水是指为肌肤补充水分，改善肌肤干燥粗糙，使肌肤水润嫩滑；能量是指给予肌肤充沛水润呵护。",
           "属性名": "喷雾，是指以水、活性添加剂等为原料，经混合工艺制成的低粘度液体，从一个加有压力的容器中向外喷出的细雾状产品，其性状是液体。"
       }
   }

2. 部分匹配失败：
   {
       "verify": false,
       "msg": "通用名解释不一致",
       "data": {
           "产品名称": "芙蕾恩肌肤补水能量喷雾",
           "商标名": "芙蕾恩为注册商标，无其他含义。",
           "通用名": "肌肤补水能量，肌肤补水是指为肌肤补充水分，改善肌肤干燥粗糙。",
           "属性名": "喷雾，是指以水、活性添加剂等为原料，经混合工艺制成的低粘度液体，从一个加有压力的容器中向外喷出的细雾状产品，其性状是液体。"
       }
   }

3. 完全未匹配：
   {
       "verify": false,
       "msg": "未找到产品名称相关信息",
       "data": {
           "产品名称": "无相关信息",
           "商标名": "无相关信息",
           "通用名": "无相关信息",
           "属性名": "无相关信息"
       }
   }

# 流程：
1. 接收OCR总文本和用户提供的验证信息。
2. 从总文本中提取与产品名称相关的所有内容，并与用户提供的信息逐项比对。
3. 根据比对结果，生成包含“verify”和“msg”字段的JSON输出。
4. 如果无法找到相关信息，明确返回“未找到相关信息”。
"""



    mod=AI.Zhipu()  

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content":f"# 待校验文本：{target_text}\n# 总文本：{all_text}"}]
    
    result=mod.chat(messages,isJson=True)
    if not result:
        result={"verify":False,"data":"","msg":"AI获取结果失败"}
    return result

# 其他文案校验
@app.post("/official")
def official_verify(target_text:str=Form(),all_text:str=Form()):
    system_prompt = """
    # 角色设定：
    你将扮演一位专业的文字识别和校验分析师，专注于分析化妆品包装盒上的OCR识别结果文本，并与用户提供的成分表或其他相关文本进行精确对比。你的任务是确保比对过程全面、准确，同时提供详细的对比结果。

    # 规则：
    - 仔细检查OCR文本中的所有内容，包括但不限于：
        - 产品名称
        - 相关解释说明（如：使用说明、功效、适用范围等）
        - 品牌信息
        - 成分列表
        - 专利信息
        - 进口成分
        - 注意事项
        - 包装设计说明（如图案说明、无意义说明等）
        - 任何其他附加信息
    - 如果OCR文本中包含英文内容，必须与对应的中文翻译相符，确保中文与英文之间是完全对等的。
    - 优先根据用户提供的匹配主题（主题名称不一定在OCR文本中，需要自己根据主题名称的定义去匹配）定位相关文本区域，进行详细比对。
    - 对比要求：除符号差异外，文字内容需完全一致。如果出现换行符、特殊符号或分隔符等情况，应预处理后再进行比对。
    - 输出仅限JSON格式，避免输出多余信息或额外解释。
    - 如果OCR文本中不存在匹配主题，需明确提示并合理返回。

    # 输出规则：
    1. 如果匹配主题在总文本中找到，且待校验文本完全匹配：
    {"verify": true, "data": 总文本中匹配到的内容, "msg": "匹配成功"}
    2. 如果匹配主题在总文本中找到，但待校验文本未完全匹配：
    {"verify": false, "data": 总文本中匹配到的内容, "msg": "匹配失败"}
    3. 如果匹配主题未在总文本中找到：
    {"verify": false, "data": , "msg": "匹配主题未找到"}

    # 注意事项：
    - 确保对比时无遗漏，OCR识别结果中可能存在换行符、特殊符号或分隔符，请预处理后再进行比对。
    - 返回结果中的data字段应为OCR文本中匹配到的内容，以便追溯。
    - 如果有多个匹配到的结果，请返回第一个匹配到的结果。
    - 英文和中文之间的翻译应完全一致，确保二者相互匹配。

    # 示例输出：
    1. 成功匹配：
    {"verify": true, "data": 水, 甘油, 丙二醇, 葡糖氨基葡聚糖, Skin Moisturizing Energy Spray, "msg": "匹配成功"}
    2. 部分匹配失败：
    {"verify": false, "data": 水, 甘油, 丙二醇, "msg": "匹配失败"}
    3. 匹配主题不存在：
    {"verify": false, "data": "", "msg": "匹配主题未找到"}

    # 流程：
    1. 接收用户输入：匹配主题、待校验文本、OCR识别结果的总文本。
    2. 在OCR总文本中定位匹配主题对应的文本区域。
    3. 对定位区域内的文本与待校验文本逐项进行完全匹配比对（忽略符号差异）。
    4. 按照上述规则生成JSON格式输出。

    """

    mod=AI.Zhipu()  

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content":f"# 待校验文本：{target_text}\n# 总文本：{all_text}"}]
    
    result=mod.chat(messages,isJson=True)
    if not result:
        result={"verify":False,"data":"","msg":"AI获取结果失败"}
    return result


# 按有关规定应当标注的其他内容 （文字部分）
@app.post("/other_text")
def other_text_verify(target_text:str=Form(),all_text:str=Form()):
    system_prompt = """
    # 角色设定：
    你将扮演一位专业的文字识别和校验分析师，专注于分析化妆品包装盒上的OCR识别结果文本，并与用户提供的成分表或其他相关文本进行精确对比。你的任务是确保比对过程全面、准确，同时提供详细的对比结果，特别是关注按法规要求必须标注的内容。

    # 规则：
    - 仔细检查OCR文本中的所有内容，包括但不限于产品名称、成分列表、使用说明、注意事项、品牌信息、注册商标、生产批号、限期使用日期、储存方法等。
    - 特别关注符合国家或地区法律法规要求的标注内容，如产品的功效、使用方法、注意事项、生产批号及限期使用日期、储存方法、产地、条形码、注册商标等。
    - 优先根据用户提供的匹配主题（如标签信息、产品功能、法律标识等）定位相关文本区域，进行详细比对。
    - 对比要求：除符号差异外，文字内容需完全一致，确保符合法规要求。
    - 输出仅限JSON格式，避免输出多余信息或额外解释。
    - 如果OCR文本中不存在匹配主题，需明确提示并合理返回。

    # 输出规则：
    1. 如果匹配主题在总文本中找到，且待校验文本完全匹配：
    {"verify": true, "data": 总文本中匹配到的内容, "msg": "匹配成功"}
    2. 如果匹配主题在总文本中找到，但待校验文本未完全匹配：
    {"verify": false, "data": 总文本中匹配到的内容, "msg": "匹配失败"}
    3. 如果匹配主题未在总文本中找到：
    {"verify": false, "data": , "msg": "匹配主题未找到"}

    # 注意事项：
    - 确保对比时无遗漏，OCR识别结果中可能存在换行符、特殊符号或分隔符，请预处理后再进行比对。
    - 返回结果中的data字段应为OCR文本中匹配到的内容，以便追溯。
    - 如果有多个匹配到的结果，请返回第一个匹配到的结果。
    - 重点检查所有必须标明的内容，如“生产批号和限期使用日期”、“注意事项”、“注册商标”等。
    
    # 示例输出
    1. 成功匹配：
    {"verify": true, "data": 清新爽肤, 水感舒适, 莹润嫩滑, "msg": "匹配成功"}
    2. 部分匹配失败：
    {"verify": false, "data": 清新爽肤, 水感舒适, "msg": "匹配失败"}
    3. 匹配主题不存在：
    {"verify": false, "data": , "msg": "匹配主题未找到"}

    # 流程：
    1. 接收用户输入：匹配主题、待校验文本、OCR识别结果的总文本。
    2. 在OCR总文本中定位匹配主题对应的文本区域。
    3. 对定位区域内的文本与待校验文本逐项进行完全匹配比对（忽略符号差异）。
    4. 按照上述规则生成JSON格式输出。
"""

    mod=AI.Zhipu()  

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content":f"# 待校验文本：{target_text}\n# 总文本：{all_text}"}]
    
    result=mod.chat(messages,isJson=True)
    if not result:
        result={"verify":False,"data":"","msg":"AI获取结果失败"}
    return result

# 按有关规定应当标注的其他内容 （标志部分）
def other_sign_verify(text:str,file_path:str):
    prompt =f"""
    # 请问图片中是否存在以下标志：
    {text}
    """
    prompt+="""
    # 输出规则：
    1. 如果存在：
    {"verify": true, "data": "指出标志在图片中的位置", "msg": "匹配成功"}
    示例：
    {"verify": true, "data": "标志在图片左上角", "msg": "匹配成功"}
    2. 如果不存在：
    {"verify": false, "data": "", "msg": "匹配失败"}

    """
    mod=AI.ZhipuPlus()
    result=mod.chat(prompt,file_path)
    try:
        result=json.loads(result)
    except Exception as e:
        result={'verify': False, 'data': '', 'msg': '匹配失败'}
    return result

# 字体校验
def font_verify(file_path:str):
    prompt="""
    请检查图片中的字体，是否所有的英文字体大小都小于中文字体大小
    # 输出规则：
    1. 如果是：
    {"verify": true, "data": "", "msg": "匹配成功"}
    2. 如果不是：
    {"verify": false, "data": "指出英文字体大于中文字体的文本", "msg": "匹配失败"}
    示例：
    {"verify": false, "data": "在芙蕾恩Fuleien中Fuleien字体较大", "msg": "匹配失败"}

    """
    mod=AI.ZhipuPlus()
    result=mod.chat(prompt,file_path)
    try:
        result=json.loads(result)
    except Exception as e:
        result={'verify': False, 'data': '', 'msg': 'AI获取结果失败'}
    return result


# 去除换行符
def remove_newline(text:str):
    return text.replace("\n","")

# 主函数
@app.post("/verify")
async def verify(data: Union[dict, str], file: UploadFile):
    # 如果传入的是文本，解析为字典
    if isinstance(data,str):
        try:
            data=json.loads(data)
        except Exception as e:
            return {"code": 400, "msg": "data的格式为JSON", "data": ""}
        
    # 将图片上传到AI，并返回解析后的文本
    ocr_result=await ocr(file)
    if ocr_result.get("code")==200:
        file_content=ocr_result.get("data")
    else:
        return ocr_result

    results = []

    # 模板类似的，统一匹配
    verify_key=list(data.keys())

    verify_key.remove("产品名称相关解释说明")
    verify_key.remove("其他文案内容")
    verify_key.remove("按有关规定应当标注的其他内容")
    
    # 创建任务列表
    tasks = []
    
    # 添加主要验证任务
    for key in verify_key:
        if "以上成分" in key:
            tasks.append({"type": key, "func": component_verify, "args": (remove_newline(data[key]), file_content)})
        elif "微量成分" in key:
            tasks.append({"type": key, "func": micro_verify, "args": (remove_newline(data[key]), file_content)})
        else:
            tasks.append({"type": key, "func": general_verify, "args": (remove_newline(data[key]) , file_content,key)})
    
    # 添加其他文案内容验证任务
    tasks.append({
        "type": "其他文案内容",
        "func": official_verify,
        "args": (remove_newline(data["其他文案内容"]), file_content)
    })
    
    # 处理其他内容
    other_data = data["按有关规定应当标注的其他内容"]
    sign_data = []
    other_text_data = []
    
    for other_value in other_data:
        other_value=remove_newline(other_value)
        if "标志" in other_value:
            sign_data.append(other_value)
        else:
            other_text_data.append(other_value)
            
    # 添加其他内容验证任务
    tasks.append({
        "type": "按有关规定应当标注的其他内容-文本",
        "func": other_text_verify,
        "args": (other_text_data, file_content)
    })
    
    # 并行执行所有验证任务
    async def execute_verify(task):
        result = await asyncio.to_thread(task["func"], *task["args"])
        result["ready"] = task["args"][0]
        return {"type": task["type"], "result": result}
        
    verify_results = await asyncio.gather(*[execute_verify(task) for task in tasks])
    results.extend(verify_results)


    return {"code": 200, "msg": "验证完成", "data": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
