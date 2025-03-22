import requests

def generate_image(
    prompt: str,
    topic_id: str,
    image_path: str = None,
    api_url: str = "http://127.0.0.1:8000/generate-image"
):
    # 准备数据
    files = {}
    if image_path:
        files = {
            'file': ('image.jpg', open(image_path, 'rb'), 'image/jpeg')
        }
    
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
    # 第一轮对话：上传初始图片
    result = generate_image(
        prompt="还是把围巾颜色换成黄色吧",
        topic_id="topic_20250321_082250",
        # image_path="dog11.jpg"
    )
