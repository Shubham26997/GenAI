import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
SYSTEM_PROMPT = """
    You are an expert AI assistant, who resolve user queries using chain of thought.
    You work on START, PLAN and OUTPUT steps.
    You need to first PLAN before acting on any query and there can be multiple planning steps along with exporing webs search and many more.
    Once you have enough plan ready and you are having enough context of the query then you can start executing the steps to solve the query and provide the result as output to the user.

    RULES:
        - Strictly follow the given JSON output format
        - Always execute one step at a time
        - Steps should always be in a given order that is START(This is the User input which you just elaborate to make user see the LLM has taken the input correctly), PLAN(This can be multiple based on the context required to solve the query and amount of steps iteration required to get to the final result), OUTPUT(Final result which will be sent to the user)
    OUTPUT Format:
        {"step": STEP | PLAN | OUTPUT, "content": "string"}
    Examples:

    START: Hey, Can you solve 2 + 3 * 4 - 5 / 10
    PLAN: {"step": PLAN, "content": "This looks like a Math problem"}
    PLAN: {"step": PLAN, "content": "This can be solve using BODMAS, or lets explore some other options"}
    PLAN: {"step": PLAN, "content": "This looks like BODMAS can be a correct option"}
    PLAN: {"step": PLAN, "content": "As per this approach we can apply divide first, so the equation will become 2+3*4-0.5"}
    PLAN: {"step": PLAN, "content": "As per this approach after the above step we can apply multiply, so the equation will become 2+12-0.5"}
    PLAN: {"step": PLAN, "content": "As per this approach after the above step we can apply addition, so the equation will become 14-0.5"}
    PLAN: {"step": PLAN, "content": "As per this approach after the above step we can apply subtract, so the equation will become 13.5"}
    PLAN: {"step": PLAN, "content": "Now the equation is completed, so the final result will be 13.5, lets present this to the user"}
    OUTPUT: {"step": OUTPUT, "content": "The equation is completed, and the final result will be 13.5, let me know if can help with anything else for you"}
    
    """

def main():
    user_input = input("📩: ")
    message_chat = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role":"user",
            "content": user_input
        }
    ]
    while True:        
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            response_format = {"type": "json_object"},
            messages=message_chat
        )
        # print(response.choices[0].message.content)
        msg_resp = json.loads(response.choices[0].message.content)
        # print(type(msg_resp))
        if msg_resp.get("step") == "OUTPUT":
            print(f"🤖: {msg_resp.get("content")}")
            break
        print(f"🧠: {msg_resp.get("content")}")
        message_chat.append({
            "role": "assistant",
            "content": json.dumps(msg_resp)
        })

if __name__ == "__main__":
    main()
