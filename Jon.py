    def check_interface(self, interface_type):
        # Просто печатаем красивый заголовок, чтобы в консоли было понятно, что мы ищем
        print(f"\n--- Проверяем интерфейс: {interface_type.__name__} ---")

        # Шаг 1: Проверяем, есть ли вообще такой интерфейс в нашем словаре
        if interface_type not in self._registry:
            print("Статус: НЕ НАЙДЕНО. Этот интерфейс еще не зарегистрирован!")
            # Делаем return, чтобы функция дальше не выполнялась
            return

        # Шаг 2: Если дошли сюда, значит интерфейс есть. Достаем его данные из словаря.
        # В словаре по ключу лежит другой словарик с ключами 'impl', 'style' и 'params'
        info = self._registry[interface_type]
        implementation = info['impl']
        fixed_params = info['params']

        print("Статус: Успешно зарегистрирован!")
        
        # Получаем имя класса (или функции-фабрики). 
        # Используем try-except на случай, если у объекта вдруг нет атрибута __name__
        try:
            impl_name = implementation.__name__
        except AttributeError:
            impl_name = str(implementation)
            
        print(f"Реализуется через: {impl_name}")
        
        # Выводим параметры. Если словарь пустой, напишем "Нет" для красоты
        if fixed_params:
            print(f"Переданные вручную параметры: {fixed_params}")
        else:
            print("Переданные вручную параметры: Нет")

        # Шаг 3: Теперь самое интересное - ищем, какие зависимости нужны этому классу
        # Проверяем, класс ли это (а не фабрика), потому что у фабрик нет __init__
        if inspect.isclass(implementation):
            print("Автоматические зависимости для создания:")
            
            # Получаем список всех аргументов из метода __init__
            init_args = inspect.signature(implementation.__init__).parameters
            
            # Заведем флажок, чтобы знать, нашли мы что-то или класс пустой
            found_deps = False
            
            for arg_name, arg_data in init_args.items():
                # Нам не нужен self (это сам объект) 
                # и не нужны параметры, которые мы уже передали руками (fixed_params)
                if arg_name != 'self' and arg_name not in fixed_params:
                    
                    # Пытаемся достать имя типа из аннотации (то, что написано после двоеточия)
                    try:
                        dep_type = arg_data.annotation.__name__
                    except AttributeError:
                        dep_type = "Тип не указан"
                        
                    print(f" -> Нужно найти: {arg_name} (тип: {dep_type})")
                    found_deps = True
                    
            # Если цикл прошел, а флажок так и остался False
            if not found_deps:
                print(" -> Дополнительных зависимостей не требуется.")
        else:
            print(" -> Это функция-фабрика, скрытые зависимости не проверяем.")
