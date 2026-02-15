from constant import LINKEDIN_ACCESS_TOKEN
from generate_post import generate
from linkedin_poster import post_to_linkedin
from get_my_id import get_linkedin_person_id

app = FastAPI()



if __name__ == "__main__":
    print("Hi Linked IN we are here to explore")
    core_problem = input("Enter the core problem: ")
    tech_compare = input("Enter the tech compare: ")
    app_context = input("Enter the app context: ")
    content_linkedin = generate(
        core_problem=core_problem,
        tech_compare=tech_compare,
        app_context=app_context)
    my_person_id = get_linkedin_person_id(LINKEDIN_ACCESS_TOKEN)
    result = post_to_linkedin(content_linkedin, LINKEDIN_ACCESS_TOKEN, my_person_id)
    print(result)
    # print(content_linkedin)