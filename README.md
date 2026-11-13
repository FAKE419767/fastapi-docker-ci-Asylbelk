# Jenkins + Docker + FastAPI: учебный проект для Windows 11

Проект находится в `C:\jenkins`. Все команды ниже выполняются в PowerShell из этой папки. API хранит товары в памяти: перезапуск процесса или контейнера удаляет данные. Используется один Uvicorn worker; несколько процессов не разделяют хранилище. Это учебное API без авторизации.

## 1. Установка инструментов

1. Установите [Python 3.11](https://www.python.org/downloads/windows/), включив Python Launcher и Add Python to PATH. Если Jenkins использует другую учетную запись, установите Python для всех пользователей.
2. Установите [Git for Windows](https://git-scm.com/download/win) и [VS Code](https://code.visualstudio.com/). В VS Code установите расширение Python от Microsoft.
3. Установите Docker Desktop с WSL 2 backend. При необходимости выполните `wsl --install` в PowerShell администратора и перезагрузите Windows. Запустите Docker Desktop, дождитесь готовности Engine и выберите Linux containers.
4. Установите Jenkins LTS через Windows MSI с [официального сайта](https://www.jenkins.io/download/). Сначала установите поддерживаемую выбранным Jenkins версию JDK; совместимость проверяйте в [Java Support Policy](https://www.jenkins.io/doc/book/platform-information/support-policy-java/). Укажите каталог JDK установщику.
5. В установщике Jenkins выберите порт **8081** и отдельную учетную запись Windows для службы (с паролем и правом Log on as a service). Для простого локального стенда удобно использовать ту же учетную запись, под которой запущен Docker Desktop. Jenkins под LocalSystem может не видеть пользовательские Docker context и настройки.

Проверка в новом терминале:

```powershell
Set-Location C:\jenkins
py -3.11 --version
git --version
java -version
docker version
docker compose version
docker info --format '{{.OSType}}'
```

`docker version` должен показать Client и Server, последняя команда — `linux`.

## 2. VS Code, локальный запуск и тесты

Откройте VS Code → File → Open Folder → `C:\jenkins`, затем Terminal → New Terminal → PowerShell.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

В VS Code через Python: Select Interpreter выберите `.venv\Scripts\python.exe`. Активация окружения не обязательна. Если оно активировано, тесты запускаются обычной командой `python -m pytest -v`.

Откройте http://localhost:8000/docs. В Swagger раскройте POST /products → Try it out → введите JSON → Execute:

```json
{"name":"Keyboard","description":"USB","price":25.5,"quantity":3}
```

GET /products покажет список, GET /products/1 — созданный товар, DELETE /products/1 удалит его (204 без тела). Неизвестный положительный ID дает 404. Некорректный ID и данные дают 422. Имя обязательно, после удаления пробелов длина 1–100; описание до 1000 символов; цена конечная и больше нуля; количество — целое неотрицательное число. Лишние поля запрещены. GET / возвращает приветствие, GET /health — `{"status":"ok"}`. Тесты создают отдельный экземпляр приложения для каждого случая.

Остановите локальный сервер клавишами Ctrl+C перед запуском Docker.

## 3. Docker: сборка и запуск

```powershell
docker build -t fastapi-jenkins-demo .
docker compose up -d --build
docker compose ps
docker ps
docker inspect --format '{{.State.Health.Status}}' fastapi-jenkins-demo
Invoke-RestMethod http://localhost:8000/health
```

Дождитесь состояния `healthy`, откройте http://localhost:8000/docs. В Docker Desktop → Containers будет контейнер `fastapi-jenkins-demo`; его логи доступны через интерфейс или `docker logs fastapi-jenkins-demo`.

Альтернатива Compose после сборки (не запускайте оба способа одновременно):

```powershell
docker run -d --name fastapi-jenkins-demo --restart unless-stopped -p 127.0.0.1:8000:8000 fastapi-jenkins-demo
```

Перед передачей управления Jenkins остановите Compose:

```powershell
docker compose down
```

Если использовали `docker run`, удалите только созданный учебный контейнер командой `docker rm -f fastapi-jenkins-demo`. Jenkins далее будет сам заменять контейнер с этим именем. Не используйте это имя для других приложений. Порт опубликован только на локальном компьютере. HEALTHCHECK использует Python, curl внутри образа не нужен.

## 4. Загрузка на GitHub

1. Войдите на GitHub и создайте пустой репозиторий `jenkins-docker-demo` без автоматического README и .gitignore.
2. В терминале VS Code выполните команды, заменив YOUR_LOGIN своим именем:

```powershell
git init
git add .
git commit -m "Add FastAPI Jenkins Docker demo"
git branch -M main
git remote add origin https://github.com/YOUR_LOGIN/jenkins-docker-demo.git
git push -u origin main
```

Если Git просит имя и email, настройте `git config user.name "Ваше имя"` и `git config user.email "Ваш email"`, затем повторите commit. Для push используйте окно входа Git Credential Manager. Не сохраняйте токены в файлах проекта. Откройте репозиторий и проверьте наличие Jenkinsfile в корне.

## 5. Jenkins на порту 8081

1. Откройте http://localhost:8081. Если Jenkins уже установлен на другом порту, найдите `jenkins.xml` в каталоге установки службы, сохраните резервную копию, измените аргумент `--httpPort` на `--httpPort=8081` и перезапустите службу Jenkins из `services.msc` с правами администратора.
2. На первом экране используйте пароль из файла `secrets\initialAdminPassword` в каталоге JENKINS_HOME, указанном на экране. Не публикуйте его.
3. Выберите Install suggested plugins, создайте администратора, укажите Jenkins URL `http://localhost:8081/`.
4. В Manage Jenkins → Plugins проверьте Pipeline, Git, JUnit и Timestamper.
5. В Manage Jenkins → Nodes → Built-In Node → Configure добавьте label `windows`, сохраните. Для этого локального учебного стенда требуется хотя бы один executor. При использовании отдельного Windows agent присвойте label ему; Docker Desktop и Python должны быть доступны именно на машине agent.
6. Учетной записи службы должны быть доступны Git, Python Launcher, Python 3.11, PowerShell и Docker CLI через PATH. После установки инструментов перезапустите службу, чтобы обновился PATH. В Manage Jenkins → Tools при необходимости настройте путь к Git.

### Доступ службы к Docker Desktop

Проверьте учетную запись на вкладке Log On службы Jenkins в `services.msc`. Docker Desktop должен быть запущен в пользовательском сеансе. Это не автономный серверный Docker daemon.

Если вашей установке Docker требуется членство в `docker-users`, добавьте фактическую учетную запись службы через Computer Management → Local Users and Groups → Groups либо PowerShell администратора (замените имя):

```powershell
Add-LocalGroupMember -Group 'docker-users' -Member 'COMPUTER\jenkins-user'
```

Затем выйдите и войдите в Windows для этой учетной записи и перезапустите службу Jenkins. Членство в группе само по себе не гарантирует доступ к пользовательскому WSL backend: проверьте Docker под той же учетной записью. Для диагностики временно создайте Pipeline с `bat 'whoami'`, `bat 'where docker'`, `bat 'py -3.11 --version'`, `bat 'docker context ls'`, `bat 'docker info'`. Последняя команда должна работать именно внутри Jenkins. Если служба не видит пользовательский backend, используйте Windows agent, запущенный в сеансе владельца Docker Desktop, с label `windows`, а controller оставьте службой. Не открывайте незащищенный Docker TCP API.

Пояснения: [Jenkins Windows service](https://www.jenkins.io/doc/book/installing/windows/), [права Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-permission-requirements/).

## 6. Создание Pipeline из GitHub

1. Jenkins → New Item → имя `fastapi-jenkins-demo` → Pipeline → OK.
2. В разделе Pipeline выберите Definition: **Pipeline script from SCM**.
3. SCM: **Git**, Repository URL: `https://github.com/YOUR_LOGIN/jenkins-docker-demo.git`.
4. Для публичного репозитория чтение возможно без credentials. Для приватного добавьте Credentials → Jenkins → Username with password, username — GitHub login, password — токен с правом чтения нужного репозитория; выберите credential. Не вставляйте токен в URL. Пароль аккаунта GitHub для Git HTTPS не используйте.
5. Branch Specifier: `*/main`, Script Path: `Jenkinsfile`. Save.
6. Убедитесь, что порт 8000 свободен, Docker Desktop работает, локальный Uvicorn остановлен, Compose выключен.
7. Нажмите **Build Now**. Слева в Build History откройте номер сборки → **Console Output**. История сохраняется для последних 20 сборок.

Ожидаемая последовательность:

| Этап | Признак успеха |
| --- | --- |
| Checkout | Получен commit из GitHub |
| Install Dependencies | Создано окружение Python 3.11, установлены зависимости |
| Run Tests | pytest завершился с кодом 0; доступен отчет Test Result |
| Docker Build | Создан образ fastapi-jenkins-demo с тегом номера сборки |
| Docker Deploy | Предыдущий учебный контейнер удален, новый запущен |
| Health Check | HTTP 200, status ok и Docker health healthy |
| Result (post) | Сообщение SUCCESS и итоговый статус SUCCESS |

Result реализован в верхнеуровневом `post`, чтобы сообщение FAILURE выводилось и при ошибке раннего этапа. Ошибка pytest прерывает Pipeline: сборка образа и deploy не выполняются. `disableConcurrentBuilds()` ставит повторные сборки этого job в очередь. Создайте только один job для данного контейнера и порта: эта опция не блокирует другие jobs и ручные команды Docker. Во время Pipeline не запускайте Compose с тем же контейнером.

После успеха:

```powershell
docker ps --filter name=fastapi-jenkins-demo
docker inspect --format '{{.State.Health.Status}}' fastapi-jenkins-demo
Invoke-RestMethod http://localhost:8000/health
```

Откройте Swagger http://localhost:8000/docs и контейнер в Docker Desktop. Повторный Build Now заменит контейнер, данные товаров сбросятся. Развертывание допускает короткий простой; автоматический откат не реализован. При ошибке health check контейнер остается для диагностики, сборка получает FAILURE.

## 7. Изменения и демонстрация CI/CD

Измените приветствие в `app/main.py`, выполните тесты, затем:

```powershell
git add .
git commit -m "Update greeting"
git push
```

Нажмите Build Now. Checkout получит новый commit. Автоматический webhook здесь не требуется: локальный Jenkins не доступен GitHub по localhost. Для демонстрации остановки на тестах можно временно изменить ожидаемое значение health в тесте, отправить commit и запустить сборку: Run Tests завершится ошибкой, deploy будет пропущен, прежний контейнер продолжит работать. После демонстрации восстановите тест и отправьте исправление.

## 8. Типичные ошибки

| Ошибка | Решение |
| --- | --- |
| `py -3.11` не найден | Установите Python 3.11 и launcher для учетной записи Jenkins; проверьте `py -0p`, перезапустите службу |
| `Activate.ps1` запрещен | Используйте прямой путь `.venv\Scripts\python.exe`, активация не нужна |
| ModuleNotFoundError | Перейдите в корень проекта, установите requirements тем же интерпретатором, запускайте `python -m pytest` |
| Docker Server недоступен, pipe not found | Запустите Desktop, дождитесь Engine, проверьте WSL 2 и Linux containers |
| Access denied для Docker/config.json | Проверьте владельца конфигурации, учетную запись службы, ее Docker context и доступ; не копируйте чужие credentials |
| Docker работает в терминале, но не в Jenkins | Проверьте PATH, Log On службы и `docker info` внутри job; при необходимости используйте agent в пользовательском сеансе |
| Сборка висит в очереди | Добавьте label windows и доступный executor соответствующему узлу |
| Порт 8000 занят | Остановите локальный Uvicorn или прежний учебный Compose; найдите владельца через `Get-NetTCPConnection -LocalPort 8000` |
| Имя контейнера уже занято | Не запускайте Compose параллельно с Jenkins; Pipeline сам удаляет только контейнер заданного имени |
| localhost:8081 не открывается | Проверьте службу Jenkins, JDK, параметр httpPort и журналы службы; используйте `Get-NetTCPConnection -LocalPort 8081` |
| Git authentication failed | Проверьте URL, main и credentials; токен должен читать приватный репозиторий |
| Jenkinsfile не найден | Он должен быть в корне ветки main; Script Path должен быть Jenkinsfile |
| pip/build не скачивает зависимости | Проверьте сеть, DNS и proxy под учетной записью службы; повторите после восстановления доступа |
| Health Check завершился ошибкой | Откройте Console Output, `docker logs --tail 100 fastapi-jenkins-demo` и `docker inspect fastapi-jenkins-demo`; исправьте причину и повторите Build Now |

Зависимости зафиксированы для воспроизводимости учебного примера; транзитивные зависимости не являются полным lock-файлом. Справка по [FastAPI TestClient](https://fastapi.tiangolo.com/tutorial/testing/).

## 9. Фактически выполненные проверки

При создании проекта 12 ноября 2026 года:

- Установка requirements в `.venv` выполнена успешно.
- `python -m pytest -v --junitxml=reports/pytest.xml`: **28 passed**, Python **3.13.17** на Windows. Есть одно DeprecationWarning в Starlette о псевдониме AnyIO; тесты проходят.
- Проверка синтаксиса `python -m compileall -q app tests` выполнена успешно.
- `docker compose config --quiet` выполнена успешно.
- Docker build был запущен, но не выполнен: пользовательская Docker-конфигурация недоступна, а при использовании отдельной конфигурации отсутствует подключение к `docker_engine` named pipe.
- Python 3.11 в доступном окружении не найден. Проверка именно на 3.11 и внутри образа еще требуется.
- Jenkins Pipeline и GitHub push не выполнялись: репозиторий и job должен настроить пользователь по инструкции выше.

Созданное при проверке `.venv` использует Python 3.13. Для перехода на 3.11 закройте процессы, использующие это окружение, переименуйте его и создайте новое:

```powershell
Rename-Item -LiteralPath .venv -NewName .venv-py313
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
```

Не добавляйте виртуальные окружения в Git.
