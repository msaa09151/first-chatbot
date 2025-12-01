import streamlit as st
import PyPDF2
from openai import AzureOpenAI
import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import requests

# 1. 환경 변수 로드 (.env 파일 필요)
load_dotenv()

search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_key = os.getenv("SEARCH_KEY")
search_index = os.getenv("SEARCH_INDEX_NAME")

semantic_configuration = "healthy-eating-habits-data1-semantic-configuration"
query_type = "vector_semantic_hybrid"
OPENWEATHER_API_KEY = "33e5c255ce70fe7a48ba4665e5944b81"


# 2. Azure OpenAI 클라이언트 설정
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
    api_version="2025-01-01-preview",  # 최신 버전
)

# 페이지 설정
st.set_page_config(
    page_title="HealthWeather 🌤️",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS로 부드러운 디자인 적용
st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp {
        background: #fafafa;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: #f5f5f5;
        padding-top: 20px;
    }
    
    /* 사이드바 헤더 */
    [data-testid="stSidebar"] h3 {
        color: #424242;
        font-weight: 600;
        padding: 10px 0;
    }
    
    /* 사이드바 텍스트 */
    [data-testid="stSidebar"] p {
        color: #757575;
        font-size: 14px;
    }
    
    /* 메인 타이틀 */
    h1 {
        color: #424242;
        font-weight: 700;
        text-align: center;
        padding: 30px 20px 10px 20px;
    }
    
    /* 채팅 메시지 */
    .stChatMessage {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    /* 입력창 */
    .stChatInput {
        border-radius: 20px;
        border: 1px solid #e0e0e0;
    }
    
    /* 버튼 */
    .stButton button {
        background: #90caf9;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 24px;
        font-weight: 500;
        transition: all 0.2s;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    
    .stButton button:hover {
        background: #64b5f6;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }
    
    /* 성공 메시지 */
    .stSuccess {
        background: #e8f5e9;
        color: #2e7d32;
        border-radius: 10px;
        padding: 12px;
        border-left: 4px solid #66bb6a;
    }
    
    /* 정보 박스 */
    .stInfo {
        background: #e3f2fd;
        color: #1565c0;
        border-radius: 10px;
        padding: 12px;
        border-left: 4px solid #64b5f6;
    }
    
    /* 경고 메시지 */
    .stWarning {
        background: #fff3e0;
        color: #e65100;
        border-radius: 10px;
        padding: 12px;
        border-left: 4px solid #ff9800;
    }
    
    /* 파일 업로더 */
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 10px;
        padding: 15px;
        border: 1px dashed #bdbdbd;
    }
    
    /* 텍스트 입력 */
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 10px;
        background: white;
    }
    
    .stTextInput input:focus {
        border-color: #90caf9;
        box-shadow: 0 0 0 1px #90caf9;
    }
    
    /* 텍스트 입력 라벨 */
    .stTextInput label {
        color: #616161;
        font-size: 14px;
        font-weight: 500;
    }
    
    /* 구분선 */
    hr {
        border: none;
        height: 1px;
        background: #e0e0e0;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------- 
# 1. 세션 상태 초기화 
# ---------------------------- 
if "messages" not in st.session_state: 
    st.session_state.messages = [] 
 
if "pdf_text" not in st.session_state: 
    st.session_state.pdf_text = "" 

if "weather_info" not in st.session_state:
    st.session_state.weather_info = ""

if "selected_city" not in st.session_state:
    st.session_state.selected_city = ""


# ----------------------------
# 날씨 정보 가져오기 함수
# ----------------------------
def get_weather(city_name):
    """OpenWeatherMap API를 사용하여 날씨 정보 가져오기"""
    try:
        # 한글 도시명을 영어로 변환하는 사전 (주요 도시 + 소도시)
        city_translation = {
            "서울": "Seoul", "부산": "Busan", "인천": "Incheon", "대구": "Daegu",
            "대전": "Daejeon", "광주": "Gwangju", "울산": "Ulsan", "수원": "Suwon",
            "창원": "Changwon", "고양": "Goyang", "용인": "Yongin", "성남": "Seongnam",
            "청주": "Cheongju", "전주": "Jeonju", "천안": "Cheonan", "안산": "Ansan",
            "안양": "Anyang", "포항": "Pohang", "제주": "Jeju", "평택": "Pyeongtaek",
            "시흥": "Siheung", "김해": "Gimhae", "파주": "Paju", "의정부": "Uijeongbu",
            "광명": "Gwangmyeong", "구리": "Guri", "남양주": "Namyangju", "양산": "Yangsan",
            "춘천": "Chuncheon", "원주": "Wonju", "강릉": "Gangneung", "속초": "Sokcho",
            "충주": "Chungju", "제천": "Jecheon", "아산": "Asan", "서산": "Seosan",
            "당진": "Dangjin", "논산": "Nonsan", "계룡": "Gyeryong", "공주": "Gongju",
            "보령": "Boryeong", "익산": "Iksan", "군산": "Gunsan", "정읍": "Jeongeup",
            "남원": "Namwon", "김제": "Gimje", "목포": "Mokpo", "여수": "Yeosu",
            "순천": "Suncheon", "광양": "Gwangyang", "나주": "Naju", "경주": "Gyeongju",
            "김천": "Gimcheon", "안동": "Andong", "구미": "Gumi", "영주": "Yeongju",
            "영천": "Yeongcheon", "상주": "Sangju", "문경": "Mungyeong", "경산": "Gyeongsan",
            "통영": "Tongyeong", "사천": "Sacheon", "밀양": "Miryang", "거제": "Geoje",
            "진주": "Jinju", "동해": "Donghae", "태백": "Taebaek", "삼척": "Samcheok",
            "양평": "Yangpyeong", "이천": "Icheon", "안성": "Anseong", "김포": "Gimpo",
            "화성": "Hwaseong", "오산": "Osan", "광주시": "Gwangju", "하남": "Hanam",
            "여주": "Yeoju", "양주": "Yangju", "동두천": "Dongducheon", "과천": "Gwacheon",
            "의왕": "Uiwang", "군포": "Gunpo", "안양시": "Anyang", "화천": "Hwacheon",
            "양구": "Yanggu", "인제": "Inje", "고성": "Goseong", "홍천": "Hongcheon",
            "횡성": "Hoengseong", "평창": "Pyeongchang", "정선": "Jeongseon", "영월": "Yeongwol",
            "태안": "Taean", "홍성": "Hongseong", "예산": "Yesan", "청양": "Cheongyang",
            "부여": "Buyeo", "서천": "Seocheon", "금산": "Geumsan", "옥천": "Okcheon",
            "영동": "Yeongdong", "진천": "Jincheon", "괴산": "Goesan", "음성": "Eumseong",
            "단양": "Danyang", "증평": "Jeungpyeong", "완주": "Wanju", "진안": "Jinan",
            "무주": "Muju", "장수": "Jangsu", "임실": "Imsil", "순창": "Sunchang",
            "고창": "Gochang", "부안": "Buan", "담양": "Damyang", "곡성": "Gokseong",
            "구례": "Gurye", "고흥": "Goheung", "보성": "Boseong", "화순": "Hwasun",
            "장흥": "Jangheung", "강진": "Gangjin", "해남": "Haenam", "영암": "Yeongam",
            "무안": "Muan", "함평": "Hampyeong", "영광": "Yeonggwang", "장성": "Jangseong"
        }
        
        # 한글이면 영어로 변환
        search_city = city_translation.get(city_name, city_name)
        
        # 1차 시도: 한국으로 제한해서 검색
        url = f"http://api.openweathermap.org/data/2.5/weather?q={search_city},KR&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url, timeout=10)
        
        # 1차 실패시 2차 시도: 국가 코드 없이 검색
        if response.status_code != 200:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={search_city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"
            response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            city_actual = data['name']
            
            weather_text = (
                f"📍 {city_actual} 날씨 정보\n"
                f"🌡️ 현재 온도: {temp}°C (체감온도: {feels_like}°C)\n"
                f"☁️ 날씨: {weather_desc}\n"
                f"💧 습도: {humidity}%\n"
                f"🌬️ 풍속: {wind_speed} m/s"
            )
            return weather_text
        elif response.status_code == 401:
            return f"❌ API 키가 유효하지 않습니다. OPENWEATHER_API_KEY를 확인해주세요."
        else:
            return f"❌ '{city_name}' 도시의 날씨 정보를 찾을 수 없습니다.\n💡 영어로 입력해보세요 (예: Seoul, Busan)"
            
    except Exception as e:
        return f"⚠️ 날씨 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"


# ---------------------------- 
# 2. 사이드바: PDF 업로드 & 도시 입력
# ---------------------------- 
with st.sidebar:
    st.markdown("### 📄 문서 업로드")
    
    uploaded_file = st.file_uploader(
        "건강 관련 문서를 올려주세요",
        type=["pdf"],
        help="건강검진 결과, 운동 가이드 등 참고를 원하는 문서 업로드"
    ) 
 
    if uploaded_file is not None: 
        pdf_reader = PyPDF2.PdfReader(uploaded_file) 
        extracted_text = "" 
 
        for page in pdf_reader.pages: 
            extracted_text += page.extract_text() + "\n" 
 
        st.session_state.pdf_text = extracted_text 
        st.success("PDF 불러오기 완료") 
    
    st.markdown("---")
    
    # 날씨 정보 입력
    st.markdown("### 🌤 오늘의 날씨")
    
    city_input = st.text_input(
        "도시명 입력",
        placeholder="예: 서울, 부산, 춘천",
        label_visibility="collapsed"
    )
    
    if st.button("날씨 확인", use_container_width=True):
        if city_input:
            with st.spinner("날씨 정보 가져오는 중..."):
                weather_result = get_weather(city_input)
                st.session_state.weather_info = weather_result
                st.session_state.selected_city = city_input
        else:
            st.warning("도시명을 입력해주세요")
    
    # 현재 저장된 날씨 정보 표시
    if st.session_state.weather_info:
        st.success("날씨 정보 저장 완료")
        st.info(st.session_state.weather_info)
        
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; padding: 15px; background: white; border-radius: 10px;'>
            <p style='color: #757575; font-size: 13px; margin: 0; line-height: 1.5;'>
                💡 날씨에 맞는 건강 관리 팁을<br>AI가 자동으로 추천해드려요
            </p>
        </div>
    """, unsafe_allow_html=True)


# 메인 헤더
st.markdown("""
    <h1>
        🌤️ HealthWeather Assistant 💚
    </h1>
    <p style='text-align: center; color: #2e7d32; font-size: 18px; margin-bottom: 30px;'>
        날씨가 변하면, 건강관리도 변해요! 함께 건강한 하루 만들어봐요 😊
    </p>
""", unsafe_allow_html=True)

# ---------------------------- 
# 3. 기존 대화 출력 
# ---------------------------- 
for message in st.session_state.messages: 
    with st.chat_message(message["role"]): 
        st.markdown(message["content"]) 


# ---------------------------- 
# 4. 사용자 입력 
# ---------------------------- 
if prompt := st.chat_input("💬 무엇을 도와드릴까요? (예: 오늘 날씨에 어울리는 식단 추천해줘)"): 
 
    # 사용자 메시지 저장 
    st.chat_message("user").markdown(prompt) 
    st.session_state.messages.append({"role": "user", "content": prompt}) 
 
    # ---------------------------- 
    # 5. AI 응답 생성 
    # ---------------------------- 
    # 시스템 메시지 구성
    system_instructions = []
    
    # 페르소나 및 말투 설정 (항상 포함)
    system_instructions.append(
        """당신은 친근하고 따뜻한 건강 관리 도우미입니다. 
        
말투 가이드라인:
- 이모지를 적극 활용해서 대화를 생동감 있게 만드세요 (😊, 💪, 🥗, ☀️, 🌧️ 등)
- 존댓말을 사용하되, 부드럽고 친근한 톤으로 대화하세요
- "~네요", "~드려요", "~해요" 같은 둥근 말투를 사용하세요
- 딱딱한 설명보다는 공감하고 격려하는 표현을 사용하세요
- 예시: "오늘 날씨가 정말 좋네요! ☀️", "수고하셨어요! 💪", "함께 건강 관리해봐요! 😊"

응답 스타일:
- 답변 시작에 상황에 맞는 이모지 사용
- 리스트 형태로 정보를 제공할 때도 각 항목에 이모지 추가
- 긍정적이고 응원하는 메시지 포함
- 전문적이지만 어렵지 않은 용어 사용"""
    )
    
    # PDF 내용 추가
    if st.session_state.pdf_text: 
        system_instructions.append(
            "\n\n아래는 사용자가 업로드한 PDF 파일의 내용입니다. "
            "이 내용을 참고하여 질문에 답변하세요.\n\n"
            f"PDF 내용:\n{st.session_state.pdf_text}"
        )
    
    # 날씨 정보 추가
    if st.session_state.weather_info:
        system_instructions.append(
            f"\n\n현재 사용자가 선택한 도시({st.session_state.selected_city})의 날씨 정보입니다. "
            "날씨 관련 질문이 있을 때 이 정보를 자연스럽게 활용하여 답변하세요.\n\n"
            f"{st.session_state.weather_info}"
        )
    
    pdf_instruction = "\n".join(system_instructions)
 
    with st.chat_message("assistant"): 
        response = client.chat.completions.create( 
            model="gpt-4o-mini",   
            messages=[ 
                {"role": "system", "content": pdf_instruction}, 
                *[ 
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages 
                ] 
            ], 
            max_tokens=6553, 
            temperature=0.7, 
            top_p=0.95, 
            frequency_penalty=0, 
            presence_penalty=0, 
            extra_body={ 
                "data_sources": [{ 
                    "type": "azure_search", 
                    "parameters": { 
                        "endpoint": f"{search_endpoint}", 
                        "index_name": search_index, 
                        "semantic_configuration": semantic_configuration, 
                        "query_type": query_type, 
                        "fields_mapping": {}, 
                        "in_scope": True, 
                        "filter": None, 
                        "strictness": 3, 
                        "top_n_documents": 5, 
                        "authentication": { 
                            "type": "api_key", 
                            "key": f"{search_key}" 
                        }, 
                        "embedding_dependency": { 
                            "type": "deployment_name", 
                            "deployment_name": "text-embedding-ada-002" 
                        } 
                    } 
                }] 
            } 
        ) 
 
        assistant_reply = response.choices[0].message.content
        
        # RAG 출처 정보 추출
        citations = []
        if hasattr(response.choices[0].message, 'context'):
            context = response.choices[0].message.context
            if context and 'citations' in context:
                citations = context['citations']
        
        # 답변 표시
        st.markdown(assistant_reply)
        
        # 출처 정보가 있으면 표시
        if citations:
            st.markdown("---")
            st.markdown("### 📚 참고 문서")
            for idx, citation in enumerate(citations, 1):
                title = citation.get('title', '제목 없음')
                filepath = citation.get('filepath', citation.get('url', ''))
                content_snippet = citation.get('content', '')
                
                with st.expander(f"📄 {idx}. {title}", expanded=False):
                    if filepath:
                        st.markdown(f"**경로**: `{filepath}`")
                    if content_snippet:
                        st.markdown(f"**내용 미리보기**:")
                        st.markdown(f"> {content_snippet[:200]}...")
        elif st.session_state.pdf_text:
            # PDF 업로드 내용을 참고한 경우
            st.markdown("---")
            st.markdown("💡 *업로드하신 PDF 문서를 참고했어요!*")
        
        # 날씨 정보를 사용한 경우 표시
        if st.session_state.weather_info and any(word in prompt.lower() for word in ['날씨', '기온', '온도', '추워', '더워', '비', '눈']):
            st.markdown(f"🌤️ *{st.session_state.selected_city} 날씨 정보를 참고했어요!*") 
 
    # AI 응답 저장 (출처 정보는 저장하지 않음, 답변만 저장)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

