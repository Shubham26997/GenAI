import json
from openai import OpenAI
from dotenv import load_dotenv
from model import PromptOutput
from system_prompt import SYSTEM_PROMPT
from weather import get_weather, run_cmd

load_dotenv()
client = OpenAI()

AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "run_cmd": run_cmd
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
            response = client.chat.completions.parse(
                model = "gpt-4o",
                response_format = PromptOutput,
                messages=message_chat
            )
            # print(response.choices[0].message.content)
            # msg_resp = json.loads(response.choices[0].message.content)
            # print(type(msg_resp))
            msg_resp = response.choices[0].message.parsed
            if msg_resp.step == "OUTPUT":
                print(f"🤖: {msg_resp.content}")
                break
            if msg_resp.step != "TOOL":
                print(f"🧠: {msg_resp.content}") 
            if msg_resp.step == "TOOL":
                tool_name = msg_resp.tool
                tool_param = msg_resp.input
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
                "content": json.dumps(response.choices[0].message.content)
            })

if __name__ == "__main__":
    main()