import json
from math import floor
import openai
from rich import print as rprint, inspect
from datetime import datetime

with open(".secrets/OPENAI-API-KEY", "r") as f:
    openai.api_key = f.read().strip()

USER_YES = ["y", "Y", "yes", "Yes", "YES", "ye", "Ye", "YE", "yep", "Yep", "YEP", "yup", "Yup", "YUP", "yeah", "Yeah", "YEAH"]
USER_NO = ["n", "N", "no", "No", "NO", "nope", "Nope", "NOPE", "nah", "Nah", "NAH", "no thanks", "No thanks", "NO THANKS", "no thank you", "No thank you", "NO THANK YOU", "not really", "Not really", "NOT REALLY", "not really thanks", "Not really thanks", "NOT REALLY THANKS", "not really thank you", "Not really thank you", "NOT REALLY THANK YOU"]

def is_yes(user_input):
    return user_input.lower().strip() in USER_YES

def is_no(user_input):
    return user_input.lower().strip() in USER_NO

# If default is yes, we check if not is_no. If default is no, we check if is_yes.

use_default = is_yes(input("Do you want to use the default options? (y/N) "))
if use_default:
    days = 2
    meals = 3
    bool_user_options = {"dairy": True, "protein": True, "veggies": True, "carbs": True, "fruits": True, "fats": True}
    time_of_day = "breakfast, lunch, and dinner"
    complexity = "simple"
    preparation = "quick"
    vegetarian = True
    preferred_cuisine = "healthy Indian"
else:
    days = input("How many days do you want to make a menu for? ")
    while not days.isdigit():
        days = input("How many days do you want to make a menu for? ")
    days = int(days)

    meals = input("How many meals do you want per day? ")
    while not meals.isdigit():
        meals = input("How many meals do you want per day? ")
    meals = int(meals)

    BOOL_USER_OPTIONS_NAMES = ["dairy", "protein", "veggies", "carbs", "fruits", "fats"]
    bool_user_options = {option: not is_no(input(f"Do you want {option}? (Y/n) ")) for option in BOOL_USER_OPTIONS_NAMES}

    TIME_BOOL_USER_OPTIONS_NAMES = ["breakfast", "lunch", "dinner", "snack", "bld", "all"]
    time_of_day = input("What time of day do you want to make a menu for? (breakfast, lunch, dinner, snack, bld, all) ")
    while time_of_day not in TIME_BOOL_USER_OPTIONS_NAMES:
        time_of_day = input("What time of day do you want to make a menu for? (breakfast, lunch, dinner, snack, all) ")

    if time_of_day not in ["bld", "all"]:
        meals = 1
        print("You can only have one meal per day if you are only making a menu for one time of day.")

    if time_of_day == "all":
        time_of_day = "breakfast, lunch, dinner, and snack"
    if time_of_day == "bld":
        time_of_day = "breakfast, lunch, and dinner"

    COMPLEXITY_OPTIONS_NAMES = ["simple", "intermediate", "complex"]
    complexity = input("How complex do you want the meals to be? (simple, intermediate, complex) ")
    while complexity not in COMPLEXITY_OPTIONS_NAMES:
        complexity = input("How complex do you want the meals to be? (simple, intermediate, complex) ")

    PREPARATION_OPTIONS_NAMES = ["quick", "medium", "long"]
    preparation = input("How long do you want the meals to take to prepare? (quick, medium, long) ")
    while preparation not in PREPARATION_OPTIONS_NAMES:
        preparation = input("How long are you ok with preparation times? (quick, medium, long) ")


    vegetarian = not is_no(input("Are you vegetarian? (Y/n) "))

    preferred_cuisine = input("What cuisine do you prefer? (leave blank for no preference) ")
print(f"""
Your chosen options are:
    - {days} days
    - {meals} meals per day
    - {'The meal should be vegetarian.' if vegetarian else 'The meal can be nonvegetarian.'}
    - Including: {', '.join([option for option, value in bool_user_options.items() if value])}
    - Excluding: {', '.join([option for option, value in bool_user_options.items() if not value])}{'Nothing' if all(value for value in bool_user_options.values()) else ''}
    - Meals should be for {time_of_day}
    - {complexity} difficulty
    - {preparation} time to prepare
    - {'No preference' if not preferred_cuisine else preferred_cuisine}
""")

confirm = not is_no(input(f"Are you sure? (Y/n) "))
if not confirm:
    exit()

show_ingredients = not is_no(input("Do you want to see the ingredients? (Y/n) "))
show_instructions = is_yes(input("Do you want to see the instructions? (y/N) "))

if show_instructions:
    print("Using instructions will take much longer to generate, and only works for a few meals.")

