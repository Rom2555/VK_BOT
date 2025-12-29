from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_sex_keyboard():
    """Клавиатура для выбора пола"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("1", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("2", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def get_action_buttons():
    """Клавиатура с 4 кнопками: Дальше, Доб. в избранное, Избранное, Начать заново"""
    keyboard = VkKeyboard(one_time=False)

    # Первая строка
    keyboard.add_button("Дальше", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Добавить в избранное", color=VkKeyboardColor.POSITIVE)

    keyboard.add_line()  # Вторая строка
    keyboard.add_button("Избранное", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("Начать заново", color=VkKeyboardColor.NEGATIVE)

    return keyboard.get_keyboard()


def get_next_button():
    """Кнопка 'Дальше'"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Дальше", color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


def get_start_button():
    """Кнопка '/start'"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("/start", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()
