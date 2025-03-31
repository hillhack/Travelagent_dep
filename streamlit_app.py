import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HUGGING_API_KEY = os.getenv("HUGGING_API_KEY")

# Title
st.title(" AI Travel Planner")
st.write("Tell me about your trip, and I'll create a personalized itinerary!")

# Initialize session state
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "destination": "",
        "duration": "",
        "budget": "",
        "interests": [],
        "diet": None,
        "mobility": ""
    }

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hugging Face API call function
def query_huggingface(prompt, context=None):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {HUGGING_API_KEY}"}
    
    # Format the prompt with instruction template
    formatted_prompt = f"""
    [INST] <<SYS>>
    You are TravelGPT, an expert AI travel planner. Your task:
    1. Help users plan their trips by asking relevant questions
    2. Generate personalized itineraries based on their preferences
    3. Use a friendly, helpful tone with occasional emojis
    <</SYS>>
    
    {f"Context: {context}" if context else ""}
    
    User request: {prompt}
    [/INST]
    """
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": formatted_prompt, "parameters": {"max_new_tokens": 500}}
        )
        return response.json()[0]['generated_text'].split('[/INST]')[-1].strip()
    except Exception as e:
        st.error(f"Error calling Hugging Face API: {str(e)}")
        return "I'm having trouble connecting to the travel planning service. Please try again later."

# Input form for basic trip details
with st.form("trip_details"):
    st.subheader("Tell me about your trip")
    
    destination = st.text_input("Where do you want to go?")
    duration = st.number_input("How many days?", min_value=1, max_value=30)
    budget = st.selectbox("Budget?", ["Low", "Medium", "High"])
    interests = st.multiselect("Interests?", ["Adventure", "Food", "History", "Art", "Nature"])
    
    submitted = st.form_submit_button("Plan My Trip!")
    
    if submitted:
        st.session_state.user_data = {
            "destination": destination,
            "duration": duration,
            "budget": budget,
            "interests": interests
        }
        st.success("Got it! Now let's refine your trip.")

# Refinement section
if st.session_state.user_data["destination"]:
    st.subheader(" Let's refine your trip")
    
    with st.form("refine_details"):
        if "Food" in st.session_state.user_data["interests"]:
            diet = st.selectbox("Dietary preferences?", ["None", "Vegetarian", "Vegan", "Gluten-free"])
        
        mobility = st.selectbox("Walking tolerance?", ["Low (prefer less walking)", "Moderate", "High (love walking)"])
        
        refine_submitted = st.form_submit_button("Continue")
        
        if refine_submitted:
            st.session_state.user_data.update({
                "diet": diet if "Food" in st.session_state.user_data["interests"] else None,
                "mobility": mobility
            })
            
            # Start the conversation with Hugging Face
            initial_prompt = f"""
            I want to visit {st.session_state.user_data['destination']} for {st.session_state.user_data['duration']} days.
            Budget: {st.session_state.user_data['budget']}
            Interests: {', '.join(st.session_state.user_data['interests'])}
            Dietary restrictions: {st.session_state.user_data['diet'] or 'None'}
            Mobility: {st.session_state.user_data['mobility']}
            """
            
            response = query_huggingface(
                "Please help me plan my trip based on these details",
                initial_prompt
            )
            
            st.session_state.messages = [
                {"role": "assistant", "content": response}
            ]
            st.success("Perfect! Let's chat about your trip details.")

# Chat interface
if st.session_state.messages:
    st.subheader(" Let's plan your trip")
    
    for message in st.session_state.messages:
        st.chat_message(message["role"]).write(message["content"])
    
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get AI response
        context = "\n".join(
            f"{msg['role']}: {msg['content']}" 
            for msg in st.session_state.messages[-5:]  # Keep last 5 messages as context
        )
        
        ai_response = query_huggingface(prompt, context)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()

# Itinerary generation
if st.session_state.messages and st.button("Generate Final Itinerary"):
    with st.spinner("Creating your perfect itinerary..."):
        # Prepare the prompt for itinerary generation
        itinerary_prompt = f"""
        Please generate a detailed {st.session_state.user_data['duration']}-day itinerary for {st.session_state.user_data['destination']} with:
        - Daily schedule (Morning/Afternoon/Evening)
        - Activities matching: {', '.join(st.session_state.user_data['interests'])}
        - Budget level: {st.session_state.user_data['budget']}
        - Dietary preferences: {st.session_state.user_data['diet'] or 'None'}
        - Mobility considerations: {st.session_state.user_data['mobility']}
        
        Format in markdown with:
        ## Day 1
        **Morning:** [Activity] (Duration)
        **Afternoon:** [Activity]
        **Evening:** [Dinner suggestion]
        Travel Tip: [Helpful advice]
        """
        
        final_itinerary = query_huggingface(itinerary_prompt)
        st.markdown("Your Personalized Itinerary")
        st.markdown(final_itinerary)
        
        # Add export options
        st.download_button(
            label="Download Itinerary",
            data=final_itinerary,
            file_name=f"{st.session_state.user_data['destination']}_itinerary.md",
            mime="text/markdown"
        )