print(f"""Your options are:
    - Ingredients: {show_ingredients}
    - Instructions: {show_instructions}
      """)

confirm = not is_no(input(f"Are you sure? (Y/n) "))
if not confirm:
    exit()

print("-" * 80)

system_message = "You are a food expert who is making a menu for a client. The client has the following requirements:"

prompt = f"""
You want to make a menu for {days} days for {time_of_day}. Each day should have around {meals} meals. 
{'The meal should be vegetarian.' if vegetarian else ''}
The menu should include {', '.join([option for option, value in bool_user_options.items() if value])}.
The menu should not include {', '.join([option for option, value in bool_user_options.items() if not value])}.
The menu should include {time_of_day}.
The menu should include {days} days.
The menu should be {complexity} difficulty to make.
The menu should take no more than a {preparation} time to prepare.
{'The menu should be ' if preferred_cuisine else ''}{preferred_cuisine if preferred_cuisine else ''}

Your output should be in strictly parseable JSON format.
Under key `info` should be a list of objects, each object representing the day and a list of meals for that day.
Each day object should be structured as follows:
    - index: the index of the day, starting with 0
    - day: the day of the week, starting with Monday and always being one of [Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
    - meals: a list of meals for that day

Each meal should be structured as follows:
    - name: the name of the meal
    - dish: the name of the dish
    {'- ingredients: a list of ingredients for that meal. Each ingredient should not be preceded by a number or a bullet point.' if show_ingredients else ''}
    {'- instructions: a list of strings, each string being a step in the instructions. Each instruction should not be preceded by a number or a bullet point. Keep instructions succinct.' if show_instructions else ''}
    - cost: the cost of the meal as an integer in cents
    - time: the time to prepare the meal in seconds
    - serves: the number of people the meal serves
    - difficulty: the difficulty of the meal, one of [simple, intermediate, complex]
    {'- cuisine: the cuisine of the meal' if not preferred_cuisine else ''}

{'''Each ingredient should be structured as follows:
    - name: the name of the ingredient
    - amount: the amount of the ingredient
    - unit: the unit of the ingredient
        Each unit should be one of the following if possible: cup, tbsp, tsp, oz, lb, g, kg, ml, L, to taste, as needed, count, or unit. (You can add more if you want to.)
    - cost: the cost of the ingredient as an integer in cents. Make sure to create realistic prices.''' if show_ingredients else ''}

Under key `cost` should be the total cost of the menu in cents.

You will not prefix or suffix the output with anything.
Do NOT, AT ANY POINT, use unnecessary spaces or newlines to indent your JSON.
"""
loading_message = "Loading..."
print(loading_message, end="", flush=True)
start_time = datetime.now()

def get_response():
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": system_message}, {"role": "user", "content": prompt}],
)
    return response


response = get_response()
end_time = datetime.now()

time_taken = end_time - start_time

print("\b" * len(loading_message), end="", flush=True)
print(" " * len(loading_message), end="", flush=True)
print("\b" * len(loading_message), end="", flush=True)

print(f"Response time: {floor(time_taken.seconds/60)}:{time_taken.seconds%60}.")

print("\n")

if response.choices[0].finish_reason != "stop":
    if response.choices[0].finish_reason == "length":
        print("The response was too long.")
    else:
        print("The response was not stopped properly.")
    inspect(response)
    exit()
else:
    try:
        parsed_response = json.loads(response.choices[0].message["content"])
        print("Here is your menu:")


        for day in parsed_response["info"]:
            print(f"{day['day']}".upper())
            for meal in day["meals"]:
                print(f"Meal: {meal['name']}")
                print(f"Dish: {meal['dish']}")
                print(f"Cost: ${floor(meal['cost']/100)}.{str(meal['cost']%100).ljust(2, '0')}")
                print(f"Time: {floor(meal['time']/60)}:{meal['time']%60}")

                if show_ingredients:
                    print("Ingredients:")
                    for ingredient in meal["ingredients"]:
                        print(f"    {ingredient['amount']} {ingredient['unit']} {ingredient['name']}")
                
                if show_instructions:
                    print("Instructions:")
                    for index, instruction in enumerate(meal["instructions"]):
                        print(f"    {index + 1}. {instruction}")
                print()
            print()
        print(f"Total meals cost: ${floor(parsed_response['cost']/100)}.{str(parsed_response['cost']%100).ljust(2, '0')}")
    except Exception as e:
        print("There was an error parsing the response.")
        rprint(e)
        print(response.choices[0].message["content"])


rprint(f"Prompt cost: {response['usage']['total_tokens']/5000} cents.")
