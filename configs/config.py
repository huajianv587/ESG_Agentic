
import os 
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY','')

        #AWS
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID','')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY','')

        #DeepSeek
        self.DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY','')

        #Supabase
        self.SUPABASE_URL = os.getenv('SUPABASE_URL','')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY','')
        self.SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD','')
        self.DEBUG = True

   