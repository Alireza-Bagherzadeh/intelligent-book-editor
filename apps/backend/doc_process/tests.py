from django.test import TestCase

# Create your tests here.


import os
from google import genai
from dotenv import load_dotenv

# بارگذاری کلید API از فایل .env
load_dotenv()

# مقداردهی کلاینت با استفاده از SDK جدید
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("لیست مدل‌های در دسترس:")
print("-" * 50)

try:
    # دریافت و چاپ لیست تمامی مدل‌ها
    for model in client.models.list():
        print(f"Name:  {model.name}")
        print(f"Display Name: {model.display_name}")
        print(f"Description:  {model.description}")
        print("-" * 50)
        
except Exception as e:
    print(f"خطا در ارتباط با API و دریافت لیست: {e}")