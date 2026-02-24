def test_interface(self, interface_type: Type) -> None:
        print(f"\n --- Проверяем интерфейс: {interface_type.__name__} ---")

        if interface_type not in self._registry:
            print("Статус: этот интерфейс ещё не зарегестрирован.")
            return

        info = self._registry[interface_type]
        implementation = info['impl']
        fixed_params = info['params']

        print("Статус: Успешно зарегестрирован!")

        try:
            impl_name = implementation.__name__
        except AttributeError:
            impl_name = str(implementation)

        print(f"Реализуется через: {impl_name}")

        if fixed_params:
            print(f"Переданные вручную параметры: {fixed_params}")
        else:
            print("Переданные вручную параметры: нет.")

        if not inspect.isclass(implementation):
            print("-> Это функция-фабрика, скрытые зависимости не проверяем.")
            return
        
        print("Автоматические зависимости для создания:")
        
        all_params = inspect.signature(implementation.__init__).parameters
        
        dependencies = [
            (name, param.annotation.__name__ if hasattr(param.annotation, '__name__') else "Тип не указан") 
            for name, param in all_params.items() if name != 'self' and name not in fixed_params
        ]
        
        if not dependencies:
            print("-> Дополнительных зависимостей не требуется.")
        else:
            for name, dep_type in dependencies:
                print(f"-> Нужно найти: {name} (тип: {dep_type})")
