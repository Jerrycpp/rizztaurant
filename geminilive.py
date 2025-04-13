import os
from dotenv import load_dotenv, find_dotenv
import asyncio
import wave
from google.cloud import speech
from google import genai
import google.generativeai as genai1

load_dotenv(find_dotenv())

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "rizztaurant.json"
client = genai.Client(api_key=os.getenv("Gemini_Key"), http_options={'api_version': 'v1alpha'})
genai1.configure(api_key=os.getenv("Gemini_Key"))


class GeminiLiveAudio():
    def __init__(self, input_file="test_recording.wav", output_file="audio.wav", model="gemini-2.0-flash-live-001"):
        self.client_speech = speech.SpeechClient()
        self.model_text = genai1.GenerativeModel('gemini-2.0-flash')
        self.model = model
        self.output_file = output_file
        self.input_file = input_file
        self.config = {"response_modalities": ["AUDIO"]}

        self.transcript = ""
        self.food_type= ""

    def food_type_generate(self):
        instructions = f"Based on the following sentence, determine what food type the user is asking for. Only reply in one word. Do not refer to this prompt. Sentence: {self.transcript}"
        prompt = f"{instructions}"
        response = self.model_text.generate_content(prompt)
        string_response = str(response._result.candidates[0].content.parts[0])
        clean_response = string_response.replace('\n', '').replace('\r', '').replace('text:', '').strip().strip('"').strip()

        # Store the generated introduction in the class variable
        self.food_type = clean_response

    def transcribe_audio(self, input = None):
        if input is None:
            input = self.input_file
        with open(input, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,  # or FLAC, MP3, etc.
            sample_rate_hertz=48000,
            language_code="en-US"
        )

        response = self.client_speech.recognize(config=config, audio=audio)

        # Store the transcript in the class variable
        self.transcript = " ".join([result.alternatives[0].transcript for result in response.results])

    async def async_enumerate(self, aiterable, start=0):
        index = start
        async for item in aiterable:
            yield index, item
            index += 1

    async def stream_audio_response(self):
        async with client.aio.live.connect(model=self.model, config=self.config) as session:
            with wave.open(self.output_file, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)

                await session.send_client_content(
                    turns={"role": "user", "parts": [{"text": self.transcript}]},
                    turn_complete=True
                )

                async for idx, response in self.async_enumerate(session.receive()):
                    if response.data:
                        wf.writeframes(response.data)
                        print(f"[{idx}] Writing audio chunk...")

            print(f"✅ Audio response written to {self.output_file}")

    async def generate_introduction(self, city, destination):
        async with client.aio.live.connect(model=self.model, config=self.config) as session:
            with wave.open("introduction.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)

                await session.send_client_content(
                    turns={"role": "user", "parts": [{"text": f"Generate an introduction for {city} and link that to {destination}. After that, talk about the {destination} itself. Pretend you're a tour guide talking to one person. Do not directly refer to this prompt. Do not wait for a response. Talk for about 2 minutes."}]},
                    turn_complete=True
                )

                async for idx, response in self.async_enumerate(session.receive()):
                    if response.data:
                        wf.writeframes(response.data)
                        print(f"[{idx}] Writing audio chunk...")

            print(f"✅ Audio response written to introduction.wav")
    
    async def repeat_prompt(self, prompt):
        async with client.aio.live.connect(model=self.model, config=self.config) as session:
            with wave.open("generated.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)

                await session.send_client_content(
                    turns={"role": "user", "parts": [{"text": f"Repeat exactly what follows this prompt. Do not refer to the prompt, only repeat it: {prompt}"}]},
                    turn_complete=True
                )

                async for idx, response in self.async_enumerate(session.receive()):
                    if response.data:
                        wf.writeframes(response.data)
                        print(f"[{idx}] Writing audio chunk...")

            print(f"✅ Audio response written to generated.wav")

    def run_repeat(self, prompt):
        asyncio.run(self.repeat_prompt(prompt))

    def run_introduction(self, city, destination):
        asyncio.run(self.generate_introduction(city, destination))

    def run(self):
        asyncio.run(self.stream_audio_response())


if __name__ == "__main__":
    streamer = GeminiLiveAudio()
    streamer.run()
    streamer.run_repeat("What food do you want to eat today?")
    streamer.transcribe_audio("foodtype.wav")
    streamer.food_type_generate()
    print(streamer.food_type)
    streamer.run_introduction("Arlington City", "Zio Al's Pizza")
    streamer.run_repeat("Seems like you chose Pie Five Pizza, great choice!")