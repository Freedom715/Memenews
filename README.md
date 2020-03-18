# from flask import Flask, url_for, request

# from requests import request

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello World'


@app.route('/bootstrap_sample')
def bootstrap():
    return '''<!doctype html>
                <html lang="en">
                  <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

                    <title>Привет, Яндекс!</title>
                  </head>
                  <body>
                    <h1>Привет, Яндекс!</h1>
                    <div class="alert alert-primary" role="alert">
                      А мы тут компонентами Bootstrap балуемся
                    </div>
                  </body>
                </html>'''


@app.route('/choice/<planet_name>')
def return_sample_page(planet_name):
    return f"""<!DOCTYPE html>
                <html lang="en">
                  <head>
                    <meta charset="utf-8">
                    <link rel="stylesheet" 
                    href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" 
                    integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" 
                    crossorigin="anonymous">
                    <link rel="stylesheet" type="text/css" href="{url_for('static',
                                                                          filename='css/style.css')}" />
                    <title>Варианты выбора</title>
                  </head>
                  <body>
                    <h1>фамилия: {planet_name}</h1>
                    <input type="email" class="form-control" id="email" aria-describedby="emailHelp" placeholder="Введите адрес почты" name="email">
                    <div class="alert alert-danger" role="alert">Наконец, она просто вшивая!</div>


                  </body>
                </html>"""


@app.route('/form_sample', methods=[ 'POST', 'GET' ])
def form_sample():
    if request.method == 'GET':
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet"
                            href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
                            integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
                            crossorigin="anonymous">

                            <title>Пример формы</title>
                          </head>
                          <body>
                            <h1>Форма для регистрации в суперсекретной системе</h1>
                            <div>
                                <form class="login_form" method="post">
                                    <link rel="stylesheet" type="text/css" href="{url_for('static',
                                                                                          filename='css/style.css')}" />
                                    <input type="email" class="form-control" id="email" aria-describedby="emailHelp" placeholder="Введите адрес почты" name="email">
                                    <div class="form-group">
                                        <label for="classSelect">Скоько Вам уже есть полных лет</label>
                                        <select class="form-control" id="classSelect" name="class">
                                          <option>0</option>
                                          <option>14</option>
                                          <option>16</option>
                                          <option>18</option>
                                        </select>
                                     </div>
                                    <div class="form-group">
                                        <label for="about">Немного о себе</label>
                                        <textarea class="form-control" id="about" rows="3" name="about"></textarea>
                                    </div>
                                    <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <div class="form-group">
                                        <label for="form-check">Укажите пол</label>
                                        <div class="form-check">
                                          <input class="form-check-input" type="radio" name="sex" id="male" value="male" checked>
                                          <label class="form-check-label" for="male">
                                            Мужской
                                          </label>
                                        </div>
                                        <div class="form-check">
                                          <input class="form-check-input" type="radio" name="sex" id="female" value="female">
                                          <label class="form-check-label" for="female">
                                            Женский
                                          </label>
                                        </div>
                                    </div>
                                    <div class="form-group form-check">
                                        <input type="checkbox" class="form-check-input" id="acceptRules" name="accept">
                                        <label class="form-check-label" for="acceptRules">Принимаю условтя приложения</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Записаться</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        print(request.form[ 'email' ])
        print(request.form[ 'password' ])
        print(request.form[ 'class' ])
        print(request.form[ 'file' ])
        print(request.form[ 'about' ])
        print(request.form[ 'accept' ])
        print(request.form[ 'sex' ])
        return "Форма отправлена"


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
