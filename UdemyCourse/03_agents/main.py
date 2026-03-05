import json
from openai import OpenAI
from dotenv import load_dotenv

from system_prompt import SYSTEM_PROMPT
from weather import get_weather

load_dotenv()
client = OpenAI()

AVAILABLE_TOOLS = {
    "get_weather": get_weather
}

def main():

    print("Please enter Your Query! or exit to exit the agent!")
    while True:
        user_input = input("📩: ")
        # print("User input is:", user_input)
        if user_input in ["exit", "exit()"]:
            print("Bye!!")
            break
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
            if msg_resp.get("step") != "TOOL":
                print(f"🧠: {msg_resp.get("content")}") 
            if msg_resp.get("step") == "TOOL":
                tool_name = msg_resp.get('tool')
                tool_param = msg_resp.get('input')
                tool_resp = AVAILABLE_TOOLS[tool_name](tool_param)
                print(f"🛠️: {tool_name}{tool_param}=>{tool_resp}")
                message_chat.append(
                    {
                        "role": "developer",
                        "content": json.dumps({
                            "step": "OBSERVE",
                            "tool": tool_name,
                            "input": tool_param,
                            "content": tool_resp
                        })
                    }
                )
                continue
            message_chat.append({
                "role": "assistant",
                "content": json.dumps(msg_resp)
            })

if __name__ == "__main__":
    main()