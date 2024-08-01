# ptdevops
Для запуска проекта необходимо: 
0) Установить на хост git, ansible.
   Создать пользователя ansible и выдать ему права на sudo NOPASSWD

Клонировать репозиторий:
```
git clone
```
1) Cоздать в каталоге ./files/tg_bot файл .env
```
   SSH_HOST = '<ip-адрес>' -- хост, где будет база Msster
    SSH_PORT = '<ssh-порт>'              -- ssh порт
    SSH_USER = '<имя пользователя>'      -- username с правами sudo NOPASSWD (<username>  ALL=(ALL:ALL) NOPASSWD:ALL)
    SSH_PASSWORD = '<пароль>'
    BOT_TOKEN = '<бот API токен>'
    CHAT_ID = '<ID телеграм группы>'     -- не используется. Указать любое значение в формате -xxxxxxxxxx, где х - цифры 0-9
    DB_USER = 'postgres'                 -- не менять
    DB_PASSWORD = 'P@ssw0rd'             -- пароль для пользователя postgres
    DB_HOST = 'ptdevops-store-main'      -- имя контейнера с СУБД PostgreSQL (MASTER) не менять
    DB_PORT = '5432'                     -- не менять
    DB_DEFAULT_NAME = 'postgres'         -- не менять
    DB_CONNECT_NAME = 'db_ptdevops'      -- не менять
```
3) Выполнить запуск инсталляции проекта:
```
ansible-playbook -i ./inventory/hosts tg_bot_playbook.yaml
```
