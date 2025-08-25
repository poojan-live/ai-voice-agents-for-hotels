
import asyncio, os
from videosdk.agents import Agent, AgentSession, CascadingPipeline, JobContext, RoomOptions, WorkerJob,ConversationFlow
from videosdk.plugins.silero import SileroVAD
from videosdk.plugins.turn_detector import TurnDetector, pre_download_model
from videosdk.plugins.deepgram import DeepgramSTT
from videosdk.plugins.openai import OpenAILLM
from videosdk.plugins.elevenlabs import ElevenLabsTTS
from typing import AsyncIterator

# Pre-downloading the Turn Detector model
pre_download_model()

class MyVoiceAgent(Agent):
    def __init__(self):
        super().__init__(instructions="""You are a courteous and knowledgeable AI voice agent specializing in hotel services. Your primary role is to assist guests and potential customers with reservations, provide information about hotel amenities, answer questions about availability, rates, and policies, and address common guest requests such as room service, wake-up calls, and local recommendations. You should guide callers through the booking process, handle special requests, and direct them to the appropriate department or staff member for complex issues. Always maintain a warm, welcoming, and professional tone, ensuring each interaction is clear, efficient, and tailored to the guest’s needs. Be proactive in offering helpful suggestions, knowledgeable about all aspects of the hotel—including check-in/out procedures, dining options, facilities, and local attractions—and ensure privacy and security by not handling sensitive payment information directly, instead guiding guests to secure payment portals or connecting them to authorized staff when necessary.""")
    async def on_enter(self): await self.session.say("Hello! How can I help you today regarding ai voice agents for hotels?")
    async def on_exit(self): await self.session.say("Goodbye!")

async def start_session(context: JobContext):
    # Create agent and conversation flow
    agent = MyVoiceAgent()
    conversation_flow = ConversationFlow(agent)

    # Create pipeline
    pipeline = CascadingPipeline(
        stt=DeepgramSTT(model="nova-2", language="en"),
        llm=OpenAILLM(model="gpt-4o"),
        tts=ElevenLabsTTS(model="eleven_flash_v2_5"),
        vad=SileroVAD(threshold=0.35),
        turn_detector=TurnDetector(threshold=0.8)
    )

    session = AgentSession(
        agent=agent,
        pipeline=pipeline,
        conversation_flow=conversation_flow
    )

    try:
        await context.connect()
        await session.start()
        # Keep the session running until manually terminated
        await asyncio.Event().wait()
    finally:
        # Clean up resources when done
        await session.close()
        await context.shutdown()

def make_context() -> JobContext:
    room_options = RoomOptions(
     #  room_id="YOUR_MEETING_ID",  # Set to join a pre-created room; omit to auto-create
        name="VideoSDK Cascaded Agent for ai voice agents for hotels",
        playground=True
    )

    return JobContext(room_options=room_options)

if __name__ == "__main__":
    job = WorkerJob(entrypoint=start_session, jobctx=make_context)
    job.start()
