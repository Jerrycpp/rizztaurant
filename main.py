import streamlit as st
import geminilive
import time
from streamlit_mic_recorder import mic_recorder
from streamlit_geolocation import streamlit_geolocation
from pydub import AudioSegment
import io
import route_gen
from evaluator import *

INPUT_AUDIO = 'audio/input.wav'
OUTPUT_AUDIO = 'audio/output.wav'
GREETING_AUDIO = 'audio/greeting.wav'
REVIEW_REQUEST_AUDIO = 'audio/request.wav'
THANKYOU_AUDIO = 'audio/thankyou.wav'
chatbot = geminilive.GeminiLiveAudio(INPUT_AUDIO, OUTPUT_AUDIO)




if 'prog_state' not in st.session_state:
    st.session_state['prog_state'] = 1

if 'destination' not in st.session_state:
    st.session_state['destination'] = 'None'


elif st.session_state['prog_state'] == 1:
    st.audio(GREETING_AUDIO, autoplay=True)
    
    st.session_state['prog_state'] = 2

    
elif st.session_state['prog_state'] == 2:
    audio_value = mic_recorder("⏺️", "⏹️", just_once=False, use_container_width=False, format='wav')
    if audio_value is not None:
        # print(type(audio_value))
        # print(audio_value.keys())
        bytes = audio_value['bytes']
        sample_width = audio_value['sample_width']
        sample_rate = audio_value['sample_rate']
        audio_value = AudioSegment.from_raw( io.BytesIO(bytes), sample_width=sample_width, frame_rate=sample_rate, channels=1).export(INPUT_AUDIO, format="wav")
        st.session_state['prog_state'] = 3

elif st.session_state['prog_state'] == 3:
    chatbot.transcribe_audio(INPUT_AUDIO)
    chatbot.food_type_generate()
    location = streamlit_geolocation()
    print(location)
    if location['latitude'] != None and location['longitude'] != None:
        # st.write(f"{location}")
        scraper = RestaurantScraper(lat=location['latitude'], lng=location['longitude'])
        scraper.run()
        scraper.get_best_restaurant('ramen')
        destination_name = scraper.best_restaurants[0]["name"]
        route = route_gen.WalkingRoute(location['latitude'], location['longitude'], destination_name)
        route.fetch_route()
        route.display_route()
        st.html("polyline_map.html")
        st.session_state['destination'] = destination_name
        st.session_state['prog_state'] = 4
    else:
        st.write("Waiting for you to press the button...")
        st.session_state['prog_state'] = 3


elif st.session_state['prog_state'] == 4:
    chatbot.run_introduction('Arlington', st.session_state['destination'])
    st.audio(OUTPUT_AUDIO, autoplay=True)
    st.session_state['prog_state'] = 5


elif st.session_state['prog_state'] == 5:
    if st.button("Tap this button if you have finished your meal!"):
        st.audio(REVIEW_REQUEST_AUDIO, autoplay=True)
        review = mic_recorder("⏺️", "⏹️", just_once=False, use_container_width=False, format='wav')
        if review is not None:
        # print(type(audio_value))
        # print(audio_value.keys())
            bytes = review['bytes']
            sample_width = review['sample_width']
            sample_rate = review['sample_rate']
            audio_value = AudioSegment.from_raw( io.BytesIO(bytes), sample_width=sample_width, frame_rate=sample_rate, channels=1).export(INPUT_AUDIO, format="wav")
        st.session_state['prog_state'] = 6

elif st.session_state['prog_state'] == 6:
    st.audio(THANKYOU_AUDIO, 'audio/wav', autoplay=True)
    st.session_state['prog_state'] = 1



if st.button("Next"):
    st.empty()


        
    

# if 'init' not in st.session_state:
#     st.audio(greetingFileAudio, autoplay=True)
#     st.session_state['init'] = 1



# if st.button('User input'):
#     audio_value = st.audio_input("Recording...", key='userInputAudio')
#     if audio_value:
#         with open(userInput, 'wb') as f:
#             f.write(audio_value.getbuffer())
#             st.write("Recorded successfilly")

# st.write("Sth sth")


