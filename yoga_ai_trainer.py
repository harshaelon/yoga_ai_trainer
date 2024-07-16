import cv2
import base64
import os
import openai
import requests
import streamlit as st 
import tempfile

from moviepy.editor import VideoFileClip,AudioFileClip



def generate_base64_frame(video):



    with tempfile.NamedTemporaryFile(delete=False,suffix=".mp4") as tmpfile:
        tmpfile.write(video.read())
    
        video_filename=tmpfile.name
    
    
    video_duration=VideoFileClip(video_filename).duration
    
    
    video= cv2.VideoCapture(video_filename)

    #convert video into its frames
    base64Frames=[]

    while video.isOpened():
        success,frame=video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg",frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
    video.release()

    return video_duration, video_filename, base64Frames

API_KEY = ""
def generate_voiceover(text):
    response=requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model":"tts-1-hd",
            "input":text,
            "voice":"onyx",
        },
    )

    audio= b""
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        audio+=chunk
    with open("output_audio.mp3","wb") as file:
        file.write(audio)

    return file.name    
    



# sending frames to openAI
openai.api_key = ""
def generate_voiceover_text(frames,video_duration):
    
    
    chat_completion=openai.chat.completions.create(
        model="gpt-4o",
        max_tokens=200,
        messages=[
            {
                "role":"user",
                "content":[
                    f"as a yoga Instructor, could you provide specific tips based on these video frames to enhance the yoga posture? please dont include personal any personal information. Ensure the voice-over script is concise, using no more than {video_duration*2} words, to fit within the {video_duration}-second video duration.",
                    * [{"image":x,"resize":512}for x in frames[0::30]]
                ],
            }
        ]
    )

    result=chat_completion.choices[0].message.content
    print(result)
    return result


def merge_audio_file(video_filename, audio_filename):
    video_clip=VideoFileClip(video_filename)
    audio_clip=AudioFileClip(audio_filename)


    final_clip=video_clip.set_audio(audio_clip)
    final_clip.write_videofile(
        'merged.mp4',codec='libx264',audio_codec='aac'
    )

    video_clip.close()
    audio_clip.close()

    return 'merged.mp4'


def main():
    st.header('Analyze yoga Posture')
    uploaded_file=st.file_uploader("chose a file")

    if uploaded_file is not None:
        st.video(uploaded_file)

    if st.button('Run',type="primary") and uploaded_file is not None:
        with st.spinner('Running.....'):
            video_duration , video_filename ,frames=generate_base64_frame(uploaded_file)
            text=generate_voiceover_text(frames,video_duration)

            #text2=generate_voiceover_generation(frames,video_duration)

            st.write(text)
            audiofile=generate_voiceover(text)


            final_video_filename=merge_audio_file(
                video_filename,audiofile
            )

            st.video(final_video_filename)

            #st.write(text2)




if __name__=='__main__':
    main()