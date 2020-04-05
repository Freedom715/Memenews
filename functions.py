def check_password(password):
    print('Function!')
    if len(password) >= 8:
        if not password.isalpha() and not password.isdigit():
            if password.lower() != password:
                print(password)
                return ''
            return 'В пароле должны быть буквы разного уровня'
        return 'В пароле должна быть хоть одна цифра или буква'
    return 'Пароль слишком короткий'
