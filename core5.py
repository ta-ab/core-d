import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import fitz  # PyMuPDF for PDF
import docx
import numpy as np
import matplotlib.pyplot as plt

# .env の読み込み
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini API の設定
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# マスコット画像の表示
st.image("mascot.jpg", width=150)

# タイトル
st.title("📚 コア博士 ボット")

# 会話履歴の初期化
if "history" not in st.session_state:
    st.session_state.history = []

# ユーザーの名前を聞く
if "username" not in st.session_state:
    username = st.text_input("あなたの名前を入力してください:")
    if username:
        st.session_state.username = username
        st.success(f"こんにちは、{username}さん！")
        st.rerun()

# 📂 ファイルの読み込み
def load_files_from_folder(folder_path):
    text_data = ""
    if not os.path.exists(folder_path):
        return None
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        try:
            if file_name.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as file:
                    text_data += file.read() + "\n\n"
            elif file_name.endswith(".pdf"):
                doc = fitz.open(file_path)
                for page in doc:
                    text_data += page.get_text() + "\n\n"
            elif file_name.endswith(".docx"):
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text_data += para.text + "\n\n"
        except Exception as e:
            text_data += f"\n❌ エラー: {file_name} を読み込めませんでした。\n"
    
    return text_data if text_data.strip() else None

# データフォルダのパス
data_folder = "data"
file_content = load_files_from_folder(data_folder)

# 会話履歴の表示
for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)

# ユーザーの入力
user_input = st.chat_input("質問を入力してください:")

if user_input and "username" in st.session_state:
    username = st.session_state.username
    chat_history = "\n".join([msg for _, msg in st.session_state.history[-5:]])  # 直近5件のみ使用

    if file_content:
        # **フォルダ内の情報をもとに回答**
        prompt = f"""
        これまでの会話履歴（直近のみ）:
        {chat_history}
        
        フォルダ内の情報:
        {file_content}
        
        ユーザーの名前は {username} さんです。
        必ず回答の中で「{username} さん」と呼びかけてください。
        
        ユーザーの質問:
        {user_input}
        
        **指示**
        - フォルダの情報を優先して回答してください。
        - 関連する情報があれば、それをもとに詳細を説明してください。
        - 不明な場合は、「一般的な知識」を使って説明してください。
        """
    else:
        # **ファイルがない場合も、できる限り回答する**
        prompt = f"""
        これまでの会話履歴（直近のみ）:
        {chat_history}
        
        ユーザーの名前は {username} さんです。
        必ず回答の中で「{username} さん」と呼びかけてください。
        
        ユーザーの質問:
        {user_input}
        
        **指示**
        - AI の知識を使って、できる限り詳しく説明してください。
        - 推測でもいいので、関連しそうな情報を提供してください。
        - 不明な場合でも、何か関連する話題を提供してください（完全に無関係でない限り）。
        """
    
    response = model.generate_content(prompt)
    reply = response.text.strip()
    
    # 会話履歴を更新
    st.session_state.history.append(("user", user_input))
    st.session_state.history.append(("assistant", reply))

    # 会話の表示
    with st.chat_message("user"):
        st.write(user_input)
    with st.chat_message("assistant"):
        st.write(reply)

    # 数値データが含まれる場合、グラフを作成
    try:
        numbers = [float(num) for num in reply.split() if num.replace('.', '', 1).isdigit()]
        if len(numbers) > 1:
            fig, ax = plt.subplots()
            ax.plot(np.arange(len(numbers)), numbers, marker='o', linestyle='-')
            st.pyplot(fig)
    except ValueError:
        pass