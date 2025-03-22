# 导入所需的Python模块
import base64
import os
import threading
from google import genai
from google.genai import types
from typing import List, Optional


# 保存二进制文件的辅助函数
def save_binary_file(file_name: str, data: bytes) -> None:
    with open(file_name, "wb") as f:
        f.write(data)


# 多轮图像对话类，用于处理与Gemini模型的图像生成对话
class MultiTurnImageChat:
    def __init__(self):
        # 初始化Gemini客户端
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            # http_options={"base_url": "https://gemini.iorpa.xyz"}
        )
        # 设置使用的模型名称
        self.model = "gemini-2.0-flash-exp-image-generation"
        # 初始化对话历史和文件列表
        self.conversation_history: List[types.Content] = []
        self.files = []
        
    def upload_image(self, image_path: str) -> None:
        """上传新图片到对话"""
        # 上传图片文件并保存到文件列表中
        file = self.client.files.upload(file=image_path)
        self.files.append(file)
    
    def _process_model_response_async(self, data: bytes, mime_type: str, output_filename: str) -> None:
        """异步处理模型响应：上传图片并更新对话历史"""
        try:
            # 上传保存的图片文件并添加到文件列表
            file = self.client.files.upload(file=output_filename)
            self.files.append(file)
            
            # 将模型生成的图片响应添加到对话历史
            self.conversation_history.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_uri(
                            file_uri=file.uri,
                            mime_type=mime_type,
                        )
                    ]
                )
            )
            print(f"图片已上传并添加到对话历史")
        except Exception as e:
            print(f"处理模型响应时出错: {e}")
        
    def add_user_message(self, text: str, image_uri: Optional[str] = None) -> None:
        """添加用户消息到对话历史"""
        # 创建消息部件列表
        parts = []
        if image_uri:
            # 如果提供了图片URI，添加图片部件
            parts.append(
                types.Part.from_uri(
                    file_uri=image_uri,
                    mime_type=self.files[-1].mime_type,
                )
            )
        # 添加文本部件
        parts.append(types.Part.from_text(text=text))
        
        # 将用户消息添加到对话历史
        self.conversation_history.append(
            types.Content(
                role="user",
                parts=parts
            )
        )
        
    def add_model_response(self, data: bytes, mime_type: str, output_filename: str) -> None:
        """添加模型响应到对话历史"""
        # 保存生成的图片到本地
        save_binary_file(output_filename, data)
        
        # 立即返回路径给用户
        print(f"File saved to: {output_filename} (type: {mime_type})")
        
        # 创建新线程异步处理上传和保存对话历史
        thread = threading.Thread(
            target=self._process_model_response_async,
            args=(data, mime_type, output_filename)
        )
        thread.daemon = True  # 设置为守护线程，主线程结束时自动结束
        thread.start()

    def print_conversation_history(self) -> None:
        """打印当前对话历史的内容"""
        print(str(self.conversation_history))
        print("\n===== 对话历史内容 =====")
        for i, content in enumerate(self.conversation_history):
            print(f"[消息 {i+1}] 角色: {content.role}")
            for j, part in enumerate(content.parts):
                if hasattr(part, 'text') and part.text:
                    print(f"  - 文本: {part.text}")
                elif hasattr(part, 'inline_data') and part.inline_data:
                    print(f"  - 内联图片: {part.inline_data.mime_type}")
                elif hasattr(part, 'file_uri') and part.file_uri:
                    print(f"  - 文件URI: {part.file_uri}")
        print("========================\n")

    def generate(self, output_filename: str) -> None:
        """生成响应并保存结果"""
        # 配置生成参数
        config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_modalities=["image", "text"],
            response_mime_type="text/plain",
        )

        # 流式生成内容
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=self.conversation_history,
            config=config,
        ):
            # 跳过无效的响应块
            if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                continue
                
            if chunk.candidates[0].content.parts[0].inline_data:
                image_data = chunk.candidates[0].content.parts[0].inline_data.data
                mime_type = chunk.candidates[0].content.parts[0].inline_data.mime_type
                
                # 添加模型响应（包括保存、上传图片并更新对话历史）
                self.add_model_response(image_data, mime_type, output_filename)
            else:
                # 打印文本响应
                print(chunk.text)


# 主函数，展示多轮对话的使用示例
def main():
    # 创建多轮对话实例
    chat = MultiTurnImageChat()
    
    # 第一轮对话：上传图片并移除文字
    chat.upload_image("美容液.jpg")
    chat.add_user_message("请帮我去除图片中的所有文字", chat.files[0].uri)
    chat.generate("output_1.jpg")
    
    # 第二轮对话：添加白色手套
    chat.add_user_message("请给图片中模特的手带上白色皮手套")
    chat.generate("output_2.jpg")
    
    # 可以继续添加更多轮次的对话...

if __name__ == "__main__":
    main()