from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import base64
from pydantic import BaseModel
from typing import List, Optional, Dict
import shutil
import os
from datetime import datetime
from chat_multi_turn import MultiTurnImageChat

# os.environ["http_proxy"] = "http://127.0.0.1:7897"
# os.environ["https_proxy"] = "http://127.0.0.1:7897"

app = FastAPI()

# 存储不同话题的对话实例
chat_sessions: Dict[str, MultiTurnImageChat] = {}

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 配置静态文件服务
app.mount("/images", StaticFiles(directory=OUTPUT_DIR), name="images")

@app.post("/generate-image")
async def generate_image(
    files: List[UploadFile] = File(None),
    prompt: str = Form(...),
    topic_id: str = Form(...)
):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{OUTPUT_DIR}/output_{timestamp}.jpg"
        
        # 获取或创建对话实例
        if topic_id not in chat_sessions:
            chat_sessions[topic_id] = MultiTurnImageChat()
            
        chat = chat_sessions[topic_id]
        
        # 如果上传了新图片，则处理新图片
        if files:
            input_filenames = []
            for i, file in enumerate(files):
                input_filename = f"{UPLOAD_DIR}/input_{timestamp}_{i}.jpg"
                with open(input_filename, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                input_filenames.append(input_filename)
            
            chat.upload_images(input_filenames)
            chat.add_user_message(prompt, [chat.files[-i].uri for i in range(len(files), 0, -1)])
        else:
            # 如果没有上传新图片，直接添加用户消息
            chat.add_user_message(prompt)
        
        # 生成图片
        chat.generate(output_filename)
        
        # 打印对话历史内容
        chat.print_conversation_history()
        
        # 确保输出文件存在
        if not os.path.exists(output_filename):
            raise HTTPException(status_code=500, detail="图片生成失败")
        
        # 读取生成的图片文件并转换为base64
        with open(output_filename, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        # 构建图片的URL路径
        image_url = f"/images/output_{timestamp}.jpg"
            
        return JSONResponse({
            "image_data": encoded_image,  # base64编码的图片数据
            "image_url": image_url,       # 可访问的图片URL
            "topic_id": topic_id,
            "status": "success"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 添加获取图片的端点
@app.get("/images/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join(OUTPUT_DIR, image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Image not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
