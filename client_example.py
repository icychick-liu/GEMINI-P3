import requests

def generate_image(
    prompt: str,
    topic_id: str,
    image_paths: List[str] = None,
    api_url: str = "http://127.0.0.1:8000/generate-image"
):
    # 准备数据
    files = []
    if image_paths:
        files = [
            ('files', (f'image_{i}.jpg', open(image_path, 'rb'), 'image/jpeg'))
            for i, image_path in enumerate(image_paths)
        ]
    
    data = {
        'prompt': prompt,
        'topic_id': topic_id
    }
    
    # 发送请求
    try:
        response = requests.post(api_url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
                
            print(f"图片URL: {result['image_url']}")
            print(f"话题ID: {result['topic_id']}")
            return result
        else:
            print(f"错误状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    # 第一轮对话：上传多张初始图片
    result = generate_image(
        prompt="调换一下这两张图片中的小狗的角色，以第一张图片为输出图片",
        topic_id="topic_20250321_082256",
        image_paths=["炒锅.jpg", "女模特.jpg"]
    )
