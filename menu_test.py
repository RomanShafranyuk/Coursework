from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem, SubmenuItem

users_online = ['Roman', 'Pasha', 'Oleg']

def send_message():
    global users_online
    user_index = SelectionMenu.get_selection(users_online, "Send to...", show_exit_option=False)
    test_prompt = prompt_utils.PromptUtils(Screen())
    res2 = test_prompt.input("Text")
    print('Message sent to', users_online[user_index])
    print('')
    test_prompt.enter_to_continue()

def see_messages():
    test_prompt = prompt_utils.PromptUtils(Screen())
    print("Roman: Nice cock!")
    print("Pasha: Great balls!")
    print('')
    test_prompt.enter_to_continue()


menu = ConsoleMenu("Secure chat client")
item1 = FunctionItem("Send new message", send_message)
item2 = FunctionItem("List incoming messages", see_messages)

menu.append_item(item1)
menu.append_item(item2)

menu.show()

print('Executing exit routine...')