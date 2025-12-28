from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_sex_keyboard():
    """Одноразовая клавиатура для выбора пола"""
    keyboard = VkKeyboard(one_time=True)  # ← Изменено: one_time=True
    keyboard.add_button("1", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("2", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def get_next_button():
    """Одноразовая кнопка 'Дальше'"""
    keyboard = VkKeyboard(one_time=True)  # ← Изменено: one_time=True
    keyboard.add_button("Дальше", color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


def get_start_button():
    """Кнопка '/start' — можно оставить постоянной (или тоже одноразовой)"""
    keyboard = VkKeyboard(one_time=True)  # ← Лучше тоже сделать одноразовой
    keyboard.add_button("/start", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()